// AppCustomizations.js: your code, kept apart from IBM's controllers
class AppCustomizations {
  applicationInitialized(app) {
    this.app = app;
  }
  // show only work orders of my own organization, whatever list is chosen
  onBeforeLoadData(datasource, query) {
    if (datasource.name !== 'todaywoassignedDS') return;
    const mine = datasource.parseQBE({ orgid: '=' + this.app.client.userInfo.defaultOrg });
    query.qbe = { ...query.qbe, ...mine };
  }
  // warn when the estimated duration is cleared
  onValueChanged({ datasource, field, newValue }) {
    if (datasource.name === 'dsCreateWo' && field === 'estdur' && !newValue) {
      this.app.toast('Estimated duration is empty', 'warning');
    }
  }
}
export default AppCustomizations;
