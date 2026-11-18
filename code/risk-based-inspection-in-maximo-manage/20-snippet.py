# ---- Maximo glue: read the assessment, run the model above, write the results ----------------------------
# Runs before every save of RBIASSESS (object launch point) and from Select Action > Recalculate Risk.
from psdi.mbo import MboConstants
from java.util import Date, Calendar

F = MboConstants.NOACCESSCHECK | MboConstants.NOVALIDATION_AND_NOACTION
YEAR_MS = 365.25 * 24 * 3600 * 1000.0
METHOD = {"THINNING": "UT thickness survey at all TMLs plus scanning of low points",
          "EXTCORR": "External visual inspection with spot UT at supports",
          "CUI": "Strip damaged insulation; profile RT or pulsed eddy current",
          "SCC": "Wet fluorescent MT or TOFD at welds and nozzles",
          "HTHA": "Phased-array UT and TOFD of welds for HTHA",
          "FATIGUE": "MT/PT at small-bore connections plus vibration survey"}

def years(d1, d2):
    return (d2.getTime() - d1.getTime()) / YEAR_MS

def add_years(d, y):
    cal = Calendar.getInstance()
    cal.setTime(d)
    cal.add(Calendar.DAY_OF_YEAR, int(round(y * 365.25)))
    return cal.getTime()

def setv(o, attr, val):
    if val is None:
        o.setValueNull(attr, F)
    else:
        o.setValue(attr, val, F)

def counts(o, attrs):
    return dict((k, o.getInt(a)) for k, a in zip(("A", "B", "C", "D"), attrs))

# Approved and superseded assessments are frozen records (API RP 580: the approved basis stays as approved).
# The calculation runs on drafts, and once more on the save that approves the assessment.
_st = mbo.getString("STATUS")
_frozen = _st == "SUPERSEDED" or (_st == "APPR" and not mbo.isModified("STATUS"))
if _frozen and launchPoint == "RBICALC":
    service.error("rbi", "frozen")

