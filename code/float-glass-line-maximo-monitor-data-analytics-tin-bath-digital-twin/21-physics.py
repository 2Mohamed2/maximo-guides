"""Physics of the FG-L1-TB tin bath and its ribbon: the stand-in for the real line (it sends only sensor values).

Per step (dt seconds):
  gas        N2 at design flow; H2 trimmed up by the operator when O2 rises (reducing margin)
  ingress    side seal leak: air in at up to 2.6 L/min; the opening lowers the over-pressure; air brings O2 and moisture
  supply     contaminated N2: the supply O2 rises from 2 ppm to ~20 ppm; pressure and dew point unchanged
  O2         first-order mixing toward (c_N2 * N2 + 209,000 * Q_air) / (N2 + H2 + Q_air), time constant ~3 min
  ribbon     600 t/day at 4 mm on a 3.8 m ribbon; speed follows from the mass balance; the weigher reads the batch
             (calibration drift adds up to +1.5 %)
  defects    tin defects follow the bath O2 with a few minutes' lag (oxidised tin picked up by the ribbon)
"""
import math
import random


class Fault:
    def __init__(self):
        self.sev, self.target, self.rate = 0.0, 0.0, 0.0

    def set(self, target, ramp_s):
        self.target = max(0.0, min(1.0, target))
        self.rate = abs(self.target - self.sev) / max(ramp_s, 1.0)

    def step(self, dt):
        if self.sev < self.target:
            self.sev = min(self.target, self.sev + self.rate * dt)
        elif self.sev > self.target:
            self.sev = max(self.target, self.sev - self.rate * dt)


class Plant:
    def __init__(self, twin, seed=601):
        self.twin, self.rng = twin, random.Random(seed)
        self.d = twin["design"]
        self.faults = {k: Fault() for k in twin["failure_modes"] if not k.startswith("$")}
        self.t = 0.0
        self.running, self.trip = True, 0
        a = self.d["atmosphere"]
        self.o2 = a["n2_supply_o2_spec_ppm"] * a["n2_design_nm3h"] / (a["n2_design_nm3h"] + a["h2_design_nm3h"])
        self.dew = a["dew_point_design_c"]
        self.tin = 0.05
        self.h2_trim = 0.0
        self.th = 4.0

    def set_fault(self, name, severity, ramp_s):
        self.faults[name].set(severity, ramp_s)

    def clear_faults(self, ramp_s=5):
        for f in self.faults.values():
            f.set(0.0, ramp_s)

    def reset(self):
        self.trip, self.running = 0, True

    def fault_state(self):
        return {k: round(v.sev, 3) for k, v in self.faults.items()}

    def _n(self, key, amp, period):
        """smooth noise, stable per key"""
        i, f = divmod(self.t / period, 1)
        a = random.Random(f"{key}{int(i)}").random() - .5
        b = random.Random(f"{key}{int(i) + 1}").random() - .5
        return 2 * amp * (a + (b - a) * (3 * f * f - 2 * f ** 3))

    def step(self, dt):
        self.t += dt
        for f in self.faults.values():
            f.step(dt)
        a, rb = self.d["atmosphere"], self.d["ribbon"]
        leak, sup, drift = (self.faults[k].sev for k in ("side_seal_leak", "n2_supply_o2", "weigher_drift"))
        n2 = a["n2_design_nm3h"] + self._n("n2", 12, 600)
        air_lpm = 2.6 * leak
        q_air = air_lpm * 60 / 1000
        c_n2 = a["n2_supply_o2_spec_ppm"] + 18.0 * sup
        # operator / controller trims H2 up as O2 rises (keeps the atmosphere reducing)
        target_trim = max(0.0, 2.4 * (self.o2 - 2.0))
        self.h2_trim += (target_trim - self.h2_trim) * min(1.0, dt / 240)
        h2 = a["h2_design_nm3h"] + self.h2_trim + self._n("h2", 1.5, 600)
        q = n2 + h2 + q_air
        o2_eq = (c_n2 * n2 + a["air_o2_ppm"] * q_air) / q
        self.o2 += (o2_eq - self.o2) * min(1.0, dt / 180)
        dew_eq = a["dew_point_design_c"] + 16.0 * math.sqrt(air_lpm)
        self.dew += (dew_eq - self.dew) * min(1.0, dt / 240)
        self.tin += ((0.05 + 0.034 * max(0.0, self.o2 - 2.0)) - self.tin) * min(1.0, dt / 300)
        p = a["design_pressure_pa"] * (n2 + h2) / (a["n2_design_nm3h"] + a["h2_design_nm3h"]) - 4.3 * air_lpm
        pull = rb["pull_tpd"] + self._n("pull", 5, 1800)
        width = rb["gross_width_m"] + self._n("w", 0.004, 300)
        speed = pull / (1.44 * rb["density_t_m3"] * self.th * width)
        return {"n2": n2, "h2": h2, "o2": self.o2, "h2pct": 100 * h2 / (n2 + h2), "dew": self.dew, "p": p,
                "lip": 1100 + self._n("lip", 2, 600), "entry": 1042 + self._n("ent", 3, 600), "exit": 612 + self._n("ext", 2.5, 600),
                "speed": speed, "width": width, "th": self.th, "weigher": pull * (1 + 0.015 * drift), "tin": self.tin}

    def measure(self, x):
        g = lambda v, s: v + self.rng.gauss(0, s)
        return {"n2_flow_nm3h": round(g(x["n2"], 3), 1), "h2_flow_nm3h": round(g(x["h2"], 0.5), 1),
                "atm_o2_ppm": round(max(0.1, g(x["o2"], 0.12)), 2), "atm_h2_pct": round(g(x["h2pct"], 0.03), 2),
                "dew_point_c": round(g(x["dew"], 0.25), 1), "bath_pressure_pa": round(g(x["p"], 0.2), 1),
                "lip_temp_c": round(g(x["lip"], 0.8), 1), "entry_temp_c": round(g(x["entry"], 0.8), 1), "exit_temp_c": round(g(x["exit"], 0.8), 1),
                "ribbon_speed_m_min": round(g(x["speed"], 0.005), 3), "ribbon_width_m": round(g(x["width"], 0.002), 3),
                "thickness_mm": round(g(x["th"], 0.008), 3), "thickness_sp_mm": x["th"],
                "weigher_tpd": round(g(x["weigher"], 1.0), 1), "tin_defects_10m2": round(max(0.0, g(x["tin"], 0.008)), 3)}
