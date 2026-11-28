// CvtTool - checks and fixes after a Maximo Oracle-to-DB2 move with Unlcvt + maxinst.
// Created by Mohamed Chihaoui.
//
//   java CvtTool.java counts   -> row count of every Maximo table on both sides (counts.csv)
//   java CvtTool.java blobs    -> copy the binary values Unlcvt leaves out (images, BIRT resources,
//                                 geometry, report output, encrypted fields); source Oracle or SQL Server
//   java CvtTool.java empties  -> count '' values in text columns on Db2 (and on a SQL Server source)
//   java CvtTool.java restore out.csv T1,T2 -> replace the Db2 rows of these tables with the source rows.
//                                 maxinst runs IBM's VCATCHUPMAXINST.dbc, which deletes the Assistant tool
//                                 definitions (MAXINTOBJTOOL) of four object structures and every MAXAICFGRAG row,
//                                 and reinserts IBM's defaults: customised or added tools are lost without it.
//
// Connections come from environment variables:
//   SRC_URL SRC_USER SRC_PASS SRC_SCHEMA   (Oracle or SQL Server)
//   TGT_URL TGT_USER TGT_PASS TGT_SCHEMA   (DB2)
// Run with the Maximo JDBC drivers on the class path:
//   java -cp oraclethin.jar:sqljdbc.jar:db2jcc.jar CvtTool.java counts
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
            case "restore" -> restore(out, a.length > 2 ? a[2] : "MAXINTOBJTOOL,MAXINTOBJTOOLPARAM,MAXAICFGRAG");
            default -> throw new IllegalArgumentException("counts | blobs | empties | restore");
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
        // views can be large joins: give each count 60 s (-2 = timed out)
        try (Statement st = c.createStatement()) {
            st.setQueryTimeout(60);
            try (ResultSet r = st.executeQuery(sql)) { r.next(); return r.getLong(1); }
        } catch (SQLTimeoutException e) { return -2; }
        catch (SQLException e) { return e.getMessage() != null && e.getMessage().toLowerCase().contains("timeout") ? -2 : -1; }
    }

    // Row counts of every persistent table, then of every Maximo view: a view can return other rows on Db2
    // even when its tables match (SQL Server joins text without regard to case, Db2 does not).
    static void counts(String out) throws Exception {
        try (Connection s = src(); Connection t = tgt(); PrintWriter w = new PrintWriter(out, "UTF-8")) {
            String ts = env("TGT_SCHEMA");
            w.println("object,kind,source_rows,db2_rows,verdict");
            int same = 0, diff = 0, vsame = 0, vdiff = 0;
            for (String[] tb : tables(s)) {
                long o = count(s, "select count(*) from " + tb[0]);
                long d = count(t, "select count(*) from " + ts + "." + tb[0]);
                String v = o == d ? "SAME" : (d < 0 ? "MISSING ON DB2" : "DIFFERENT");
                if (o == d) same++; else diff++;
                w.println(tb[0] + ",table," + o + "," + d + "," + v);
            }
            List<String> views = new ArrayList<>();
            try (Statement st = s.createStatement(); ResultSet r = st.executeQuery(
                    "select viewname from maxview where viewname in (select objectname from maxobject where isview = 1) order by 1")) {
                while (r.next()) views.add(r.getString(1));
            }
            for (String vw : views) {
                long o = count(s, "select count(*) from " + vw);
                long d = count(t, "select count(*) from " + ts + "." + vw);
                if (o == -1 && d == -1) continue;
                String v = (o == -2 || d == -2) ? "TIMEOUT" : o == d ? "SAME" : (d < 0 ? "ERROR ON DB2" : o < 0 ? "ERROR ON SOURCE" : "DIFFERENT");
                if (o == d) vsame++; else vdiff++;
                w.println(vw + ",view," + o + "," + d + "," + v);
            }
            System.out.println("tables same=" + same + " different=" + diff + "; views same=" + vsame + " different=" + vdiff + " -> " + out);
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
            // binary columns of the source: Oracle BLOB / RAW (encrypted CRYPTO fields), SQL Server varbinary / image
            boolean ora = s.getMetaData().getDatabaseProductName().toLowerCase().contains("oracle");
            String colSql = ora
                ? "select table_name, column_name, data_type from user_tab_columns where data_type in ('BLOB','RAW','LONG RAW') order by 1, 2"
                : "select upper(table_name), upper(column_name), data_type from information_schema.columns "
                  + "where data_type in ('varbinary','image','binary') order by 1, 2";
            List<String[]> cols = new ArrayList<>();
            try (Statement st = s.createStatement(); ResultSet r = st.executeQuery(colSql)) {
                while (r.next()) if (keyOf.containsKey(r.getString(1))) cols.add(new String[]{r.getString(1), r.getString(2), r.getString(3)});
            }
            w.println("table,column,matched_on,rows_with_bytes,copied_to_db2,not_found_on_db2,bytes,source_type");
            for (String[] c : cols) {
                String tb = c[0], col = c[1];
                String[] match = MATCH_ON.getOrDefault(tb, new String[]{keyOf.get(tb)});
                String sel = String.join(", ", match), where = String.join(" = ? and ", match) + " = ?";
                int found = 0, upd = 0, miss = 0; long bytes = 0;
                try (Statement st = s.createStatement();
                     ResultSet r = st.executeQuery("select " + sel + ", " + col + " from " + tb + " where " + col + " is not null"
                         + (ora ? (c[2].equals("BLOB") ? " and dbms_lob.getlength(" + col + ") > 0" : "") : " and datalength(" + col + ") > 0"));
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
                    w.println(tb + "," + col + "," + note + "," + found + "," + upd + "," + miss + "," + bytes + "," + c[2]);
                    System.out.println(tb + "." + col + ": " + found + " with bytes, " + upd + " copied, " + miss + " not found [" + note + "]");
                }
            }
        }
    }

    // Counts '' in the text columns of the listed tables on Db2, and on the source when it is SQL Server
    // (Oracle cannot store ''; SQL Server can, so there the two counts must match).
    static void empties(String out, String list) throws Exception {
        try (Connection s = src(); Connection t = tgt(); PrintWriter w = new PrintWriter(out, "UTF-8")) {
            String ts = env("TGT_SCHEMA"), ss = env("SRC_SCHEMA");
            boolean ora = s.getMetaData().getDatabaseProductName().toLowerCase().contains("oracle");
            w.println("table,column,source_rows,db2_rows");
            long total = 0, totalSrc = 0; int checked = 0, differ = 0;
            for (String tb : list.split(",")) {
                List<String> cs = new ArrayList<>();
                try (PreparedStatement p = t.prepareStatement(
                        "select colname from syscat.columns where tabschema = ? and tabname = ? and typename in ('VARCHAR','CHARACTER')")) {
                    p.setString(1, ts); p.setString(2, tb);
                    try (ResultSet r = p.executeQuery()) { while (r.next()) cs.add(r.getString(1)); }
                }
                for (String c : cs) {
                    long n = count(t, "select count(*) from " + ts + "." + tb + " where " + c + " = ''");
                    long m = ora ? 0 : count(s, "select count(*) from " + ss + "." + tb + " where " + c + " = ''");
                    checked++; total += Math.max(n, 0); totalSrc += Math.max(m, 0);
                    if (n != m) differ++;
                    if (n != 0 || m != 0) w.println(tb + "," + c + "," + m + "," + n);
                }
            }
            w.println("TOTAL," + checked + " columns," + totalSrc + "," + total);
            System.out.println(checked + " text columns checked; rows holding '': source " + totalSrc + ", Db2 " + total
                + "; columns that differ: " + differ + " -> " + out);
        }
    }

    // Replace the target rows of whole tables with the source rows (same ids, rowstamp from MAXSEQ).
    static void restore(String out, String list) throws Exception {
        try (Connection s = src(); Connection t = tgt(); PrintWriter w = new PrintWriter(out, "UTF-8")) {
            t.setAutoCommit(false);
            String ts = env("TGT_SCHEMA"), ss = env("SRC_SCHEMA");
            w.println("table,db2_rows_before,source_rows,inserted");
            for (String tb : list.split(",")) {
                long before = count(t, "select count(*) from " + ts + "." + tb);
                long srcRows = count(s, "select count(*) from " + ss + "." + tb);
                if (srcRows < 0 || before < 0) { w.println(tb + ",missing,missing,0"); continue; }
                int ins = 0;
                try (Statement st = t.createStatement()) { st.executeUpdate("delete from " + ts + "." + tb); }
                try (Statement q = s.createStatement(); ResultSet r = q.executeQuery("select * from " + ss + "." + tb)) {
                    ResultSetMetaData m = r.getMetaData();
                    StringBuilder names = new StringBuilder(), marks = new StringBuilder();
                    List<Integer> idx = new ArrayList<>();
                    for (int i = 1; i <= m.getColumnCount(); i++) {
                        String n = m.getColumnName(i).toUpperCase();
                        if (names.length() > 0) { names.append(','); marks.append(','); }
                        names.append(n);
                        if (n.equals("ROWSTAMP")) marks.append("NEXTVAL FOR " + ts + ".MAXSEQ");
                        else { marks.append('?'); idx.add(i); }
                    }
                    try (PreparedStatement p = t.prepareStatement("insert into " + ts + "." + tb + " (" + names + ") values (" + marks + ")")) {
                        while (r.next()) {
                            int k = 1;
                            for (int i : idx) {
                                Object v = r.getObject(i);
                                if (v instanceof Blob b) v = b.getBytes(1, (int) b.length());
                                else if (v instanceof Clob c) v = c.getSubString(1, (int) c.length());
                                p.setObject(k++, v);
                            }
                            ins += p.executeUpdate();
                        }
                    }
                }
                t.commit();
                w.println(tb + "," + before + "," + srcRows + "," + ins);
                System.out.println(tb + ": Db2 had " + before + ", source " + srcRows + ", restored " + ins);
            }
        }
    }
}
