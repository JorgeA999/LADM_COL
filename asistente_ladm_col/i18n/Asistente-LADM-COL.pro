FORMS = ../ui/change_detection/changes_all_parcels_panel_widget.ui \
        ../ui/change_detection/changes_parties_panel_widget.ui \
        ../ui/change_detection/changes_per_parcel_panel_widget.ui \
        ../ui/change_detection/dlg_change_detection_settings.ui \
        ../ui/change_detection/dlg_select_duplicate_parcel_change_detection.ui \
        ../ui/change_detection/dockwidget_change_detection.ui \
        ../ui/change_detection/parcels_changes_summary_panel_widget.ui \
        ../ui/data_model_converter/dlg_data_model_converter.ui \
        ../ui/dialogs/dlg_about.ui \
        ../ui/dialogs/dlg_custom_model_dir.ui \
        ../ui/dialogs/dlg_get_db_or_schema_name.ui \
        ../ui/dialogs/dlg_import_from_excel.ui \
        ../ui/dialogs/dlg_load_layers.ui \
        ../ui/dialogs/dlg_log_quality.ui \
        ../ui/dialogs/dlg_quality.ui \
        ../ui/dialogs/dlg_settings.ui \
        ../ui/dialogs/dlg_topological_edition.ui \
        ../ui/dialogs/dlg_upload_progress.ui \
        ../ui/dialogs/dlg_welcome_screen.ui \
	    ../ui/dialogs/settings_gpkg.ui \
	    ../ui/dialogs/settings_pg.ui \
	    ../ui/dialogs/settings_mssql.ui \
	    ../ui/field_data_capture/allocate_parcels_initial_panel_widget.ui \
	    ../ui/field_data_capture/allocate_parcels_to_surveyor.ui \
	    ../ui/field_data_capture/configure_surveyors.ui \
	    ../ui/field_data_capture/dockwidget_field_data_capture.ui \
        ../ui/dockwidgets/dockwidget_queries.ui \
        ../ui/qgis_model_baker/dlg_import_schema.ui \
        ../ui/qgis_model_baker/dlg_import_data.ui \
        ../ui/qgis_model_baker/dlg_export_data.ui \
        ../ui/supplies/cobol_data_source_widget.ui \
        ../ui/supplies/dlg_missing_supplies.ui \
        ../ui/supplies/snc_data_source_widget.ui \
        ../ui/supplies/wig_cobol_supplies.ui \
        ../ui/supplies/wiz_supplies_etl.ui \
        ../ui/transitional_system/dlg_cancel_task.ui \
        ../ui/transitional_system/dlg_login_st.ui \
        ../ui/transitional_system/dlg_upload_file.ui \
        ../ui/transitional_system/dockwidget_transitional_system.ui \
        ../ui/transitional_system/home_widget.ui \
        ../ui/transitional_system/task_widget_item.ui \
        ../ui/transitional_system/tasks_widget.ui \
        ../ui/transitional_system/transitional_system_initial_panel_widget.ui \
        ../ui/transitional_system/transitional_system_task_panel_widget.ui \
        ../ui/wizards/survey/dlg_group_party.ui \
	    ../ui/wizards/survey/wiz_associate_extaddress_survey.ui \
        ../ui/wizards/survey/wiz_create_administrative_source_survey.ui \
        ../ui/wizards/survey/wiz_create_boundaries_survey.ui \
        ../ui/wizards/survey/wiz_create_building_survey.ui \
        ../ui/wizards/survey/wiz_create_building_unit_survey.ui \
        ../ui/wizards/survey/wiz_create_col_party_survey.ui \
        ../ui/wizards/survey/wiz_create_parcel_survey.ui \
        ../ui/wizards/survey/wiz_create_plot_survey.ui \
        ../ui/wizards/survey/wiz_create_points_survey.ui \
        ../ui/wizards/survey/wiz_create_restriction_survey.ui \
        ../ui/wizards/survey/wiz_create_right_of_way_survey.ui \
        ../ui/wizards/survey/wiz_create_right_survey.ui \
        ../ui/wizards/survey/wiz_create_spatial_source_survey.ui \
        ../ui/wizards/valuation/wiz_create_building_unit_qualification_valuation.ui \
        ../ui/wizards/valuation/wiz_create_building_unit_valuation.ui \
        ../ui/wizards/valuation/wiz_create_geoeconomic_zone_valuation.ui \
        ../ui/wizards/valuation/wiz_create_physical_zone_valuation.ui

