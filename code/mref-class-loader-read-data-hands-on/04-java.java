/** Active buildings: one dynamic query, filtered on the status, paged by the engine. */
private String buildings(TririgaWS tws) throws Exception {
    DisplayLabel[] cols = {
        new DisplayLabel("triIdTX", "id", "General"),
        new DisplayLabel("triNameTX", "name", "General"),
        new DisplayLabel("triCityTX", "city", "General"),
        new DisplayLabel("triPrimaryUseCL", "use", "General")};
    Filter[] where = {filter("triStatusCL", "Active")};
    QueryResult r = tws.runDynamicQuery(null, "Location", new String[]{"triBuilding"}, null, null, null,
        COMPANY, cols, null, null, where, null, 1, 500);
    return "{\"total\":" + r.getTotalResults() + ",\"rows\":" + rows(r, cols) + "}";
}
