CALCS = [  # device type, output metric, expression
    ("FG_FURNACE", "SPEC_ENERGY", "(df['GAS_FLOW'] * 24 * 0.036 / df['PULL_RATE']).round(2)"),
    ("FG_LINE", "LOSS_TPD", "(df['PULL_RATE'] * (100 - df['YIELD']) / 100).round(1)"),
    # tin bath atmosphere twin: a sealed bath holds the O2 of its N2 supply (about 2 ppm), diluted by the H2;
    # anything above that is air getting in. Bath pressure follows the protective gas flow; a leak lets it fall.
    ("FG_TINBATH", "O2_EXPECTED", f"({TIN_O2_EXP}).round(2)"),
    ("FG_TINBATH", "AIR_INGRESS", f"(({TIN_O2_GAP}) * ({TIN_FLOW}) / 209000 * 1000 / 60).clip(lower=0).round(2)"),
    ("FG_TINBATH", "P_EXPECTED", f"(25 * ({TIN_FLOW}) / 1850).round(1)"),
    ("FG_TINBATH", "P_DEFICIT", f"(25 * ({TIN_FLOW}) / 1850 - df['BATH_PRESSURE']).round(1)"),
    # ribbon mass balance twin: glass carried by the ribbon (speed x width x thickness x density) against the weigher
    ("FG_RIBBON", "RIBBON_TPD", f"({RIBBON_TPD}).round(1)"),
    ("FG_RIBBON", "MASS_GAP", f"(100 * (df['WEIGHER_TPD'] / ({RIBBON_TPD}) - 1)).round(2)"),
]
