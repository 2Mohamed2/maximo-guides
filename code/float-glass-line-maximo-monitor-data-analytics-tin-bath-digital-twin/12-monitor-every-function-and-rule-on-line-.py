SPEC_ENERGY  (FG_FURNACE, PythonExpression)
    (GAS_FLOW * 24 * 0.036 / PULL_RATE).round(2)

LOSS_TPD  (FG_LINE, PythonExpression)
    (PULL_RATE * (100 - YIELD) / 100).round(1)

O2_EXPECTED  (FG_TINBATH, PythonExpression)
    (2 * N2_FLOW / (N2_FLOW + H2_FLOW)).round(2)

AIR_INGRESS  (FG_TINBATH, PythonExpression)
    (
      (ATM_O2 - 2 * N2_FLOW / (N2_FLOW + H2_FLOW))
      * (N2_FLOW + H2_FLOW)
      / 209000
      * 1000
      / 60
    ).clip(lower=0).round(2)

P_EXPECTED  (FG_TINBATH, PythonExpression)
    (25 * (N2_FLOW + H2_FLOW) / 1850).round(1)

P_DEFICIT  (FG_TINBATH, PythonExpression)
    (25 * (N2_FLOW + H2_FLOW) / 1850 - BATH_PRESSURE).round(1)

RIBBON_TPD  (FG_RIBBON, PythonExpression)
    (RIBBON_SPEED * RIBBON_WIDTH * THICKNESS * 2.5 * 1.44).round(1)

MASS_GAP  (FG_RIBBON, PythonExpression)
    (
      100
      * (
          WEIGHER_TPD
          / (RIBBON_SPEED * RIBBON_WIDTH * THICKNESS * 2.5 * 1.44)
          - 1
        )
    ).round(2)

O2_ANOMALY  (FG_TINBATH, KMeansAnomalyScore)
    input ATM_O2, window 12 readings

TIN_O2_HIGH  (FG_TINBATH, AlertExpression, High)
    ATM_O2 > 8

TIN_O2_ANOMALY  (FG_TINBATH, AlertExpression, Medium)
    O2_ANOMALY > 3

CROWN_TEMP_LOW  (FG_FURNACE, AlertExpression, Medium)
    CROWN_TEMP < 1575

GAS_PRESSURE_LOW  (FG_FURNACE, AlertExpression, High)
    GAS_PRESSURE < 260

TIN_DEFECTS_HIGH  (FG_COLDEND, AlertExpression, Medium)
    TIN_DEFECTS > 0.3

BUBBLES_HIGH  (FG_COLDEND, AlertExpression, Medium)
    BUBBLES > 0.5

TIN_AIR_INGRESS  (FG_TINBATH, AlertExpression, High)
    (ATM_O2 - 2 * N2_FLOW / (N2_FLOW + H2_FLOW))
    * (N2_FLOW + H2_FLOW)
    / 209000
    * 1000
    / 60
    > 1

MASS_BALANCE_GAP  (FG_RIBBON, AlertExpression, Medium)
    (
      100
      * (
          WEIGHER_TPD
          / (RIBBON_SPEED * RIBBON_WIDTH * THICKNESS * 2.5 * 1.44)
          - 1
        )
    ).abs()
    > 1

YIELD_LOW  (FG_LINE, AlertExpression, High)
    (YIELD < 82) & (STATE == 2)
