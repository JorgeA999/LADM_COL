"""
/***************************************************************************
                              Asistente LADM-COL
                             --------------------
        begin                : 2020-06-01
        copyright            : (C) 2020 by Germán Carrillo (SwissTierras Colombia)
        email                : gcarrillo@linuxmail.org
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 ***************************************************************************/
"""
import os.path
import time
import getpass

from qgis.PyQt.QtCore import (QCoreApplication,
                              QObject,
                              pyqtSignal)
from qgis.core import Qgis

from asistente_ladm_col.app_interface import AppInterface
from asistente_ladm_col.config.general_config import QR_METADATA_TOOL_NAME
from asistente_ladm_col.config.quality_rule_config import (QR_METADATA_TOOL,
                                                           QR_METADATA_DATA_SOURCE,
                                                           QR_METADATA_TOLERANCE,
                                                           QR_METADATA_TIMESTAMP,
                                                           QR_METADATA_RULES,
                                                           QR_METADATA_PERSON)
from asistente_ladm_col.core.quality_rules.quality_rule_layer_manager import QualityRuleLayerManager
from asistente_ladm_col.core.quality_rules.quality_rule_execution_result import (QualityRulesExecutionResult,
                                                                                 QualityRuleExecutionResult)
from asistente_ladm_col.core.quality_rules.quality_rule_registry import QualityRuleRegistry
from asistente_ladm_col.lib.logger import Logger
from asistente_ladm_col.lib.quality_rule.quality_rule_manager import QualityRuleManager
from asistente_ladm_col.utils.decorators import _log_quality_rule_validations
from asistente_ladm_col.utils.quality_error_db_utils import (get_quality_error_connector,
                                                             get_quality_validation_output_path,
                                                             save_metadata)
from asistente_ladm_col.utils.qt_utils import export_title_text_to_pdf
from asistente_ladm_col.utils.utils import Utils


