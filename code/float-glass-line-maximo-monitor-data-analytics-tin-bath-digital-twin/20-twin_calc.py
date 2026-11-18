"""The tin bath twin's expectations (FG-L1-TB, Float Line 1, 600 t/day).

One definition, two outputs:
  monitor_expressions(twin) -> pandas expressions for Maximo Monitor PythonExpression functions
  evaluate(twin, reading)   -> the same numbers in Python (3D twin, tests)

Atmosphere (sealed bath, steady state):
  O2_expected   = c_N2 * N2 / (N2 + H2)                    c_N2 = N2 supply spec (2 ppm)
  air ingress   = (O2 - O2_expected) * (N2 + H2) / 209,000  Nm3/h -> L/min (x 1000/60), if all excess O2 is air
  P_expected    = P_design * (N2 + H2) / (N2_design + H2_design)
  A leak raises O2 AND lowers the pressure AND wets the gas; a contaminated N2 supply raises O2 only.
Ribbon mass balance:
  glass carried (t/day) = speed (m/min) x width (m) x thickness (mm) x density (t/m3) x 1.44
  mass gap %            = weigher / glass carried - 1
"""


def _k(twin):
    a, r = twin["design"]["atmosphere"], twin["design"]["ribbon"]
    return dict(c=a["n2_supply_o2_spec_ppm"], air=a["air_o2_ppm"], p0=a["design_pressure_pa"],
                q0=a["n2_design_nm3h"] + a["h2_design_nm3h"], rho=r["density_t_m3"], dp0=a["dew_point_design_c"])


def _parts(twin):
    k = _k(twin)
    Q = "(df['N2_FLOW_NM3H'] + df['H2_FLOW_NM3H']).clip(lower=1)"
    O2E = f"({k['c']} * df['N2_FLOW_NM3H'] / {Q})"
    EX = f"(df['ATM_O2_PPM'] - {O2E})"
    AIR = f"({EX} * {Q} / {k['air']} * 1000 / 60).clip(lower=0)"
    PE = f"({k['p0']} * {Q} / {k['q0']})"
    PD = f"({PE} - df['BATH_PRESSURE_PA'])"
    RT = f"(df['RIBBON_SPEED_M_MIN'] * df['RIBBON_WIDTH_M'] * df['THICKNESS_MM'] * {k['rho']} * 1.44)"
    GAP = f"(100 * (df['WEIGHER_TPD'] / {RT}.clip(lower=1) - 1))"
    return dict(Q=Q, O2E=O2E, EX=EX, AIR=AIR, PE=PE, PD=PD, RT=RT, GAP=GAP, k=k)


def monitor_expressions(twin):
    p = _parts(twin)
    return [
        ("O2_EXPECTED_PPM", f"{p['O2E']}.round(2)"),
        ("O2_EXCESS_PPM", f"{p['EX']}.round(2)"),
        ("AIR_INGRESS_LPM", f"{p['AIR']}.round(2)"),
        ("PRESSURE_EXPECTED_PA", f"{p['PE']}.round(1)"),
        ("PRESSURE_DEFICIT_PA", f"{p['PD']}.round(1)"),
        ("RIBBON_TPD", f"{p['RT']}.round(1)"),
        ("MASS_GAP_PCT", f"{p['GAP']}.round(2)"),
    ]


def evaluate(twin, r):
    k = _k(twin)
    q = max(r["n2_flow_nm3h"] + r["h2_flow_nm3h"], 1)
    o2e = k["c"] * r["n2_flow_nm3h"] / q
    ex = r["atm_o2_ppm"] - o2e
    pe = k["p0"] * q / k["q0"]
    rt = r["ribbon_speed_m_min"] * r["ribbon_width_m"] * r["thickness_mm"] * k["rho"] * 1.44
    return {"o2_expected_ppm": o2e, "o2_excess_ppm": ex, "air_ingress_lpm": max(0.0, ex * q / k["air"] * 1000 / 60),
            "pressure_expected_pa": pe, "pressure_deficit_pa": pe - r["bath_pressure_pa"],
            "ribbon_tpd": rt, "mass_gap_pct": 100 * (r["weigher_tpd"] / max(rt, 1) - 1),
            "dew_excess_c": r["dew_point_c"] - k["dp0"]}


def alert_rules(twin):
    L = twin["twin_model"]["limits"]
    p = _parts(twin)
    return [
        ("TB_SEAL_LEAK", f"({p['EX']} > {L['o2_excess_alert_ppm']}) & ({p['PD']} > {L['pressure_deficit_alert_pa']})", "High", "side_seal_leak"),
        ("TB_N2_SUPPLY_O2", f"({p['EX']} > {L['o2_excess_alert_ppm']}) & ({p['PD']} < {L['pressure_deficit_ok_pa']})", "High", "n2_supply_o2"),
        ("TB_MASS_BALANCE_GAP", f"{p['GAP']}.abs() > {L['mass_gap_alert_pct']}", "Medium", "weigher_drift"),
        ("TB_TIN_DEFECTS", f"df['TIN_DEFECTS_10M2'] > {L['tin_defects_alert']}", "Medium", None),
    ]


SEVERITY_PENALTY = {"Critical": 60, "High": 30, "Medium": 15, "Low": 5}


def conditions(twin, r, t):
    L = twin["twin_model"]["limits"]
    out = []

    def add(cond, name, sev, text, part, fm=None):
        if cond:
            out.append({"name": name, "severity": sev, "text": text, "part": part, "failure_mode": fm})
    ex, pd = t["o2_excess_ppm"], t["pressure_deficit_pa"]
    add(ex > L["o2_excess_alert_ppm"] and pd > L["pressure_deficit_alert_pa"], "TB_SEAL_LEAK", "High",
        f"Air getting in: {t['air_ingress_lpm']:.1f} L/min (O2 {r['atm_o2_ppm']:.1f} ppm vs {t['o2_expected_ppm']:.1f} sealed, "
        f"pressure {pd:.1f} Pa low, dew point {r['dew_point_c']:.0f} °C)", "seals", "side_seal_leak")
    add(ex > L["o2_excess_alert_ppm"] and pd < L["pressure_deficit_ok_pa"], "TB_N2_SUPPLY_O2", "High",
        f"O2 {r['atm_o2_ppm']:.1f} ppm with the pressure holding and dry gas: the N2 supply carries ~{r['atm_o2_ppm'] * 1.08:.0f} ppm O2",
        "gas", "n2_supply_o2")
    add(abs(t["mass_gap_pct"]) > L["mass_gap_alert_pct"], "TB_MASS_BALANCE_GAP", "Medium",
        f"Weigher {r['weigher_tpd']:.0f} t/day vs ribbon {t['ribbon_tpd']:.0f} t/day ({t['mass_gap_pct']:+.1f} %)", "ribbon", "weigher_drift")
    add(r["tin_defects_10m2"] > L["tin_defects_alert"], "TB_TIN_DEFECTS", "Medium",
        f"Tin defects {r['tin_defects_10m2']:.2f} per 10 m² at inspection", "ribbon")
    health = max(0, 100 - sum(SEVERITY_PENALTY[c["severity"]] for c in out))
    return out, health
