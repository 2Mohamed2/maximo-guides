ALERTS = [  # device type, alert name, expression, severity
    ("FG_TINBATH", "TIN_O2_HIGH", "df['ATM_O2'] > 8", "High"),
    ("FG_TINBATH", "TIN_O2_ANOMALY", "df['O2_ANOMALY'] > 3", "Medium"),
    ("FG_FURNACE", "CROWN_TEMP_LOW", "df['CROWN_TEMP'] < 1575", "Medium"),
    ("FG_FURNACE", "GAS_PRESSURE_LOW", "df['GAS_PRESSURE'] < 260", "High"),
    ("FG_COLDEND", "TIN_DEFECTS_HIGH", "df['TIN_DEFECTS'] > 0.3", "Medium"),
    ("FG_COLDEND", "BUBBLES_HIGH", "df['BUBBLES'] > 0.5", "Medium"),
    ("FG_TINBATH", "TIN_AIR_INGRESS", f"({TIN_O2_GAP}) * ({TIN_FLOW}) / 209000 * 1000 / 60 > 1", "High"),
    ("FG_RIBBON", "MASS_BALANCE_GAP", f"(100 * (df['WEIGHER_TPD'] / ({RIBBON_TPD}) - 1)).abs() > 1", "Medium"),
    ("FG_LINE", "YIELD_LOW", "(df['YIELD'] < 82) & (df['STATE'] == 2)", "High"),
]