def _run():
    a = mbo
    if a.isNull("ASSESSDATE"):
        setv(a, "ASSESSDATE", Date())
    rbi = a.getDate("ASSESSDATE")
    if a.isNull("PLANDATE"):
        setv(a, "PLANDATE", add_years(rbi, 5.0))
    plan_y = max(years(rbi, a.getDate("PLANDATE")), 0.0)
    tnom = a.getDouble("TNOM")
    tmin = a.getDouble("TMIN")
    inst = a.getDate("INSTALLDATE")
    notes = []

    # 1. thickness history up to the RBI date, oldest first (gauge meter readings are MEASUREMENT rows)
    pts = []
    rs = a.getMboSet("$rbithk", "MEASUREMENT", "assetnum=:assetnum and siteid=:siteid and metername=:tmeter")
    rs.setOrderBy("measuredate")
    rs.reset()
    r = rs.moveFirst()
    while r is not None:
        d = r.getDate("MEASUREDATE")
        if d is not None and not r.isNull("MEASUREMENTVALUE") and not d.after(rbi):
            pts.append((d, r.getDouble("MEASUREMENTVALUE")))
        r = rs.moveNext()
    setv(a, "NUMREADINGS", len(pts))

    # 2. corrosion rates: long-term from nominal, short-term from the last two readings; the higher one governs
    crlt, crst = 0.0, 0.0
    if pts:
        dlast, tlast = pts[-1]
        if inst is not None and years(inst, dlast) > 0 and tnom > 0:
            crlt = (tnom - tlast) / years(inst, dlast)
        if len(pts) > 1 and years(pts[-2][0], dlast) > 0:
            crst = (pts[-2][1] - tlast) / years(pts[-2][0], dlast)
        setv(a, "TLAST", tlast)
        setv(a, "LASTREADDATE", dlast)
        if a.isNull("LASTINSPDATE"):
            setv(a, "LASTINSPDATE", dlast)
    else:
        dlast, tlast = (inst or rbi), tnom
        setv(a, "TLAST", None)
        setv(a, "LASTREADDATE", None)
        notes.append("No thickness readings: nominal thickness used.")
    cr = max(crlt, crst, 0.0)
    age_rd0 = max(years(dlast, rbi), 0.0)
    ttoday = tlast - cr * age_rd0
    rl = 99.0 if cr <= 0 else max(0.0, min(99.0, (ttoday - tmin) / cr))
    for k, v in (("CRLT", round(crlt, 3)), ("CRST", round(crst, 3)), ("CORRRATE", round(cr, 3)),
                 ("TTODAY", round(ttoday, 2)), ("REMLIFE", round(rl, 1))):
        setv(a, k, v)

    # 3. strength ratio from the design data (conservative S*E/FS = 1 when design data is missing)
    s_allow, ys, ts, joint = a.getDouble("ALLOWSTRESS"), a.getDouble("YIELDSTR"), a.getDouble("TENSILESTR"), a.getDouble("JOINTEFF") or 1.0
    if s_allow > 0 and ys > 0 and ts > 0 and tlast > 0:
        sr = strength_ratio(tlast, tmin, s_allow, joint, ys, ts)
    else:
        sr = tmin / tlast if tlast > 0 else 1.0
        notes.append("Design stresses missing: SR = tmin / t_rdi.")
    setv(a, "SR", round(sr, 3))

    # 4. damage mechanisms
    eq = dict(cr=cr, t_rdi=tlast, sr=sr, conf=a.getString("CRCONF") or "LOW",
              counts=counts(a, ("THINNA", "THINNB", "THINNC", "THINND")))
    mechs, rows = [], []
    dm = a.getMboSet("DAMAGE")
    d = dm.moveFirst()
    while d is not None:
        if not d.toBeDeleted():
            start = d.getDate("STARTDATE") or inst or rbi
            mechs.append(dict(mech=d.getString("MECHANISM"), susc=d.getString("SUSCEPT"), cr=d.getDouble("CORRRATE"),
                              age0=max(years(start, rbi), 0.0), counts=counts(d, ("NA", "NB", "NC", "ND"))))
            rows.append(d)
        d = dm.moveNext()

    # 5. probability, consequence, risk and the inspection plan
    gff = a.getDouble("GFF") or 3.06e-5
    fmsv = fms(a.getInt("MSSCORE"))
    fc = (a.getDouble("REPAIRCOST") + a.getDouble("AFFACOST") + a.getDouble("OUTAGEDAYS") * a.getDouble("LOSSPERDAY")
          + a.getDouble("INJCOST") + a.getDouble("ENVCOST"))
    target = a.getDouble("RISKTARGET") or 10000.0
    last_insp = a.getDate("LASTINSPDATE") or dlast
    p = plan(eq, mechs, age_rd0, gff, fmsv, fc, target, plan_y, rl, max(years(last_insp, rbi), 0.0))
    now, end = p["now"], p["end"]
    for row, dnow, dend in zip(rows, now["rows"], end["rows"]):
        setv(row, "DF", round(dnow, 1))
        setv(row, "DFPLAN", round(dend, 1))
        setv(row, "RECMETHOD", METHOD.get(row.getString("MECHANISM"), ""))
    pc_now, pc_end = pof_category(now["total"]), pof_category(end["total"])
    cfin, carea = cof_category(fc, COF_FIN), cof_category(a.getDouble("CONSAREA"), COF_AREA)
    cof = max(cfin, carea)
    for k, v in (("ART", round(now["art"], 4)), ("FMS", round(fmsv, 3)), ("DFTHIN", round(now["thin"], 1)),
                 ("DFEXT", round(now["ext"], 1)), ("DFSCC", round(now["scc"], 1)), ("DFOTHER", round(now["other"], 1)),
                 ("DFTOTAL", round(now["total"], 1)), ("POF", gff * fmsv * now["total"]), ("POFCATNOW", pc_now),
                 ("DFPLAN", round(end["total"], 1)), ("POFCAT", pc_end), ("COFCOST", round(fc, 2)), ("COFFIN", cfin),
                 ("COFAREA", carea), ("COFCAT", cof), ("FINRISK", round(p["risk_now"], 2)),
                 ("RISKCELLNOW", "%d%s" % (pc_now, cof)), ("FINRISKPLAN", round(p["risk_plan"], 2)),
                 ("RISKCELL", "%d%s" % (pc_end, cof)), ("RISK", risk_level(pc_end, cof)), ("DRIVER", p["driver"]),
                 ("INSPEFFREQ", p["need"]), ("FINRISKMIT", round(p["risk_mit"], 2)),
                 ("INSPMETHOD", (METHOD.get(p["driver"], "") + " (effectiveness %s or better)" % p["need"])[:100])):
        setv(a, k, v)
    setv(a, "TARGETDATE", add_years(rbi, p["t_target"]) if p["t_target"] is not None else None)
    nxt = add_years(rbi, p["due"])
    setv(a, "NEXTINSPDATE", nxt)
    setv(a, "INSPINTERVAL", round(max(years(last_insp, nxt), 0.0), 1))

    note = ("Thinning: Cr = max(LT %.3f, ST %.3f) = %.3f mm/y, t_rdi %.2f mm, Art %.4f, SR %.3f, confidence %s, "
            "remaining life %.1f y. Df now: thin %.1f, ext/CUI %.1f, cracking %.1f, HTHA/fatigue %.1f -> total %.1f "
            "(PoF cat %d); at plan date %.1f (cat %d). FMS %.3f, PoF %.2e /y. FC %.0f USD (%s), area %.0f m2 (%s) -> CoF %s. "
            "Risk %.0f USD/y now, %.0f at plan date vs target %.0f. Inspection due in %.1f y (%s); "
            "%s inspection of effectiveness %s brings plan-date risk to %.0f USD/y. %s"
            % (crlt, crst, cr, tlast, now["art"], sr, eq["conf"], rl, now["thin"], now["ext"], now["scc"], now["other"],
               now["total"], pc_now, end["total"], pc_end, fmsv, gff * fmsv * now["total"], fc, cfin,
               a.getDouble("CONSAREA"), carea, cof, p["risk_now"], p["risk_plan"], target, p["due"], p["why"],
               p["driver"], p["need"], p["risk_mit"], " ".join(notes)))
    setv(a, "CALCNOTE", note[:1000])

if not _frozen:
    _run()
