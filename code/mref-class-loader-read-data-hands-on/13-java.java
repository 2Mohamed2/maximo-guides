/**
 * Floors of a building, each with its number of active spaces. Two queries filtered on the parent building's
 * name (a text field every location carries), counted here. getChildren is not used: inside a Class Loader its
 * answer came back as HTTP 401 "Login Failed." although the data had been read.
 */
private String floors(TririgaWS tws, String building) throws Exception {
    DisplayLabel[] fcols = {new DisplayLabel("triNameTX", "name", "General")};
    QueryResult fr = tws.runDynamicQuery(null, "Location", new String[]{"triFloor"}, null, null, null,
        COMPANY, fcols, null, null, new Filter[]{filter("triParentBuildingTX", building)}, null, 1, 500);
    DisplayLabel[] scols = {new DisplayLabel("triParentFloorTX", "floor", "General")};
    Map<String, Integer> perFloor = new HashMap<>();
    QueryResult sr = tws.runDynamicQuery(null, "Location", new String[]{"triSpace"}, null, null, null,
        COMPANY, scols, null, null, new Filter[]{filter("triParentBuildingTX", building), filter("triStatusCL", "Active")}, null, 1, 1000);
    while (sr != null && sr.getQueryResponseHelpers() != null && sr.getQueryResponseHelpers().length > 0) {
        for (QueryResponseHelper h : sr.getQueryResponseHelpers()) {
            QueryResponseColumn[] cs = h.getQueryResponseColumns();
            String f = cs == null || cs.length == 0 ? "" : cs[0].getDisplayValue();
            perFloor.merge(f == null ? "" : f, 1, Integer::sum);
        }
        if (sr.getContinuationToken() == null) break;
        sr = tws.runDynamicQueryContinue(sr.getContinuationToken());
    }
    List<String> out = new ArrayList<>();
    QueryResponseHelper[] hs = fr == null ? null : fr.getQueryResponseHelpers();
    if (hs != null) {
        for (QueryResponseHelper h : hs) {
            QueryResponseColumn[] cs = h.getQueryResponseColumns();
            String name = cs == null || cs.length == 0 ? "" : cs[0].getDisplayValue();
            out.add("{\"recordId\":" + h.getRecordId() + ",\"name\":" + q(name == null ? "" : name)
                + ",\"spaces\":" + perFloor.getOrDefault(name, 0) + "}");
        }
    }
    return "{\"total\":" + (fr == null ? 0 : fr.getTotalResults()) + ",\"rows\":[" + String.join(",", out) + "]}";
}
