# RBI calculation core, structured after API RP 581 (3rd edition) Part 1 and Part 2.
# Pure functions only: this text is embedded in the RBI.CALC automation script (Jython 2.7)
# and imported by the test harness (CPython 3), so keep it compatible with both.
import math

# ---- Standard constants -------------------------------------------------------------------------------
# Values follow API RP 581 3rd edition (Part 2, thinning model; Part 1, risk categories).
# VERIFY them against your licensed copy of API RP 581 before production use and keep them under change control.
DS = (1.0, 2.0, 4.0)                       # damage state factors: rate as measured, 2x, 4x
COV_DT, COV_SF, COV_P = 0.20, 0.20, 0.05   # coefficients of variation: thinning, flow stress, pressure
PRIOR = {"LOW": (0.5, 0.3, 0.2), "MEDIUM": (0.7, 0.2, 0.1), "HIGH": (0.8, 0.15, 0.05)}
COND = {"A": (0.9, 0.09, 0.01), "B": (0.7, 0.2, 0.1), "C": (0.5, 0.3, 0.2), "D": (0.4, 0.33, 0.27)}
NORM = 1.56e-4                             # thinning damage factor normalisation
POF_DF = (1.0, 10.0, 100.0, 1000.0)        # PoF category 1..5 upper limits on the damage factor
COF_FIN = (1e4, 1e5, 1e6, 1e7)             # CoF category A..E upper limits, financial (USD)
COF_AREA = (9.29, 92.9, 929.0, 9290.0)     # CoF category A..E upper limits, consequence area (m2) = 100..100000 ft2

# ---- Screening values (company-configurable, not API tables) ------------------------------------------
# API RP 581 gives mechanism-specific base damage factor tables for cracking, HTHA and fatigue.
# These screening values stand in for them until you load the licensed tables.
SVI = {"HIGH": 50.0, "MEDIUM": 10.0, "LOW": 1.0}           # SCC severity index by susceptibility
BASE_OTHER = {"HIGH": 500.0, "MEDIUM": 50.0, "LOW": 5.0}   # HTHA / mechanical fatigue base damage factor
CREDIT = {"A": 0.1, "B": 0.25, "C": 0.5, "D": 0.8}          # factor per past inspection, by effectiveness
MAX_INTERVAL = 10.0                                          # years, absolute cap on an inspection interval
RISK_LEVEL = ((4, "LOW"), (6, "MEDIUM"), (7, "MEDHIGH"), (10, "HIGH"))  # matrix score = PoF cat + CoF index

def _erf(x):
    # Abramowitz-Stegun 7.1.26, |error| < 1.5e-7; used when math.erf is missing (older Jython)
    t = 1.0 / (1.0 + 0.3275911 * abs(x))
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * math.exp(-x * x)
    return y if x >= 0 else -y

def phi(x):
    """Standard normal cumulative distribution."""
    erf = getattr(math, "erf", _erf)
    return 0.5 * (1.0 + erf(x / math.sqrt(2.0)))

def posterior(conf, counts):
    """Bayesian update of the damage-state priors with the inspections done (counts = dict A..D -> n)."""
    pr = PRIOR.get(conf, PRIOR["LOW"])
    w = []
    for i in range(3):
        v = pr[i]
        for k in ("A", "B", "C", "D"):
            v *= COND[k][i] ** counts.get(k, 0)
        w.append(v)
    s = sum(w)
    return [x / s for x in w]

def strength_ratio(t_rdi, tmin, s_allow, joint, ys, ts):
    """SR = (S*E / FS) * tmin / t_rdi with flow stress FS = (YS+TS)/2 * E * 1.1."""
    fs = (ys + ts) / 2.0 * joint * 1.1
    return (s_allow * joint / fs) * (tmin / t_rdi)

def df_thinning(cr, age, t_rdi, sr, conf, counts):
    """Thinning damage factor: probability of failure over the three damage states, normalised."""
    if cr <= 0 or t_rdi <= 0:
        return 0.0, 0.0
    art = cr * age / t_rdi
    post = posterior(conf, counts)
    p = 0.0
    for i in range(3):
        d = DS[i]
        num = 1.0 - d * art - sr
        den = math.sqrt((d * art * COV_DT) ** 2 + ((1.0 - d * art) * COV_SF) ** 2 + (sr * COV_P) ** 2)
        p += post[i] * phi(-num / den)
    return max(p / NORM, 0.1), art

