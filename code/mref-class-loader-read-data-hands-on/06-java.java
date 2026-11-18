/** The rows of a query result as JSON objects keyed by the labels we asked for. */
private static String rows(QueryResult r, DisplayLabel[] cols) {
    List<String> out = new ArrayList<>();
    QueryResponseHelper[] hs = r == null ? null : r.getQueryResponseHelpers();
    if (hs != null) {
        for (QueryResponseHelper h : hs) {
            StringBuilder o = new StringBuilder("{\"recordId\":").append(h.getRecordId());
            QueryResponseColumn[] cs = h.getQueryResponseColumns();
            for (int i = 0; cs != null && i < cs.length; i++) {
                String key = cs[i].getLabel() != null ? cs[i].getLabel() : cols[Math.min(i, cols.length - 1)].getLabel();
                String val = cs[i].getDisplayValue() != null ? cs[i].getDisplayValue() : cs[i].getValue();
                o.append(',').append(q(key)).append(':').append(q(val == null ? "" : val));
                // Numbers with a unit (area, cost) come back in the signed-in user's unit: pass the unit on.
                if (cs[i].getUom() != null && !cs[i].getUom().isBlank())
                    o.append(',').append(q(key + "Unit")).append(':').append(q(cs[i].getUom()));
            }
            out.add(o.append('}').toString());
        }
    }
    return "[" + String.join(",", out) + "]";
}
