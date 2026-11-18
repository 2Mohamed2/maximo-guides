# Read-only SQL for the Maximo Assistant (MCP tool script_runsqlquery).
# Input : query  - one SELECT (or WITH ... SELECT) statement
# Output: responseBody - JSON {columns, rows, rowcount, truncated} or {error}
from psdi.server import MXServer
from com.ibm.json.java import JSONObject, JSONArray, OrderedJSONObject
from java.lang import Exception as JavaException
from java.util.regex import Pattern

MAXROWS = 200
MAXCELL = 500
BLOCKED = r"\b(insert|update|delete|merge|drop|alter|create|truncate|grant|revoke|call|rename|comment|lock|refresh|reorg|runstats|export|import|load)\b"
SENSITIVE = ("password", "apikey", "apikeytoken", "maxusrdbauthinfo", "encryptedvalue", "cryptokey")

def answer(obj):
    return obj.serialize(True)

def fail(msg):
    o = OrderedJSONObject()
    o.put("error", msg)
    return answer(o)

def run(sql, userInfo):
    mx = MXServer.getMXServer()
    profile = mx.lookup("SECURITY").getProfile(userInfo)
    if not profile.hasAppOption("AUTOSCRIPT", "READ"):
        return fail("Not authorized: running SQL from the assistant needs read access to the Automation Scripts application.")
    if sql is None:
        sql = ""
    sql = (u"%s" % sql).strip()
    while sql.endswith(";"):
        sql = sql[:-1].strip()
    low = sql.lower()
    if low == "":
        return fail("No SQL statement was given.")
    if not (low.startswith("select") or low.startswith("with")):
        return fail("Only SELECT statements can be run.")
    if ";" in sql or "--" in sql or "/*" in sql:
        return fail("Only one statement without comments can be run.")
    if Pattern.compile(BLOCKED).matcher(low).find():
        return fail("The statement contains a keyword that changes data or structure; only read-only SELECT is allowed.")
    for word in SENSITIVE:
        if word in low:
            return fail("The statement touches credential data (" + word + "), which this tool does not return.")
    key = userInfo.getConnectionKey()
    con = mx.getDBManager().getConnection(key)
    st = None
    rs = None
    try:
        st = con.createStatement()
        st.setMaxRows(MAXROWS + 1)
        st.setQueryTimeout(60)
        rs = st.executeQuery(sql)
        md = rs.getMetaData()
        n = md.getColumnCount()
        names = []
        cols = JSONArray()
        for i in range(1, n + 1):
            nm = md.getColumnLabel(i)
            names.append(nm)
            cols.add(nm)
        rows = JSONArray()
        count = 0
        truncated = False
        while rs.next():
            if count >= MAXROWS:
                truncated = True
                break
            r = OrderedJSONObject()
            for i in range(n):
                v = rs.getString(i + 1)
                if v is not None and len(v) > MAXCELL:
                    v = v[:MAXCELL] + "..."
                r.put(names[i], v)
            rows.add(r)
            count = count + 1
        out = OrderedJSONObject()
        out.put("rowcount", count)
        out.put("truncated", truncated)
        out.put("columns", cols)
        out.put("rows", rows)
        if truncated:
            out.put("note", "Only the first " + str(MAXROWS) + " rows are returned. Add a filter or FETCH FIRST n ROWS ONLY.")
        return answer(out)
    except JavaException, e:
        return fail("SQL error: " + str(e.getMessage()))
    except Exception, e:
        return fail("Error: " + str(e))
    finally:
        try:
            if rs is not None:
                rs.close()
        except:
            pass
        try:
            if st is not None:
                st.close()
        except:
            pass
        mx.getDBManager().freeConnection(key)

responseBody = run(query, userInfo)