SOURCES = ../__init__.py \
          ../app_interface.py \
          ../asistente_ladm_col_plugin.py \
          ../config/change_detection_config.py \
          ../config/config_db_supported.py \
          ../config/gui/gui_config.py \
          ../config/help_strings.py \
          ../config/ladm_names.py \
          ../config/layer_tree_indicator_config.py \
          ../config/mapping_config.py \
          ../config/quality_rules_config.py \
          ../config/role_config.py \
          ../config/task_steps_config.py \
          ../config/transitional_system_config.py \
          ../config/translation_strings.py \
          ../config/wizard_config.py \
          ../core/app_core_interface.py \
          ../gui/app_gui_interface.py \
          ../gui/change_detection/changes_all_parcels_panel.py \
          ../gui/change_detection/changes_parties_panel.py \
          ../gui/change_detection/changes_per_parcel_panel.py \
          ../gui/change_detection/dlg_change_detection_settings.py \
          ../gui/change_detection/dlg_select_duplicate_parcel_change_detection.py \
          ../gui/change_detection/dockwidget_change_detection.py \
          ../gui/change_detection/parcels_changes_summary_panel.py \
          ../gui/data_model_converter/dlg_data_model_converter.py \
          ../gui/db_panel/db_schema_db_panel.py \
          ../gui/db_panel/gpkg_config_panel.py \
          ../gui/db_panel/mssql_config_panel.py \
          ../gui/db_panel/pg_config_panel.py \
          ../gui/dialogs/dlg_about.py \
          ../gui/dialogs/dlg_custom_model_dir.py \
          ../gui/dialogs/dlg_get_db_or_schema_name.py \
          ../gui/dialogs/dlg_import_from_excel.py \
          ../gui/dialogs/dlg_load_layers.py \
          ../gui/dialogs/dlg_log_quality.py \
          ../gui/dialogs/dlg_quality.py \
          ../gui/dialogs/dlg_settings.py \
          ../gui/dialogs/dlg_topological_edition.py \
          ../gui/dialogs/dlg_upload_progress.py \
          ../gui/dialogs/dlg_welcome_screen.py \
          ../gui/field_data_capture/allocate_parcels_initial_panel.py \
          ../gui/field_data_capture/allocate_parcels_to_surveyor_panel.py \
          ../gui/field_data_capture/configure_surveyors_panel.py \
          ../gui/field_data_capture/dockwidget_field_data_capture.py \
          ../gui/gui_builder/gui_builder.py \
          ../gui/gui_builder/role_registry.py \
          ../gui/qgis_model_baker/dlg_import_schema.py \
          ../gui/qgis_model_baker/dlg_import_data.py \
          ../gui/qgis_model_baker/dlg_export_data.py \
          ../gui/queries/dockwidget_queries.py \
          ../gui/reports/reports.py \
          ../gui/right_of_way.py \
          ../gui/supplies/dlg_missing_cobol_supplies.py \
          ../gui/supplies/dlg_missing_snc_supplies.py \
          ../gui/supplies/dlg_missing_supplies_base.py \
          ../gui/supplies/snc_data_sources_widget.py \
          ../gui/supplies/wiz_supplies_etl.py \
          ../gui/toolbar.py \
          ../gui/transitional_system/dlg_cancel_task.py \
          ../gui/transitional_system/dlg_login_st.py \
          ../gui/transitional_system/dlg_upload_file.py \
          ../gui/transitional_system/task_panel.py \
          ../gui/transitional_system/tasks_widget.py \
          ../gui/transitional_system/transitional_system_initial_panel.py \
          ../gui/wizards/abs_wizard_factory.py \
          ../gui/wizards/map_interaction_expansion.py \
          ../gui/wizards/multi_page_spatial_wizard_factory.py \
          ../gui/wizards/multi_page_wizard_factory.py \
          ../gui/wizards/select_features_on_map_wrapper.py \
          ../gui/wizards/single_page_spatial_wizard_factory.py \
          ../gui/wizards/single_page_wizard_factory.py \
          ../gui/wizards/spatial_wizard_factory.py \
          ../gui/wizards/survey/dlg_create_group_party_survey.py \
          ../gui/wizards/survey/wiz_create_ext_address_survey.py \
          ../gui/wizards/survey/wiz_create_parcel_survey.py \
          ../gui/wizards/survey/wiz_create_plot_survey.py \
          ../gui/wizards/survey/wiz_create_points_survey.py \
          ../gui/wizards/survey/wiz_create_right_of_way_survey.py \
          ../gui/wizards/survey/wiz_create_rrr_survey.py \
          ../gui/wizards/survey/wiz_create_spatial_source_survey.py \
          ../gui/wizards/valuation/wiz_create_building_unit_qualification_valuation.py \
          ../gui/wizards/valuation/wiz_create_building_unit_valuation.py \
          ../gui/wizards/wizard_factory.py \
          ../lib/context.py \
          ../lib/db/db_connection_manager.py \
          ../lib/db/db_connector.py \
          ../lib/db/gpkg_connector.py \
          ../lib/db/mssql_connector.py \
          ../lib/db/pg_connector.py \
          ../lib/dependency/crypto_dependency.py \
          ../lib/dependency/dependency.py \
          ../lib/dependency/java_dependency.py \
          ../lib/dependency/plugin_dependency.py \
          ../lib/dependency/report_dependency.py \
          ../lib/geometry.py \
          ../lib/processing/algs/InsertFeaturesToLayer.py \
          ../lib/processing/algs/PolygonsToLines.py \
          ../lib/quality_rule/quality_rule.py \
          ../lib/source_handler.py \
          ../lib/transitional_system/st_session/st_session.py \
          ../lib/transitional_system/task_manager/task_manager.py \
          ../lib/transitional_system/task_manager/task_steps.py \
          ../logic/quality/line_quality_rules.py \
          ../logic/quality/logic_quality_rules.py \
          ../logic/quality/point_quality_rules.py \
          ../logic/quality/polygon_quality_rules.py \
          ../logic/quality/quality_rule_engine.py \
          ../logic/quality/quality_rule_layer_manager.py \
          ../logic/quality/quality_rules.py \
          ../logic/quality_rules/qr_boundary_points_covered_plot_nodes.py \
          ../logic/quality_rules/qr_boundary_points_not_covered_by_boundary_nodes.py \
          ../logic/quality_rules/qr_duplicate_administrative_source_records.py \
          ../logic/quality_rules/qr_duplicate_boundary_point_records.py \
          ../logic/quality_rules/qr_duplicate_boundary_records.py \
          ../logic/quality_rules/qr_duplicate_building_records.py \
          ../logic/quality_rules/qr_duplicate_building_unit_records.py \
          ../logic/quality_rules/qr_duplicate_control_point_records.py \
          ../logic/quality_rules/qr_duplicate_party_records.py \
          ../logic/quality_rules/qr_duplicate_restriction_records.py \
          ../logic/quality_rules/qr_duplicate_right_records.py \
          ../logic/quality_rules/qr_duplicate_survey_point_records.py \
          ../logic/quality_rules/qr_gaps_in_plots.py \
          ../logic/quality_rules/qr_group_party_percentage_that_do_not_make_one.py \
          ../logic/quality_rules/qr_multiparts_in_right_of_way.py \
          ../logic/quality_rules/qr_overlapping_boundaries.py \
          ../logic/quality_rules/qr_overlapping_boundary_points.py \
          ../logic/quality_rules/qr_overlapping_buildings.py \
          ../logic/quality_rules/qr_overlapping_control_points.py \
          ../logic/quality_rules/qr_overlapping_right_of_ways_buildings.py \
          ../logic/quality_rules/qr_overlapping_right_of_ways.py \
          ../logic/quality_rules/qr_parcel_right_relationship.py \
          ../logic/quality_rules/qr_parcel_with_invalid_department_code.py \
          ../logic/quality_rules/qr_parcel_with_invalid_municipality_code.py \
          ../logic/quality_rules/qr_parcel_with_invalid_parcel_number.py \
          ../logic/quality_rules/qr_parcel_with_invalid_previous_parcel_number.py \
          ../logic/quality_rules/qr_plot_nodes_covered_boundary_points.py \
          ../logic/quality_rules/qr_plots_covered_by_boundaries.py \
          ../logic/quality_rules/qr_validate_data_against_model.py \
          ../logic/quality_rules/qr_validate_legal_party.py \
          ../logic/quality_rules/qr_validate_natural_party.py \
          ../utils/decorators.py \
          ../utils/qgis_model_baker_utils.py \
          ../utils/qt_utils.py \
          ../utils/st_utils.py \
          ../utils/utils.py

TRANSLATIONS = Asistente-LADM-COL_es.ts