class QualityRuleEngine(QObject):
    """
    Engine that executes Quality Rules

    :param db: DBConnector object
    :param rules: Either a dict {rule_key:rule_name} or a list [rule_key1, rule_key2]
    :param tolerance: Tolerance to be used when running the QRs, in millimeters
    """
    def __init__(self, db, rules, tolerance, output_path=''):
        QObject.__init__(self)
        self.logger = Logger()
        self.app = AppInterface()

        self.__qr_registry = QualityRuleRegistry()

        self.__db = db
        self.__db_qr = None
        self.__rules = self.__get_dict_rules(rules)
        self.__result_layers = list()
        self.__with_gui = self.app.settings.with_gui

        self.__output_path = output_path

        self.app.settings.tolerance = tolerance  # Tolerance must be given, we don't want anything implicit about it
        self.__tolerance = self.app.settings.tolerance  # Tolerance input might be altered (e.g., if it comes negative)
        self.__layer_manager = QualityRuleLayerManager(db, self.__rules, self.__tolerance)
        self.quality_rule_logger = QualityRuleLogger(self.__db, self.__tolerance)

        # Clear informality cache before executing QRs.
        # Note: between creating an object of this class and calling validate_quality_rules() a lot
        # of things could happen (like new caches being built!). It is your responsibility to create
        # an instance of this class or initialize() a QREngine object just before calling validate_quality_rules().
        self.app.core.clear_cached_informal_spatial_units()

    def initialize(self, db, rules, tolerance, output_path='', clear_informality_cache=True):
        """
        Objects of this class are reusable calling initialize()
        """
        self.__result_layers = list()
        self.__db = db
        self.__db_qr = None
        self.__rules = self.__get_dict_rules(rules)
        self.__with_gui = self.app.settings.with_gui

        self.__output_path = output_path

        self.app.settings.tolerance = tolerance
        self.__tolerance = self.app.settings.tolerance  # Tolerance input might be altered (e.g., if it comes negative)
        self.__layer_manager.initialize(self.__rules, self.__tolerance)
        self.quality_rule_logger.initialize(self.__db, self.__tolerance)

        # This time, (initializing an existing object) we give you the chance to avoid
        # rebuilding the informality cache. It is handy if you're executing validations
        # consecutively and you're sure that reusing a previous cache does make sense.
        if clear_informality_cache:
            self.app.core.clear_cached_informal_spatial_units()

    def __get_dict_rules(self, rules):
        if isinstance(rules, dict):
            return rules  # We have everything ready

        # If rules is a list, we need to retrieve the quality rule names from the QRRegistry
        return {rule_key: self.__qr_registry.get_quality_rule(rule_key) for rule_key in rules}

    def validate_quality_rules(self, options=dict()):
        """
        :param options: Dict of dicts with of options per rule. {qr1_key: {qr1_opt1: value1, ...}, ...}
        """
        res = False
        msg = ""
        qr_res = dict()  # {rule_key: QualityRuleExecutionResult}
        if self.__rules:
            # First, create the error db and fill its metadata...
            self.__timestamp = time.strftime('%Y%m%d_%H%M%S')
            res_db, msg_db, self.__db_qr = get_quality_error_connector(self.__output_path, self.__timestamp, True)

            if not res_db:
                self.logger.warning_msg(__name__, QCoreApplication.translate("QualityRuleEngine",
                                                                             "There was a problem creating the quality error DB! Details:").format(msg_db))
                return False, msg_db, None

            self.quality_rule_logger.set_count_topology_rules(len(self.__rules))
            self.logger.info(__name__,
                             QCoreApplication.translate("QualityRuleEngine",
                                "Validating {} quality rules (tolerance: {}).").format(len(self.__rules), self.__tolerance))

            for rule_key, rule in self.__rules.items():
                if rule is not None:
                    layers = self.__layer_manager.get_layers(rule_key)
                    if layers:
                        qr_res[rule_key] = self.__validate_quality_rule(rule, layers, options.get(rule_key, dict()))
                        # if self.__with_gui:
                        #     self.add_error_layers(qr_res[rule_key].error_layers)
                    else:
                        qr_msg = QCoreApplication.translate("QualityRuleEngine",
                                "Couldn't execute '{}' quality rule! Required layers are not available. Skipping...").format(rule.name())
                        qr_res[rule_key] = QualityRuleExecutionResult(Qgis.Critical, qr_msg)
                        self.logger.warning(__name__, qr_msg)
                else:
                    qr_msg = QCoreApplication.translate("QualityRuleEngine",
                                                     "Quality rule with key '{}' does not exist or is not registered! Skipping...").format(
                        rule_key)
                    qr_res[rule_key] = QualityRuleExecutionResult(Qgis.Critical, qr_msg)
                    self.logger.warning(__name__, qr_msg)

            metadata = {QR_METADATA_TOOL: QR_METADATA_TOOL_NAME,
                        QR_METADATA_DATA_SOURCE: self.__db.get_description_conn_string(),
                        QR_METADATA_TOLERANCE: self.__tolerance/1000,
                        QR_METADATA_TIMESTAMP: self.__timestamp,
                        QR_METADATA_RULES: list(self.__rules.keys()),  # QR keys
                        QR_METADATA_PERSON: getpass.getuser()}
            save_metadata(self.__db_qr, metadata)

            res = True
            msg = "Success!"
            self.quality_rule_logger.generate_log_button()
            self.__layer_manager.clean_temporary_layers()

            self.export_result_to_pdf()
        else:
            self.logger.warning(__name__, QCoreApplication.translate("QualityRuleEngine", "No rules to validate!"))

        return res, msg, QualityRulesExecutionResult(qr_res)

    @_log_quality_rule_validations
    def __validate_quality_rule(self, rule, layers, options):
        """
        Intermediate function to log quality rule execution.

        :param rule: Quality rule instance
        :param layers: Layer dict with the layers the quality rule needs (ready to use for tolerance > 0 scenarios)
        :param options: Dict of options per rule. {qr1_opt1: value1, ...}
        :return: An instance of QualityRuleExecutionResult
        """
        return rule.validate(self.__db, self.__db_qr, layers, self.__tolerance, options=options)

    def add_error_layers(self, error_layers):
        for error_layer in error_layers:
            if error_layer.featureCount():  # Only load error layers that have at least one feature
                self.app.gui.add_error_layer(None, error_layer)

    def get_db_quality(self):
        return self.__db_qr

    def export_result_to_pdf(self):
        output_path = get_quality_validation_output_path(self.__output_path, self.__timestamp)
        if output_path is None:
            self.logger.critical(__name__, QCoreApplication.translate("QualityRuleEngine",
                                                                      "PDF report could not be exported, there were problems with the output path '{}'!").format(
                self.__output_path))
            return

        pdf_path = os.path.join(output_path, "Reglas_de_Calidad_{}.pdf".format(self.__timestamp))
        log = self.quality_rule_logger.get_log_result()
        export_title_text_to_pdf(pdf_path, log.title, log.text)


class QualityRuleLogger(QObject):
    """
    Works with the @_log_quality_rule_validations decorator to log both text
    and time for each quality rule executed.
    """
    show_message_emitted = pyqtSignal(str, int)
    show_button_emitted = pyqtSignal()
    set_initial_progress_emitted = pyqtSignal(str)
    set_final_progress_emitted = pyqtSignal(str)

    def __init__(self, db, tolerance):
        QObject.__init__(self)
        self.log_text = ""
        self.log_total_time = 0
        self.tolerance = tolerance
        self.__db = db

    def initialize(self, db, tolerance):
        """
        Objects of this class are reusable calling initialize()
        """
        self.log_text = ""
        self.log_total_time = 0
        self.tolerance = tolerance
        self.__db = db

    def set_count_topology_rules(self, count):
        self.show_message_emitted.emit(QCoreApplication.translate("QualityDialog", ""), count)

    def generate_log_button(self):
        self.show_button_emitted.emit()

    def get_log_result(self):
        return QualityRuleResultLog(self.__db, self.log_text, self.tolerance, self.log_total_time)


class QualityRuleResultLog(QObject):
    def __init__(self, db, log_text, tolerance, log_total_time):
        QObject.__init__(self)
        self.__db = db
        self.text = log_text
        self.tolerance = tolerance
        self.log_total_time = log_total_time

    @property
    def title(self):
        return QCoreApplication.translate(
            "QualityRuleResultLog",
            "<h2 align='center'>Quality Check Results</h2><div style='text-align:center;'>{}<br>Database: {}<br>Total execution time: {}<br>Tolerance {}mm.</div>").format(
            time.strftime("%d/%m/%y %H:%M:%S"),
            self.__db.get_description_conn_string(),
            Utils.set_time_format(self.log_total_time),
            self.tolerance)
