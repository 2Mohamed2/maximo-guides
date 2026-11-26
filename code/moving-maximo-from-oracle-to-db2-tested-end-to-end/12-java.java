// CvtTool - checks and fixes after a Maximo Oracle-to-DB2 move with Unlcvt + maxinst.
// Created by Mohamed Chihaoui.
//
//   java CvtTool.java counts   -> row count of every Maximo table on both sides (counts.csv)
//   java CvtTool.java blobs    -> copy BLOB bytes Unlcvt leaves out (images, BIRT resources,
//                                 geometry, report output)
//   java CvtTool.java empties  -> count '' values in text columns on DB2 (Oracle cannot store '')
//
// Connections come from environment variables:
//   SRC_URL SRC_USER SRC_PASS SRC_SCHEMA   (Oracle)
//   TGT_URL TGT_USER TGT_PASS TGT_SCHEMA   (DB2)
// Run with the Maximo JDBC drivers on the class path:
//   java -cp oraclethin.jar:db2jcc.jar CvtTool.java counts
import java.io.*;
import java.sql.*;
import java.util.*;

public class CvtTool {
    static String env(String k) { String v = System.getenv(k); if (v == null) throw new IllegalArgumentException(k + " not set"); return v; }
    static Connection src() throws SQLException { return DriverManager.getConnection(env("SRC_URL"), env("SRC_USER"), env("SRC_PASS")); }
    static Connection tgt() throws SQLException { return DriverManager.getConnection(env("TGT_URL"), env("TGT_USER"), env("TGT_PASS")); }

    public static void main(String[] a) throws Exception {
        String out = a.length > 1 ? a[1] : "/work/" + a[0] + ".csv";
        switch (a[0]) {
            case "counts" -> counts(out);
            case "blobs" -> blobs(out);
            case "empties" -> empties(out, a.length > 2 ? a[2] : "WORKORDER,ASSET,LOCATIONS,PERSON,LABOR,ITEM,INVENTORY,PO,POLINE,PR,TICKET,JOBPLAN,PM,MATUSETRANS,COMPANIES");
            default -> throw new IllegalArgumentException("counts | blobs | empties");
        }
    }

    // Persistent Maximo tables (not views), from the source data dictionary
    static List<String[]> tables(Connection s) throws SQLException {
        List<String[]> l = new ArrayList<>();
        try (ResultSet r = s.createStatement().executeQuery(
                "select t.tablename, t.uniquecolumnname from maxtable t join maxobject o on o.objectname = t.tablename "
                + "where o.persistent = 1 and o.isview = 0 order by 1")) {
            while (r.next()) l.add(new String[]{r.getString(1), r.getString(2)});
        }
        return l;
    }

    static long count(Connection c, String sql) {
        // close the statement too: Db2 runs out of JDBC packages (SQL0805N) otherwise
        try (Statement st = c.createStatement(); ResultSet r = st.executeQuery(sql)) { r.next(); return r.getLong(1); }
        catch (SQLException e) { return -1; }
    }

    static void counts(String out) throws Exception {
        try (Connection s = src(); Connection t = tgt(); PrintWriter w = new PrintWriter(out, "UTF-8")) {
            String ts = env("TGT_SCHEMA");
            w.println("table,oracle_rows,db2_rows,verdict");
            int same = 0, diff = 0;
            for (String[] tb : tables(s)) {
                long o = count(s, "select count(*) from " + tb[0]);
                long d = count(t, "select count(*) from " + ts + "." + tb[0]);
                String v = o == d ? "SAME" : (d < 0 ? "MISSING ON DB2" : "DIFFERENT");
                if (o == d) same++; else diff++;
                w.println(tb[0] + "," + o + "," + d + "," + v);
            }
            System.out.println("tables same=" + same + " different=" + diff + " -> " + out);
        }
    }

