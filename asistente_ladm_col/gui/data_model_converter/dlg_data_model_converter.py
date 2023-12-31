"""
/***************************************************************************
                              Asistente LADM-COL
                             --------------------
        begin           : 2021-01-29
        git sha         : :%H$
        copyright       : (C) 2021 by Sergio Ramírez (SwissTierras Colombia)
                          (C) 2021 by Germán Carrillo (SwissTierras Colombia)
        email           : seralra96@gmail.com
                          gcarrillo@linuxmail.org
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtWidgets import (QDialog,
                                 QMessageBox,
                                 QDialogButtonBox,
                                 QSizePolicy)
from qgis.PyQt.QtCore import (Qt,
                              QSettings,
                              QCoreApplication,
                              pyqtSignal)
from qgis.PyQt.QtGui import QColor
from qgis.core import (Qgis,
                       QgsProcessingException,
                       QgsProcessingFeedback,
                       QgsProject)
from qgis.gui import (QgsMessageBar,
                      QgsMapCanvas)

import processing

from asistente_ladm_col.config.general_config import (SUPPLIES_DB_SOURCE,
                                                      COLLECTED_DB_SOURCE,
                                                      SETTINGS_CONNECTION_TAB_INDEX)
from asistente_ladm_col.config.keys.common import REQUIRED_MODELS
from asistente_ladm_col.config.ladm_names import LADMNames
from asistente_ladm_col.app_interface import AppInterface
from asistente_ladm_col.lib.logger import Logger
from asistente_ladm_col.lib.context import Context
from asistente_ladm_col.gui.dialogs.dlg_settings import SettingsDialog
from asistente_ladm_col.utils import get_ui_class

DIALOG_DATA_MODEL_CONVERTER_UI = get_ui_class('data_model_converter/dlg_data_model_converter.ui')


class DataModelConverterDialog(QDialog, DIALOG_DATA_MODEL_CONVERTER_UI):
    #on_result = pyqtSignal(bool)  # whether the tool was run successfully or not

    def __init__(self, conn_manager=None, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.conn_manager = conn_manager
        self.logger = Logger()
        self.app = AppInterface()

        self._running_tool = False        
        self.tool_name = QCoreApplication.translate("DataModelConverterDialog", "Data Model Converter")
 
        # we will use a unique instance of setting dialog
        self.settings_dialog = SettingsDialog(self.conn_manager, parent=parent)
        # The database configuration is saved if it becomes necessary
        # to restore the configuration when the user rejects the dialog
        self.init_db_target = None
        self.init_db_source = None
        self.set_init_db_config()  # Always call after the settings_dialog variable is set

        self._db_target = self.conn_manager.get_db_connector_from_source()
        self._db_source = self.conn_manager.get_db_connector_from_source(SUPPLIES_DB_SOURCE)

        # There may be 1 case where we need to emit a db_connection_changed from the change detection settings dialog:
        #   1) Connection Settings was opened and the DB conn was changed.
        self._db_target_was_changed = False  # To postpone calling refresh gui until we close this dialog instead of settings
        self._db_source_was_changed = False

        self.btn_source_db.clicked.connect(self.show_settings_source_db)
        self.btn_target_db.clicked.connect(self.show_settings_target_db)

        # Initialize
        self.initialize_progress()

        # Set MessageBar for QDialog
        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

        # Set connections
        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.button(QDialogButtonBox.Ok).setText(QCoreApplication.translate("DataModelConverterDialog", "Convert"))
        self.finished.connect(self.finished_slot)
        self.update_connection_info()

        self.restore_settings()

    def progress_changed(self, value):
        QCoreApplication.processEvents()  # Listen to cancel from the user
        self.progress.setValue(int(value))

    def accepted(self):
        self.save_settings()

        self.bar.clearWidgets()  # Remove previous messages

        if LADMNames.SURVEY_1_0_MODEL_KEY not in self._db_source.get_models():
            res = False
            msg = QCoreApplication.translate("DataModelConverterDialog", "Source DB should be based on the Survey V1.0 Model")
            self.show_message(msg, Qgis.Critical)
            return

        self.set_gui_controls_enabled(False)
        self.progress.setVisible(True)
        msg = QCoreApplication.translate("DataModelConverterDialog", "Converting data (this might take a while)...")
        res, msg = self.run_etl(Context())
        if res:
            self.show_message(msg, Qgis.Success)
            self.buttonBox.clear()
            self.buttonBox.setEnabled(True)
            self.buttonBox.addButton(QDialogButtonBox.Close)
        else:
            self.show_message(msg, Qgis.Critical)
        pass

    def run_etl(self, *args):
        import time
        start_execution = time.time()
        self.logger.info(__name__, "Running ETL model...")
        self.print_info(QCoreApplication.translate("DataModelConverterDialog",'Initiating ETL, this can take several minutes'))

        settings = QSettings()
        automatic_values = settings.value('Asistente-LADM-COL/automatic_values/automatic_values_in_batch_mode')
        if automatic_values:
            settings.setValue('Asistente-LADM-COL/automatic_values/automatic_values_in_batch_mode', False)

        db_source = self._db_source
        db_target = self._db_target
        source_layers = {db_source.names.LC_SURVEY_POINT_T: None,
                  db_source.names.LC_CONTROL_POINT_T: None,
                  db_source.names.LC_BOUNDARY_POINT_T: None,
                  db_source.names.LC_BOUNDARY_T: None,
                  db_source.names.POINT_BFS_T: None,
                  db_source.names.LC_PLOT_T: None,
                  db_source.names.LC_BUILDING_T: None,
                  db_source.names.LC_BUILDING_UNIT_T: None,
                  db_source.names.LC_RIGHT_OF_WAY_T: None,
                  db_source.names.COL_VALUE_AREA_T: None,
                  db_source.names.MORE_BFS_T: None,
                  db_source.names.LESS_BFS_T: None,
                  db_source.names.LC_TIPOLOGY_BUILDING_T: None,
                  db_source.names.LC_NON_CONVENTIONAL_QUALIFICATION_T: None,
                  db_source.names.LC_CONVENTIONAL_QUALIFICATION_T: None,
                  db_source.names.LC_GROUP_QUALIFICATION_T: None,
                  db_source.names.LC_BUILDING_OBJECT_T: None,
                  db_source.names.LC_PARCEL_T: None,
                  db_source.names.LC_SURVEY_CADASTRAL_ADDITIONAL_DATA_T: None,
                  db_source.names.LC_PARCEL_NUMBER_NEW_STRUCTURE_T: None,
                  db_source.names.LC_FMI_NEW_STRUCTURE_T: None,
                  db_source.names.LC_CONTACT_VISIT_T: None,
                  db_source.names.LC_CONDOMINIUM_PH_DATA_T: None,
                  db_source.names.LC_REAL_ESTATE_MARKET_OFFERS_T: None,
                  db_source.names.EXT_ADDRESS_S: None,
                  db_source.names.LC_COPROPERTY_T: None,
                  db_source.names.FRACTION_T: None,
                  db_source.names.COL_UE_BAUNIT_T: None,
                  db_source.names.LC_PARTY_T: None,
                  db_source.names.LC_PARTY_CONTACT_T: None,
                  db_source.names.LC_GROUP_PARTY_T: None,
                  db_source.names.MEMBERS_T: None,
                  db_source.names.LC_RIGHT_T: None,
                  db_source.names.LC_RESTRICTION_T: None,
                  db_source.names.LC_ADMINISTRATIVE_SOURCE_T: None,
                  db_source.names.LC_SPATIAL_SOURCE_T: None,
                  db_source.names.EXT_ARCHIVE_S: None,
                  db_source.names.COL_RRR_SOURCE_T: None,
                  db_source.names.COL_UNIT_SOURCE_T: None,
                  db_source.names.COL_UE_SOURCE_T: None,
                  db_source.names.COL_BAUNIT_SOURCE_T: None}
        target_layers = {db_target.names.LC_SURVEY_POINT_T: None,
                  db_target.names.LC_CONTROL_POINT_T: None,
                  db_target.names.LC_BOUNDARY_POINT_T: None,
                  db_target.names.LC_BOUNDARY_T: None,
                  db_target.names.POINT_BFS_T: None,
                  db_target.names.LC_PLOT_T: None,
                  db_target.names.LC_BUILDING_T: None,
                  db_target.names.LC_BUILDING_UNIT_T: None,
                  db_target.names.LC_RIGHT_OF_WAY_T: None,
                  db_target.names.COL_VALUE_AREA_T: None,
                  db_target.names.MORE_BFS_T: None,
                  db_target.names.LESS_BFS_T: None,
                  db_target.names.LC_TIPOLOGY_BUILDING_T: None,
                  db_target.names.LC_NON_CONVENTIONAL_QUALIFICATION_T: None,
                  db_target.names.LC_CONVENTIONAL_QUALIFICATION_T: None,
                  db_target.names.LC_GROUP_QUALIFICATION_T: None,
                  db_target.names.LC_BUILDING_OBJECT_T: None,
                  db_target.names.LC_PARCEL_T: None,
                  db_target.names.LC_SURVEY_CADASTRAL_ADDITIONAL_DATA_T: None,
                  db_target.names.LC_PARCEL_NUMBER_NEW_STRUCTURE_T: None,
                  db_target.names.LC_FMI_NEW_STRUCTURE_T: None,
                  db_target.names.LC_CONTACT_VISIT_T: None,
                  db_target.names.LC_CONDOMINIUM_PH_DATA_T: None,
                  db_target.names.LC_REAL_ESTATE_MARKET_OFFERS_T: None,
                  db_target.names.EXT_ADDRESS_S: None,
                  db_target.names.LC_COPROPERTY_T: None,
                  db_target.names.BUILDING_UNIT_CHARACTERISTICS_T: None,
                  db_target.names.COL_UE_BAUNIT_T: None,
                  db_target.names.LC_PARTY_T: None,
                  db_target.names.LC_PARTY_CONTACT_T: None,
                  db_target.names.LC_GROUP_PARTY_T: None,
                  db_target.names.MEMBERS_T: None,
                  db_target.names.LC_RIGHT_T: None,
                  db_target.names.LC_RESTRICTION_T: None,
                  db_target.names.LC_ADMINISTRATIVE_SOURCE_T: None,
                  db_target.names.LC_SPATIAL_SOURCE_T: None,
                  db_target.names.EXT_ARCHIVE_S: None,
                  db_target.names.COL_RRR_SOURCE_T: None,
                  db_target.names.COL_UNIT_SOURCE_T: None,
                  db_target.names.COL_UE_SOURCE_T: None,
                  db_target.names.COL_BAUNIT_SOURCE_T: None}

        self.print_info(QCoreApplication.translate("DataModelConverterDialog",'Loading layers...'))
        self.app.core.get_layers(db_source, source_layers, load=True)
        self.app.core.get_layers(db_target, target_layers, load=True)

        if not source_layers or not target_layers:
            return False, QCoreApplication.translate("AsistenteLADMCOLPlugin",
                                                                              "Error running the ETL model. Details: Layers for ETL were not loaded")

        params = {'inlcpuntolevantamiento': source_layers[db_source.names.LC_SURVEY_POINT_T],
                  'inlcpuntocontrol': source_layers[db_source.names.LC_CONTROL_POINT_T],
                  'inlcpuntolindero': source_layers[db_source.names.LC_BOUNDARY_POINT_T],
                  'inlclindero': source_layers[db_source.names.LC_BOUNDARY_T],
                  'inpuntoccl': source_layers[db_source.names.POINT_BFS_T],
                  'inlcterreno': source_layers[db_source.names.LC_PLOT_T],
                  'inlcconstruccion': source_layers[db_source.names.LC_BUILDING_T],
                  'inlcunidadconstruccion': source_layers[db_source.names.LC_BUILDING_UNIT_T],
                  'inlcservidumbretransito': source_layers[db_source.names.LC_RIGHT_OF_WAY_T],
                  'incolareavalor': source_layers[db_source.names.COL_VALUE_AREA_T],
                  'incolmasccl': source_layers[db_source.names.MORE_BFS_T],
                  'incolmenosccl': source_layers[db_source.names.LESS_BFS_T],
                  'inlctipologia': source_layers[db_source.names.LC_TIPOLOGY_BUILDING_T],
                  'inlccalificacionnoconvencional': source_layers[db_source.names.LC_NON_CONVENTIONAL_QUALIFICATION_T],
                  'inlccalificacionconvencional': source_layers[db_source.names.LC_CONVENTIONAL_QUALIFICATION_T],
                  'inlcgrupocalificacion': source_layers[db_source.names.LC_GROUP_QUALIFICATION_T],
                  'inlcobjetoconstruccion': source_layers[db_source.names.LC_BUILDING_OBJECT_T],
                  'inlcpredio': source_layers[db_source.names.LC_PARCEL_T],
                  'inlcdatosadicionaleslevantamientocatastral': source_layers[db_source.names.LC_SURVEY_CADASTRAL_ADDITIONAL_DATA_T],
                  'inlcestructuranovedadnumeropredial': source_layers[db_source.names.LC_PARCEL_NUMBER_NEW_STRUCTURE_T],
                  'inlcestructuranovedadfmi': source_layers[db_source.names.LC_FMI_NEW_STRUCTURE_T],
                  'inlccontactovisita': source_layers[db_source.names.LC_CONTACT_VISIT_T],
                  'inlcdatosphcondominio': source_layers[db_source.names.LC_CONDOMINIUM_PH_DATA_T],
                  'inlcofertasmercadoinmobiliario': source_layers[db_source.names.LC_REAL_ESTATE_MARKET_OFFERS_T],
                  'inextdireccion': source_layers[db_source.names.EXT_ADDRESS_S],
                  'inlcprediocopropiedad': source_layers[db_source.names.LC_COPROPERTY_T],
                  'infraccion': source_layers[db_source.names.FRACTION_T],
                  'incoluebaunit': source_layers[db_source.names.COL_UE_BAUNIT_T],
                  'inlcinteresado': source_layers[db_source.names.LC_PARTY_T],
                  'inlcinteresadocontacto': source_layers[db_source.names.LC_PARTY_CONTACT_T],
                  'inlcagrupacioninteresados': source_layers[db_source.names.LC_GROUP_PARTY_T],
                  'incolmiembros': source_layers[db_source.names.MEMBERS_T],
                  'inlcderecho': source_layers[db_source.names.LC_RIGHT_T],
                  'inlcrestriccion': source_layers[db_source.names.LC_RESTRICTION_T],
                  'inlcfuenteadministrativa': source_layers[db_source.names.LC_ADMINISTRATIVE_SOURCE_T],
                  'inlcfuenteespacial': source_layers[db_source.names.LC_SPATIAL_SOURCE_T],
                  'inextarchivo': source_layers[db_source.names.EXT_ARCHIVE_S],
                  'incolrrrfuente': source_layers[db_source.names.COL_RRR_SOURCE_T],
                  'incolunidadfuente': source_layers[db_source.names.COL_UNIT_SOURCE_T],
                  'incoluefuente': source_layers[db_source.names.COL_UE_SOURCE_T],
                  'incolbaunitfuente': source_layers[db_source.names.COL_BAUNIT_SOURCE_T],
                  'outlcpuntolevantamiento': target_layers[db_target.names.LC_SURVEY_POINT_T],
                  'outlcpuntocontrol': target_layers[db_target.names.LC_CONTROL_POINT_T],
                  'outlcpuntolindero': target_layers[db_target.names.LC_BOUNDARY_POINT_T],
                  'outlclindero': target_layers[db_target.names.LC_BOUNDARY_T],
                  'outpuntoccl': target_layers[db_target.names.POINT_BFS_T],
                  'outlcterreno': target_layers[db_target.names.LC_PLOT_T],
                  'outlcconstruccion': target_layers[db_target.names.LC_BUILDING_T],
                  'outlcunidadconstruccion': target_layers[db_target.names.LC_BUILDING_UNIT_T],
                  'outlcservidumbretransito': target_layers[db_target.names.LC_RIGHT_OF_WAY_T],
                  'outcolareavalor': target_layers[db_target.names.COL_VALUE_AREA_T],
                  'outcolmasccl': target_layers[db_target.names.MORE_BFS_T],
                  'outcolmenosccl': target_layers[db_target.names.LESS_BFS_T],
                  'outlctipologia': target_layers[db_target.names.LC_TIPOLOGY_BUILDING_T],
                  'outlccalificacionnoconvencional': target_layers[db_target.names.LC_NON_CONVENTIONAL_QUALIFICATION_T],
                  'outlccalificacionconvencional': target_layers[db_target.names.LC_CONVENTIONAL_QUALIFICATION_T],
                  'outlcgrupocalificacion': target_layers[db_target.names.LC_GROUP_QUALIFICATION_T],
                  'outlcobjetoconstruccion': target_layers[db_target.names.LC_BUILDING_OBJECT_T],
                  'outlcpredio': target_layers[db_target.names.LC_PARCEL_T],
                  'outlcdatosadicionaleslevantamientocatastral': target_layers[db_target.names.LC_SURVEY_CADASTRAL_ADDITIONAL_DATA_T],
                  'outlcestructuranovedadnumeropredial': target_layers[db_target.names.LC_PARCEL_NUMBER_NEW_STRUCTURE_T],
                  'outlcestructuranovedadfmi': target_layers[db_target.names.LC_FMI_NEW_STRUCTURE_T],
                  'outlccontactovisita': target_layers[db_target.names.LC_CONTACT_VISIT_T],
                  'outlcdatosphcondominio': target_layers[db_target.names.LC_CONDOMINIUM_PH_DATA_T],
                  'outlcofertasmercadoinmobiliario': target_layers[db_target.names.LC_REAL_ESTATE_MARKET_OFFERS_T],
                  'outextdireccion': target_layers[db_target.names.EXT_ADDRESS_S],
                  'outlcprediocopropiedad': target_layers[db_target.names.LC_COPROPERTY_T],
                  'outlccaracteristicasunidadconstruccion': target_layers[db_target.names.BUILDING_UNIT_CHARACTERISTICS_T],
                  'outcoluebaunit': target_layers[db_target.names.COL_UE_BAUNIT_T],
                  'outlcinteresado': target_layers[db_target.names.LC_PARTY_T],
                  'outlcinteresadocontacto': target_layers[db_target.names.LC_PARTY_CONTACT_T],
                  'outlcagrupacioninteresados': target_layers[db_target.names.LC_GROUP_PARTY_T],
                  'outcolmiembros': target_layers[db_target.names.MEMBERS_T],
                  'outlcderecho': target_layers[db_target.names.LC_RIGHT_T],
                  'outlcrestriccion': target_layers[db_target.names.LC_RESTRICTION_T],
                  'outlcfuenteadministrativa': target_layers[db_target.names.LC_ADMINISTRATIVE_SOURCE_T],
                  'outlcfuenteespacial': target_layers[db_target.names.LC_SPATIAL_SOURCE_T],
                  'outextarchivo': target_layers[db_target.names.EXT_ARCHIVE_S],
                  'outcolrrrfuente': target_layers[db_target.names.COL_RRR_SOURCE_T],
                  'outcolunidadfuente': target_layers[db_target.names.COL_UNIT_SOURCE_T],
                  'outcoluefuente': target_layers[db_target.names.COL_UE_SOURCE_T],
                  'outcolbaunitfuente': target_layers[db_target.names.COL_BAUNIT_SOURCE_T]}

        f = QgsProcessingFeedback()
        f.progressChanged.connect(self.progress_changed)

        self.print_info(QCoreApplication.translate("DataModelConverterDialog",'Initiating migration process...'))

        try:
            processing.run("model:ETL_SURVEY_1_0_TO_1_2", params, feedback=f)
            self.logger.info(__name__, "ETL model finished!")
            self.print_info(QCoreApplication.translate("DataModelConverterDialog",'\nRESULTS:\n'))
            etl_log = f.textLog()
            self.print_success_text(etl_log)
            self.print_info("""\n\nINFORMACIÓN ADICIONAL:\nPRECAUCIÓN:\nSi los predios no tienen datos adicionales de levantamiento catastral de origen se toman los siguientes valores por defecto:\n\nDestinacion_Economica: Habitacional\nClase_Suelo: Urbano\nAsí mismo, se asumen los siguientes valores por defecto por inexistencia en la tabla LC_Predio:\nCodigo_Homologado: NULL\nInterrelacionado: False\nCodigo_Homologado_FMI: NULL\nValor_Referencia: NULL\n\nEn LC_DatosAdicionalesLevantamientoCatastral:\nOtro_Cual_Resultado: NULL\nDespojo_Abandono: NULL\nEstrato: NULL\nOtro_Cual_Estrato: NULL\n\nEn LC_Interesado:\nEstado_Civil: NULL\n\nEn LC_Construccion:\nValor de referencia: NULL\n\nEn LC_TipologiaConstruccion:\nCual: NULL""",
            '#0000FF')
            self.clean_layer_tree()
            time_execution = time.time() - start_execution
            self.print_info(QCoreApplication.translate("DataModelConverterDialog", '\n\nMigration successfully completed in {} seconds!'.format(round(time_execution, 1))), '#008000')
            self.app.gui.redraw_all_layers()
            if automatic_values:
                settings.setValue('Asistente-LADM-COL/automatic_values/automatic_values_in_batch_mode', True)
            return True, QCoreApplication.translate("DataModelConverterDialog", "Migration successfully completed!")
        except QgsProcessingException as e:
            self.logger.warning_msg(__name__, QCoreApplication.translate("AsistenteLADMCOLPlugin",
                                                                                 "There was an error running the ETL model. See the QGIS log for details."))
            self.logger.critical(__name__, QCoreApplication.translate("AsistenteLADMCOLPlugin",
                                                                              "Error running the ETL model. Details: {}").format(
                str(e)))
            return False, QCoreApplication.translate("AsistenteLADMCOLPlugin",
                                                                              "Error running the ETL model. Details: {}").format(
                str(e))

    def print_success_text(self, text):
        import re
        success_list = re.findall('[0-9]+ out of [0-9]+ features from input layer were successfully copied into \'.*', text)
        for success in success_list:
            self.print_info(success)

    def clean_layer_tree(self):
        self.print_info(QCoreApplication.translate("DataModelConverterDialog",'\nCleaning Layertree...\n'))
        QgsProject.instance().removeAllMapLayers()
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup('tables')
        root.removeChildNode(group)
        group = root.findGroup('domains')
        root.removeChildNode(group)

    def reject(self):
        if self._running_tool:
            reply = QMessageBox.question(self,
                                         QCoreApplication.translate("DataModelConverterDialog", "Warning"),
                                         QCoreApplication.translate("DataModelConverterDialog",
                                                                    "The '{}' tool is still running. Do you want to cancel it? If you cancel, the data might be incomplete in the target database.").format(self.tool_name),
                                         QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self._running_tool = False
                msg = QCoreApplication.translate("DataModelConverterDialog", "The '{}' tool was cancelled.").format(self.tool_name)
                self.logger.info(__name__, msg)
                self.show_message(msg, Qgis.Info)
        else:
            self.logger.info(__name__, "Dialog closed.")
            self.done(1)

    def finished_slot(self, result):
        self.bar.clearWidgets()
        pass

    def set_init_db_config(self):
        """
         A copy of the initial connections to the database is made,
         User can change the initial connections and then cancel the changes.
         Initial connections need to be re-established
        """
        self.init_db_target = self.conn_manager.get_db_connector_from_source(COLLECTED_DB_SOURCE)
        self.init_db_source = self.conn_manager.get_db_connector_from_source(SUPPLIES_DB_SOURCE)

    def show_settings_target_db(self):
        self.settings_dialog.setWindowTitle(QCoreApplication.translate("DataModelConverterDialog", "TARGET DB Connection Settings"))
        self.settings_dialog.set_db_source(COLLECTED_DB_SOURCE)
        self.settings_dialog.set_tab_pages_list([SETTINGS_CONNECTION_TAB_INDEX])
        self.settings_dialog.set_required_models([LADMNames.SURVEY_MODEL_KEY])
        self.settings_dialog.db_connection_changed.connect(self.db_connection_changed)

        if self.settings_dialog.exec_():
            self._db_target = self.settings_dialog.get_db_connection()
            self.update_connection_info()
        self.settings_dialog.db_connection_changed.disconnect(self.db_connection_changed)

    def show_settings_source_db(self):
        self.settings_dialog.setWindowTitle(QCoreApplication.translate("DataModelConverterDialog", "SOURCE DB Connection Settings"))
        self.settings_dialog.set_db_source(SUPPLIES_DB_SOURCE)
        self.settings_dialog.set_tab_pages_list([SETTINGS_CONNECTION_TAB_INDEX])
        self.settings_dialog.set_required_models([LADMNames.SURVEY_1_0_MODEL_KEY])
        self.settings_dialog.db_connection_changed.connect(self.db_connection_changed)

        if self.settings_dialog.exec_():
            self._db_source = self.settings_dialog.get_db_connection()
            self.update_connection_info()
        self.settings_dialog.db_connection_changed.disconnect(self.db_connection_changed)

    def db_connection_changed(self, db, ladm_col_db, db_source):
        # We dismiss parameters here, after all, we already have the db, and the ladm_col_db
        # may change from this moment until we close the import schema dialog
        if db_source == COLLECTED_DB_SOURCE:
            self._db_target_was_changed = True
            self._schedule_layers_and_relations_refresh = True
        else:
            self._db_source_was_changed = True

    def update_connection_info(self):
        # Validate db connections
        self.lbl_msg_collected.setText("")
        self.lbl_msg_supplies.setText("")
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        # First, update status of same_db button according to collected db connection
        res_target, code_collected, msg_collected = self._db_target.test_connection(models={REQUIRED_MODELS: [LADMNames.SURVEY_MODEL_KEY]})
        res_source, code_supplies, msg_supplies = self._db_source.test_connection(models={REQUIRED_MODELS: [LADMNames.SURVEY_1_0_MODEL_KEY]})

        db_description = self._db_source.get_description_conn_string()
        if db_description:
            self.db_source_connect_label.setText(db_description)
            self.db_source_connect_label.setToolTip(self._db_source.get_display_conn_string())
        else:
            self.db_source_connect_label.setText(QCoreApplication.translate("DataModelConverterDialog", "The database is not defined!"))
            self.db_source_connect_label.setToolTip('')

        # Update collected db connection label
        db_description = self._db_target.get_description_conn_string()
        if db_description:
            self.db_target_connect_label.setText(db_description)
            self.db_target_connect_label.setToolTip(self._db_target.get_display_conn_string())
        else:
            self.db_target_connect_label.setText(QCoreApplication.translate("DataModelConverterDialog", "The database is not defined!"))
            self.db_target_connect_label.setToolTip('')

        # Update error message labels
        if not res_target:
            self.lbl_msg_collected.setText(QCoreApplication.translate("DataModelConverterDialog", "Warning: DB connection is not valid"))
            self.lbl_msg_collected.setToolTip(msg_collected)

        if not res_source:
            self.lbl_msg_supplies.setText(QCoreApplication.translate("DataModelConverterDialog", "Warning: DB connection is not valid"))
            self.lbl_msg_supplies.setToolTip(msg_supplies)

        if res_target and res_source:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    def selected_converter_changed(self, index):
        # Ideas for this:
        #   Some converters might need new wizard pages. So this slot should get them from the controller
        #   and pass them to a method that shows them, converting first the single-page wizard into multi-page.
        pass

    def set_convert_button_enabled(self, enable):
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enable)

    def initialize_progress(self):
        self.progress.setValue(0)
        self.progress.setVisible(False)

    def set_gui_controls_enabled(self, enable):
        self.set_convert_button_enabled(enable)

    def save_settings(self):
        settings = QSettings()

        # In the main page (source-target configuration), save if splitter is closed
        self.app.settings.xtf_converter_splitter_collapsed = self.splitter.sizes()[1] == 0
        
    def restore_settings(self):
        settings = QSettings()

        # If splitter in the main page was closed before, set it as closed again
        if self.app.settings.xtf_converter_splitter_collapsed:
            sizes = self.splitter.sizes()
            self.splitter.setSizes([sizes[0], 0])
        pass

    def print_info(self, text, text_color='#000000', clear=False):
        self.txtStdout.setTextColor(QColor(text_color))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def show_message(self, message, level, duration=0):
        self.bar.clearWidgets()  # Remove previous messages before showing a new one
        self.bar.pushMessage(message, level, duration)
