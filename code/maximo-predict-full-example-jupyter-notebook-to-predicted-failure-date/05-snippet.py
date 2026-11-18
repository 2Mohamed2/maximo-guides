from pmlib import api as _api
_t = _api.get_new_monitor_table_name_for_prediction_result
_api.get_new_monitor_table_name_for_prediction_result = lambda db, name, cols: _t(db, asset_group_id, cols)
group._write(df)