    // Tables whose ids maxinst renumbers: match on the record they belong to instead of the id.
    static final Map<String, String[]> MATCH_ON = Map.of("IMGLIB", new String[]{"REFOBJECT", "REFOBJECTID"});
    // Rebuilt by the Manage build on the new database: redeploy customised mobile apps, do not copy.
    static final Set<String> SKIP = Set.of("MAFAPPDATA");

    static void blobs(String out) throws Exception {
        try (Connection s = src(); Connection t = tgt(); PrintWriter w = new PrintWriter(out, "UTF-8")) {
            t.setAutoCommit(false);
            String ts = env("TGT_SCHEMA");
            Map<String, String> keyOf = new HashMap<>();
            for (String[] tb : tables(s)) keyOf.put(tb[0], tb[1]);
            List<String[]> cols = new ArrayList<>();
            try (Statement st = s.createStatement(); ResultSet r = st.executeQuery(
                    "select table_name, column_name from user_tab_columns where data_type = 'BLOB' order by 1, 2")) {
                while (r.next()) if (keyOf.containsKey(r.getString(1))) cols.add(new String[]{r.getString(1), r.getString(2)});
            }
            w.println("table,column,matched_on,rows_with_bytes,copied_to_db2,not_found_on_db2,bytes");
            for (String[] c : cols) {
                String tb = c[0], col = c[1];
                String[] match = MATCH_ON.getOrDefault(tb, new String[]{keyOf.get(tb)});
                String sel = String.join(", ", match), where = String.join(" = ? and ", match) + " = ?";
                int found = 0, upd = 0, miss = 0; long bytes = 0;
                try (Statement st = s.createStatement();
                     ResultSet r = st.executeQuery("select " + sel + ", " + col + " from " + tb
                         + " where " + col + " is not null and dbms_lob.getlength(" + col + ") > 0");
                     PreparedStatement u = t.prepareStatement("update " + ts + "." + tb + " set " + col + " = ? where " + where)) {
                    while (r.next()) {
                        found++;
                        if (SKIP.contains(tb)) continue;
                        byte[] b = r.getBytes(match.length + 1); bytes += b.length;
                        u.setBytes(1, b);
                        for (int i = 0; i < match.length; i++) u.setObject(i + 2, r.getObject(i + 1));
                        if (u.executeUpdate() >= 1) upd++; else miss++;
                    }
                }
                t.commit();
                if (found > 0) {
                    String note = SKIP.contains(tb) ? "SKIPPED (redeploy)" : String.join("+", match);
                    w.println(tb + "," + col + "," + note + "," + found + "," + upd + "," + miss + "," + bytes);
                    System.out.println(tb + "." + col + ": " + found + " with bytes, " + upd + " copied, " + miss + " not found [" + note + "]");
                }
            }
        }
    }

    static void empties(String out, String list) throws Exception {
        try (Connection t = tgt(); PrintWriter w = new PrintWriter(out, "UTF-8")) {
            String ts = env("TGT_SCHEMA");
            w.println("table,column,empty_string_rows");
            long total = 0; int checked = 0;
            for (String tb : list.split(",")) {
                List<String> cs = new ArrayList<>();
                try (PreparedStatement p = t.prepareStatement(
                        "select colname from syscat.columns where tabschema = ? and tabname = ? and typename in ('VARCHAR','CHARACTER')")) {
                    p.setString(1, ts); p.setString(2, tb);
                    try (ResultSet r = p.executeQuery()) { while (r.next()) cs.add(r.getString(1)); }
                }
                for (String c : cs) {
                    long n = count(t, "select count(*) from " + ts + "." + tb + " where " + c + " = ''");
                    checked++; total += Math.max(n, 0);
                    if (n != 0) w.println(tb + "," + c + "," + n);
                }
            }
            w.println("TOTAL," + checked + " columns," + total);
            System.out.println(checked + " text columns checked, " + total + " rows hold '' -> " + out);
        }
    }
}
