# SettlementIQ — Documented Project Assumptions

1. **Amount Tolerance (`R2_TOLERANCE = ±₹1.00 INR`)**: Project assumption for INR minor rounding variances only.
2. **SLA Timing Window (`R4_TIMING = 2 Business Days`)**: Monday–Friday business calendar (`ISODOW 1..5`).
3. **GST Rate (`18.00%`)**: Applied to contracted MDR + fixed gateway fee.
4. **Exposure vs. Loss**: Only `OPEN` (`680`) and `REOPENED` (`25`) exceptions contribute to `₹37,52,510.63` unresolved exposure; `RESOLVED` (`95`) have `₹0.00` unresolved exposure; `₹1,26,151.24` confirmed loss is restricted to 15 evidenced write-offs.