def df_scc(susc, age, counts):
    """Cracking: base from the severity index, reduced by inspections, grown with age^1.1."""
    base = SVI.get(susc, 0.0)
    for k, n in counts.items():
        base *= CREDIT.get(k, 1.0) ** n
    return base * max(age, 1.0) ** 1.1

def df_other(susc, counts):
    base = BASE_OTHER.get(susc, 0.0)
    for k, n in counts.items():
        base *= CREDIT.get(k, 1.0) ** n
    return base

def pof_category(df):
    for i, lim in enumerate(POF_DF):
        if df <= lim:
            return i + 1
    return 5

def cof_category(value, limits):
    for i, lim in enumerate(limits):
        if value <= lim:
            return "ABCDE"[i]
    return "E"

def risk_level(pofcat, cofcat):
    score = pofcat + "ABCDE".index(cofcat) + 1
    for lim, lvl in RISK_LEVEL:
        if score <= lim:
            return lvl
    return "HIGH"

def fms(score):
    """Management systems factor from the management systems evaluation score (0-1000)."""
    return 10.0 ** (-0.02 * (score / 10.0) + 1.0)

def total_df(eq, mechs, age_rd, extra=None):
    """Damage factors at a time point.
    eq: dict(cr, t_rdi, sr, conf, counts) for internal thinning; age_rd = years since the thickness reading.
    mechs: list of dict(mech, susc, cr, age, counts); their 'age' is already measured to the same time point.
    extra: (mechanism, effectiveness) -> one more inspection credited to that mechanism (mitigation case).
    Combination rule (general thinning): max(internal, external/CUI) + cracking + HTHA + fatigue."""
    def cnt(c, mech):
        c = dict(c)
        if extra and extra[0] == mech:
            c[extra[1]] = c.get(extra[1], 0) + 1
        return c
    d_thin, art = df_thinning(eq["cr"], age_rd, eq["t_rdi"], eq["sr"], eq["conf"], cnt(eq["counts"], "THINNING"))
    rows, d_ext, d_scc, d_oth = [], 0.0, 0.0, 0.0
    for m in mechs:
        c = cnt(m["counts"], m["mech"])
        if m["mech"] in ("EXTCORR", "CUI"):
            d = df_thinning(m["cr"], m["age"], eq["t_rdi"], eq["sr"], "LOW", c)[0]
            d_ext = max(d_ext, d)
        elif m["mech"] == "SCC":
            d = df_scc(m["susc"], m["age"], c)
            d_scc = max(d_scc, d)
        else:
            d = df_other(m["susc"], c)
            d_oth += d
        rows.append(d)
    total = max(d_thin, d_ext) + d_scc + d_oth
    return dict(thin=d_thin, art=art, ext=d_ext, scc=d_scc, other=d_oth, total=total, rows=rows)

def plan(eq, mechs, age_rd0, gff, fmsv, fc, target, plan_years, rl, since_insp):
    """Risk-target inspection planning on a monthly grid from the RBI date (t=0) to the plan date and beyond.
    mechs carry age0 (their age at the RBI date). rl = remaining life at the RBI date (years);
    since_insp = years from the last inspection to the RBI date.
    Returns the inspection due time (years from the RBI date), what governs it, and the damage factors."""
    def at(t, extra=None):
        ms = [dict(m, age=m["age0"] + t) for m in mechs]
        return total_df(eq, ms, age_rd0 + t, extra)
    def risk(t, extra=None):
        return gff * fmsv * at(t, extra)["total"] * fc
    t_target, t = None, 0.0
    while t <= 15.0:
        if risk(t) > target:
            t_target = t
            break
        t += 1.0 / 12.0
    cands = [(MAX_INTERVAL - since_insp, "maximum interval of %.0f y" % MAX_INTERVAL),
             (rl / 2.0, "half the remaining life (API 510/570)")]
    if t_target is not None:
        cands.append((t_target, "risk target reached"))
    due, why = sorted(cands, key=lambda c: c[0])[0]
    due = max(due, 0.0)
    now, end = at(0.0), at(plan_years)
    drivers = [("THINNING", end["thin"])] + [(m["mech"], d) for m, d in zip(mechs, end["rows"])]
    driver = sorted(drivers, key=lambda x: -x[1])[0][0]
    need, mit = "A", None
    for eff in ("D", "C", "B", "A"):
        r = risk(plan_years, (driver, eff))
        if r <= target:
            need, mit = eff, r
            break
    if mit is None:
        mit = risk(plan_years, (driver, "A"))
    return dict(now=now, end=end, risk_now=risk(0.0), risk_plan=risk(plan_years), t_target=t_target, due=due,
                why=why, driver=driver, need=need, risk_mit=mit)
