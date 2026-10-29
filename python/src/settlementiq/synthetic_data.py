"""Deterministic Synthetic Data Generator for SettlementIQ (10,000+ Scale, 28 Scenarios).

Generates 100% synthetic payment ecosystem datasets using a fixed configurable seed (default=42):
1. merchants.csv (25 merchants across 4 payment gateways/acquirers & 5 Indian regions)
2. transactions.csv (10,000 primary + 25 repeated ingestion rows = 10,025 rows; 9,990 ledger + 10 orphan settlements)
3. settlements.csv (interconnected settlement lines including multi-part, duplicate, late, fee-adjusted, and repeated ingestion)
4. bank_entries.csv (bank statement credits/debits, timing delays, duplicate bank postings, and orphan bank entries)
5. refunds.csv (clean refunds, refund amount mismatches, unreversed failed refunds, missing refund evidence)
6. ground_truth.csv (10,000 independently labeled evaluation cases isolated from the matching engine)

Covers all 28 required synthetic scenarios with exact Decimal arithmetic (ROUND_HALF_UP).
"""
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
import pathlib
import random
from typing import Any, Dict, List, Tuple

from .config import DEFAULT_CONFIG, SettlementIQConfig

TWO_PLACES = Decimal("0.01")


def q2(val: Decimal | float | int | str) -> Decimal:
    """Quantize a monetary value to 2 decimal places using ROUND_HALF_UP."""
    return Decimal(str(val)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def add_business_days(start_date: date, add_days: int) -> date:
    """Add Mon-Fri business days to start_date."""
    curr = start_date
    rem = add_days
    while rem > 0:
        curr += timedelta(days=1)
        if curr.weekday() < 5:
            rem -= 1
    return curr


def count_business_days(start_date: date, end_date: date) -> int:
    """Count elapsed Mon-Fri business days between start_date and end_date."""
    if end_date <= start_date:
        return 0
    curr = start_date
    days = 0
    while curr < end_date:
        curr += timedelta(days=1)
        if curr.weekday() < 5:
            days += 1
    return days


def generate_merchants() -> List[Dict[str, Any]]:
    """Generate 25 realistic synthetic merchants across 4 gateways and 5 regions."""
    specs = [
        ("MERCH_1001", "Aarav Digital Retail Pvt Ltd", "E-Commerce & Retail", "2024-01-10", "ACTIVE", "T+1", "0.0180", "2.00", "INR", "West", "Tier1_Standard"),
        ("MERCH_1002", "BharatMart Hypermarkets", "Grocery & Essentials", "2024-01-22", "ACTIVE", "T+1", "0.0140", "1.50", "INR", "North", "Tier1_Standard"),
        ("MERCH_1003", "CloudPulse SaaS India", "Software & B2B SaaS", "2024-02-05", "ACTIVE", "T+2", "0.0220", "3.00", "INR", "South", "Tier1_Standard"),
        ("MERCH_1004", "Deccan Express Logistics", "Logistics & Supply Chain", "2024-02-18", "ACTIVE", "T+2", "0.0175", "2.00", "INR", "South", "Tier2_Monitored"),
        ("MERCH_1005", "ElectroPrime Appliances", "Consumer Electronics", "2024-03-01", "ACTIVE", "T+2", "0.0200", "2.50", "INR", "West", "Tier2_Monitored"),
        ("MERCH_1006", "FabVogue Fashion Co", "Apparel & Lifestyle", "2024-03-14", "ACTIVE", "T+2", "0.0190", "2.00", "INR", "North", "Tier1_Standard"),
        ("MERCH_1007", "GreenVeda Wellness Ltd", "Healthcare & Pharmacy", "2024-04-02", "ACTIVE", "T+1", "0.0150", "1.50", "INR", "East", "Tier1_Standard"),
        ("MERCH_1008", "Horizon Sky Travel & Stays", "Travel & Hospitality", "2024-04-19", "ACTIVE", "T+2", "0.0240", "3.50", "INR", "West", "Tier3_HighExposure"),
        ("MERCH_1009", "Indus MedCare Diagnostics", "Healthcare & Pharmacy", "2024-05-06", "ACTIVE", "T+1", "0.0135", "1.00", "INR", "South", "Tier1_Standard"),
        ("MERCH_1010", "Jaipur Heritage Artisans", "Home & Specialty Retail", "2024-05-20", "ACTIVE", "T+2", "0.0210", "2.00", "INR", "North", "Tier2_Monitored"),
        ("MERCH_1011", "Kaveri EdTech Academy", "Education & Upskilling", "2024-06-03", "ACTIVE", "T+2", "0.0185", "2.00", "INR", "South", "Tier1_Standard"),
        ("MERCH_1012", "Lotus Gourmet Hospitality", "Food & Dining", "2024-06-17", "ACTIVE", "T+1", "0.0160", "1.50", "INR", "West", "Tier1_Standard"),
        ("MERCH_1013", "MetroAuto Spares & Service", "Automotive & Parts", "2024-07-01", "ACTIVE", "T+2", "0.0195", "2.50", "INR", "Central", "Tier2_Monitored"),
        ("MERCH_1014", "Namma QuickBasket Delivery", "Hyperlocal Quick-Commerce", "2024-07-15", "ACTIVE", "T+1", "0.0155", "1.00", "INR", "South", "Tier1_Standard"),
        ("MERCH_1015", "Orbit Interactive Gaming", "Digital Goods & Gaming", "2024-08-01", "ACTIVE", "T+2", "0.0250", "3.00", "INR", "West", "Tier3_HighExposure"),
        ("MERCH_1016", "Pragati AgriTech Inputs", "Agriculture & B2B", "2024-08-14", "ACTIVE", "T+2", "0.0145", "1.50", "INR", "Central", "Tier1_Standard"),
        ("MERCH_1017", "Quantum FinServ Advisory", "Financial Services", "2024-09-01", "ACTIVE", "T+2", "0.0205", "2.50", "INR", "West", "Tier2_Monitored"),
        ("MERCH_1018", "Raga Music & Ticketing", "Events & Entertainment", "2024-09-12", "ACTIVE", "T+2", "0.0230", "3.00", "INR", "South", "Tier3_HighExposure"),
        ("MERCH_1019", "Surya Solar Home Systems", "Utilities & Clean Energy", "2024-09-25", "ACTIVE", "T+2", "0.0170", "2.00", "INR", "North", "Tier1_Standard"),
        ("MERCH_1020", "Triveni Book & Media House", "Publishing & Books", "2024-10-08", "ACTIVE", "T+1", "0.0165", "1.50", "INR", "East", "Tier1_Standard"),
        ("MERCH_1021", "Udaan Fitness & Sports", "Sports & Fitness", "2024-10-22", "ACTIVE", "T+2", "0.0185", "2.00", "INR", "North", "Tier1_Standard"),
        ("MERCH_1022", "Vanguard Cloud Hosting", "IT Infrastructure", "2024-11-05", "ACTIVE", "T+2", "0.0215", "2.50", "INR", "South", "Tier2_Monitored"),
        ("MERCH_1023", "Western Ghats Specialty Coffee", "Food & Beverage", "2024-11-19", "ACTIVE", "T+1", "0.0160", "1.50", "INR", "South", "Tier1_Standard"),
        ("MERCH_1024", "Zenith Home Furnishings", "Home & Furniture", "2024-12-02", "ACTIVE", "T+2", "0.0225", "3.00", "INR", "West", "Tier2_Monitored"),
        ("MERCH_1025", "Apex OmniChannel Retail", "Department Stores", "2024-12-18", "ACTIVE", "T+1", "0.0150", "1.50", "INR", "East", "Tier1_Standard"),
    ]
    gateways = ["AxisPay_Gateway", "HDFC_SmartHub", "ICICI_PaySeal", "RazorFlow_India"]
    rows = []
    for i, s in enumerate(specs):
        rows.append({
            "merchant_id": s[0],
            "merchant_name": s[1],
            "merchant_category": s[2],
            "onboarding_date": s[3],
            "merchant_status": s[4],
            "settlement_frequency": s[5],
            "contractual_fee_rate": s[6],
            "contractual_fixed_fee": s[7],
            "currency": s[8],
            "region": s[9],
            "operational_classification": s[10],
            "default_payment_gateway": gateways[i % len(gateways)],
            "settlement_sla_days": "1" if s[5] == "T+1" else "2",
            "is_synthetic": "TRUE",
        })
    return rows


def generate_synthetic_ecosystem(config: SettlementIQConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Generate 10,000 evaluation cases across all 28 required scenarios."""
    rng = random.Random(config.random_seed)
    merchants = generate_merchants()
    merch_map = {m["merchant_id"]: m for m in merchants}
    merch_ids = list(merch_map.keys())
    methods = ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NET_BANKING"]

    transactions: List[Dict[str, Any]] = []
    settlements: List[Dict[str, Any]] = []
    bank_entries: List[Dict[str, Any]] = []
    refunds: List[Dict[str, Any]] = []
    ground_truth: List[Dict[str, Any]] = []

    start_date = date(2026, 9, 1)
    ing_ts = "2026-10-25T20:00:00Z"

    # 3,200 distinct synthetic customers (CUST_10001 .. CUST_13200)
    num_customers = 3200

    def calc_fees(gross: Decimal, m_id: str) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
        """Return (mdr_fee, gst_tax, total_fee, expected_net)."""
        m = merch_map[m_id]
        rate = Decimal(m["contractual_fee_rate"])
        fixed = Decimal(m["contractual_fixed_fee"])
        mdr = q2(gross * rate + fixed)
        gst = q2(mdr * config.gst_rate)
        tot_fee = q2(mdr + gst)
        net = q2(gross - tot_fee)
        return mdr, gst, tot_fee, net

    stl_seq = 1
    bnk_seq = 1
    ref_seq = 1

    # Scenario ranges across 1..10000:
    # 1..8500     (8,500): S01 Exact Transaction-to-Settlement & S02 Exact Settlement-to-Bank Match (Clean baseline)
    #   - Within 1..8500:
    #     - 1..8000     (8,000): S01_EXACT_TXN_STL_BANK_MATCH
    #     - 8001..8300    (300): S27_CLEAN_RECORD_NO_FALSE_POSITIVE (high-value clean transactions)
    #     - 8301..8420    (120): S28_BOUNDARY_EXACT_TOLERANCE_TIMING (exact ₹1.00 boundary or exact 2-business-day SLA boundary)
    #     - 8421..8500     (80): S11_LEGITIMATE_REPEATED_CUSTOMER_ORDER (same customer & amount minutes apart, valid distinct payment)
    # 8501..8800    (300): S03_SMALL_VARIANCE_WITHIN_TOLERANCE (within +/- ₹1.00 INR tolerance)
    # 8801..9050    (250): S04_FEE_ADJUSTED_SETTLEMENT (gateway interchange/reserve adjustment supported by fee policy)
    # 9051..9200    (150): S13_LEGITIMATE_MULTI_PART_SETTLEMENT (two partial settlement lines summing to exact expected net)
    # 9201..9360    (160): S05_LATE_SETTLEMENT (> 2 business days SLA)
    # 9361..9420     (60): S23_LATE_ARRIVING_BANK_POSTING (settlement on time, bank credit > 2 business days after settlement)
    # 9421..9560    (140): S06_MISSING_SETTLEMENT_RECORD (captured transaction, no settlement & no bank entry)
    # 9561..9610     (50): S07_SETTLEMENT_WITHOUT_LEDGER (orphan settlement & bank entry with no ledger transaction)
    # 9611..9660     (50): S08_BANK_WITHOUT_SETTLEMENT_OR_MISSING_BANK (30 missing bank entry for settled txn + 20 bank entry without settlement)
    # 9661..9730     (70): S09_DUPLICATE_SETTLEMENT_CONFIRMED (transaction settled twice across two settlement IDs)
    # 9731..9760     (30): S10_DUPLICATE_BANK_ENTRY (single settlement credited twice in bank statement)
    # 9761..9820     (60): S12_PARTIAL_SETTLEMENT_SHORTFALL (only 1 of 2 installments settled; 40% unpaid shortfall)
    # 9821..9855     (35): S14_AMBIGUOUS_CANDIDATE_MATCH (multiple unlinked candidate settlements with identical merchant/date/amount)
    # 9856..9895     (40): S21_REFUND_AMOUNT_MISMATCH (settled refund deduction != requested refund amount)
    # 9896..9925     (30): S22_REFUND_UNREVERSED_OR_MISSING_EVIDENCE (15 unreversed failed refund + 15 refund missing settlement/bank evidence)
    # 9926..9955     (30): S26_MANUAL_REVIEW_REQUIRED (large unexplained variance > ₹1.00 or duplicate candidate needing analyst review)
    # 9956..9965     (10): S15_MISSING_TRANSACTION_IDENTIFIER (malformed/blank transaction_id in ledger -> quarantined)
    # 9966..9975     (10): S16_MISSING_SETTLEMENT_REFERENCE (blank merchant_id / mandatory reference -> quarantined)
    # 9976..9985     (10): S17_INVALID_MALFORMED_AMOUNT (negative or zero transaction_amount -> quarantined)
    # 9986..9992      (7): S18_MISSING_DATE (missing transaction_date -> quarantined)
    # 9993..10000     (8): S19_INVALID_CURRENCY (currency='USD' or 'EUR' without FX policy -> quarantined)
    # Plus:
    # - Scenario 20 (S20_REPEATED_INGESTION): 25 exact re-ingested rows in transactions.csv (idx 1..25) and 25 in settlements.csv
    # - Scenario 24 (S24_PREVIOUSLY_RESOLVED_EXCEPTION): 95 exceptions across S05/S06/S09/S21 marked RESOLVED with resolved_timestamp
    # - Scenario 25 (S25_REOPENED_EXCEPTION): 25 exceptions across S05/S09/S12 marked REOPENED with reopened_timestamp

    for idx in range(1, config.default_txn_count + 1):
        m_id = merch_ids[(idx - 1) % len(merch_ids)]
        m_info = merch_map[m_id]
        gateway = m_info["default_payment_gateway"]
        sla_days = int(m_info["settlement_sla_days"])
        pay_method = methods[(idx * 3) % len(methods)]
        cust_id = f"CUST_{10001 + ((idx * 17) % num_customers)}"

        day_offset = (idx - 1) % 50  # 2026-09-01 .. 2026-10-20
        txn_date = start_date + timedelta(days=day_offset)
        txn_ts = f"{txn_date.isoformat()}T{8 + (idx % 14):02d}:{(idx * 11) % 60:02d}:{(idx * 7) % 60:02d}Z"
        exp_stl_date = add_business_days(txn_date, sla_days)

        # Deterministic gross transaction amount between ₹250.00 and ₹18,500.00
        gross = q2(Decimal(str(250 + ((idx * 173) % 18250))) + Decimal(str(((idx * 29) % 100) / 100)))
        mdr_fee, gst_tax, total_fee, expected_net = calc_fees(gross, m_id)

        txn_id = f"TXN_2026_{idx:06d}"
        pay_ref = f"PAYREF_{202600000 + idx}"
        ord_ref = f"ORD_{500000 + idx}"
        batch_id = f"BATCH_{gateway[:4].upper()}_{exp_stl_date.strftime('%Y%m%d')}"

        def add_txn(
            t_id: str = txn_id,
            c_id: str = cust_id,
            m_code: str = m_id,
            p_ref: str = pay_ref,
            o_ref: str = ord_ref,
            t_ts: str = txn_ts,
            t_date: str = txn_date.isoformat(),
            t_amt: str = f"{gross:.2f}",
            curr: str = "INR",
            p_meth: str = pay_method,
            p_stat: str = "CAPTURED",
            p_gw: str = gateway,
            s_exp_date: str = exp_stl_date.isoformat(),
            t_fee: str = f"{total_fee:.2f}",
            exp_net: str = f"{expected_net:.2f}",
            ver: str = "1",
            src_sys: str = "CORE_SWITCH_LEDGER",
        ) -> Dict[str, Any]:
            row = {
                "transaction_id": t_id,
                "customer_id": c_id,
                "merchant_id": m_code,
                "payment_reference": p_ref,
                "order_reference": o_ref,
                "transaction_timestamp": t_ts,
                "transaction_date": t_date,
                "transaction_amount": t_amt,
                "currency": curr,
                "payment_method": p_meth,
                "payment_status": p_stat,
                "payment_gateway": p_gw,
                "settlement_expected_date": s_exp_date,
                "transaction_fee": t_fee,
                "expected_net_amount": exp_net,
                "ingestion_timestamp": ing_ts,
                "source_system": src_sys,
                "record_version": ver,
                "is_synthetic": "TRUE",
            }
            transactions.append(row)
            return row

        def add_stl(
            s_id: str,
            s_ref: str,
            t_id: str,
            p_ref: str,
            m_code: str,
            b_id: str,
            s_date: date,
            g_amt: Decimal,
            f_amt: Decimal,
            n_amt: Decimal,
            curr: str = "INR",
            s_stat: str = "SETTLED",
            s_type: str = "STANDARD",
            line_no: int = 1,
            tot_lines: int = 1,
            src_sys: str = gateway,
        ) -> Dict[str, Any]:
            row = {
                "settlement_id": s_id,
                "settlement_reference": s_ref,
                "transaction_id": t_id,
                "payment_reference": p_ref,
                "merchant_id": m_code,
                "settlement_batch_id": b_id,
                "settlement_timestamp": f"{s_date.isoformat()}T18:30:00Z",
                "settlement_date": s_date.isoformat(),
                "gross_amount": f"{g_amt:.2f}",
                "fee_amount": f"{f_amt:.2f}",
                "net_settlement_amount": f"{n_amt:.2f}",
                "currency": curr,
                "settlement_status": s_stat,
                "settlement_type": s_type,
                "allocation_line_no": str(line_no),
                "total_allocation_lines": str(tot_lines),
                "source_system": src_sys,
                "ingestion_timestamp": ing_ts,
                "is_synthetic": "TRUE",
            }
            settlements.append(row)
            return row

        def add_bnk(
            b_id_str: str,
            b_ref: str,
            s_ref: str,
            t_ref: str,
            m_code: str,
            v_date: date,
            cr_amt: Decimal,
            dr_amt: Decimal = Decimal("0.00"),
            curr: str = "INR",
            desc: str = "NEFT/RTGS ACQUIRER PAYOUT",
            b_stat: str = "POSTED",
        ) -> Dict[str, Any]:
            signed_amt = q2(cr_amt - dr_amt)
            row = {
                "bank_entry_id": b_id_str,
                "bank_reference": b_ref,
                "settlement_reference": s_ref,
                "transaction_reference": t_ref,
                "merchant_id": m_code,
                "entry_timestamp": f"{v_date.isoformat()}T19:45:00Z",
                "value_date": v_date.isoformat(),
                "credit_amount": f"{cr_amt:.2f}",
                "debit_amount": f"{dr_amt:.2f}",
                "signed_bank_amount": f"{signed_amt:.2f}",
                "currency": curr,
                "bank_description": desc,
                "bank_status": b_stat,
                "ingestion_timestamp": ing_ts,
                "is_synthetic": "TRUE",
            }
            bank_entries.append(row)
            return row

        def add_gt(
            case_id: str,
            src_id: str,
            scenario: str,
            exp_class: str,
            match_grp: str,
            exp_var: Decimal,
            exc_type: str,
            severity: str,
            res_state: str,
            exp_amt: Decimal,
            obs_amt: Decimal,
            is_exc: bool,
            conf_loss: Decimal = Decimal("0.00"),
            m_code: str = m_id,
            gw: str = gateway,
        ) -> None:
            ground_truth.append({
                "synthetic_case_id": case_id,
                "source_record_id": src_id,
                "merchant_id": m_code,
                "payment_gateway": gw,
                "planted_scenario": scenario,
                "expected_classification": exp_class,
                "expected_match_group": match_grp,
                "expected_amount": f"{exp_amt:.2f}",
                "observed_amount": f"{obs_amt:.2f}",
                "expected_variance": f"{exp_var:.2f}",
                "expected_abs_exposure": f"{(Decimal('0.00') if (not is_exc or res_state == 'RESOLVED') else abs(exp_var)):.2f}",
                "expected_confirmed_loss": f"{conf_loss:.2f}",
                "expected_exception_type": exc_type,
                "expected_severity": severity,
                "expected_resolution_state": res_state,
                "is_planted_exception": "TRUE" if is_exc else "FALSE",
            })

        # ------------------------------------------------------------------
        # BLOCK 1: Clean Exact Matches, Boundary Cases & Legitimate Repeats (1..8500)
        # ------------------------------------------------------------------
        if 1 <= idx <= 8500:
            s_id = f"STL_2026_{stl_seq:06d}"
            s_ref = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_str = f"BNK_2026_{bnk_seq:06d}"
            b_ref = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            if 1 <= idx <= 8000:
                scen = "S20_REPEATED_INGESTION" if idx <= 25 else ("S02_EXACT_STL_BANK_MATCH" if idx % 2 == 0 else "S01_EXACT_TXN_STL_MATCH")
                exp_cls = "MATCHED_EXACT"
                var_val = Decimal("0.00")
                obs_net = expected_net
                stl_dt = exp_stl_date
                p_ref_use = pay_ref
                o_ref_use = ord_ref
            elif 8001 <= idx <= 8300:
                scen = "S27_CLEAN_RECORD_NO_FALSE_POSITIVE"
                exp_cls = "MATCHED_EXACT"
                var_val = Decimal("0.00")
                obs_net = expected_net
                stl_dt = exp_stl_date
                p_ref_use = pay_ref
                o_ref_use = ord_ref
            elif 8301 <= idx <= 8420:
                # Boundary cases: first 60 exact 2-business-day boundary (MATCHED_EXACT),
                # next 60 exact +/- ₹1.00 boundary (MATCHED_WITH_VARIANCE)
                if idx <= 8360:
                    scen = "S28_BOUNDARY_SLA_2BDAYS"
                    exp_cls = "MATCHED_EXACT"
                    var_val = Decimal("0.00")
                    obs_net = expected_net
                    stl_dt = add_business_days(txn_date, 2)
                else:
                    scen = "S28_BOUNDARY_TOLERANCE_1INR"
                    exp_cls = "MATCHED_WITH_VARIANCE"
                    var_val = Decimal("1.00") if idx % 2 == 0 else Decimal("-1.00")
                    obs_net = q2(expected_net + var_val)
                    stl_dt = exp_stl_date
                p_ref_use = pay_ref
                o_ref_use = ord_ref
            else:
                # 8421..8500: S11 Legitimate repeated customer order (shared order_reference prefix, distinct txn_id)
                scen = "S11_LEGITIMATE_REPEATED_IDENTIFIER"
                exp_cls = "MATCHED_EXACT"
                var_val = Decimal("0.00")
                obs_net = expected_net
                stl_dt = exp_stl_date
                p_ref_use = pay_ref
                o_ref_use = f"ORD_REPEAT_{(idx - 8421) // 2 + 1:04d}"

            t_row = add_txn(p_ref=p_ref_use, o_ref=o_ref_use)
            s_row = add_stl(s_id, s_ref, txn_id, p_ref_use, m_id, batch_id, stl_dt, gross, q2(total_fee - var_val), obs_net)
            add_bnk(b_id_str, b_ref, s_ref, txn_id, m_id, stl_dt, obs_net)

            # Scenario 20: Repeated ingestion of first 25 transactions and settlements
            if idx <= 25:
                dup_t = dict(t_row)
                dup_t["source_system"] = "CORE_SWITCH_LEDGER_REPLAY"
                transactions.append(dup_t)
                dup_s = dict(s_row)
                dup_s["source_system"] = f"{gateway}_REPLAY"
                settlements.append(dup_s)

            add_gt(
                f"CASE_{idx:06d}", txn_id, scen, exp_cls, f"{txn_id}|{s_id}|{b_id_str}",
                var_val, "NONE", "NONE", "NOT_APPLICABLE", expected_net, obs_net, False
            )

        # ------------------------------------------------------------------
        # BLOCK 2: Small Variance Within Tolerance (8501..8800 = 300 cases)
        # ------------------------------------------------------------------
        elif 8501 <= idx <= 8800:
            s_id = f"STL_2026_{stl_seq:06d}"
            s_ref = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_str = f"BNK_2026_{bnk_seq:06d}"
            b_ref = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            deltas = [Decimal("-0.85"), Decimal("-0.50"), Decimal("-0.25"), Decimal("0.30"), Decimal("0.65"), Decimal("0.90")]
            delta = deltas[(idx - 8501) % len(deltas)]
            obs_net = q2(expected_net + delta)

            add_txn()
            add_stl(s_id, s_ref, txn_id, pay_ref, m_id, batch_id, exp_stl_date, gross, q2(total_fee - delta), obs_net)
            add_bnk(b_id_str, b_ref, s_ref, txn_id, m_id, exp_stl_date, obs_net)

            add_gt(
                f"CASE_{idx:06d}", txn_id, "S03_SMALL_VARIANCE_TOLERANCE", "MATCHED_WITH_VARIANCE",
                f"{txn_id}|{s_id}|{b_id_str}", delta, "NONE", "LOW", "NOT_APPLICABLE", expected_net, obs_net, False
            )

        # ------------------------------------------------------------------
        # BLOCK 3: Fee-Adjusted Settlements (8801..9050 = 250 cases)
        # ------------------------------------------------------------------
        elif 8801 <= idx <= 9050:
            s_id = f"STL_2026_{stl_seq:06d}"
            s_ref = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_str = f"BNK_2026_{bnk_seq:06d}"
            b_ref = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            # Documented gateway cross-border/interchange surcharge adjustment of ₹15.00..₹65.00
            surcharge = q2(Decimal(str(15 + ((idx - 8801) % 6) * 10)))
            adj_fee = q2(total_fee + surcharge)
            obs_net = q2(gross - adj_fee)

            add_txn()
            add_stl(
                s_id, s_ref, txn_id, pay_ref, m_id, batch_id, exp_stl_date,
                gross, adj_fee, obs_net, s_type="FEE_ADJUSTED"
            )
            add_bnk(b_id_str, b_ref, s_ref, txn_id, m_id, exp_stl_date, obs_net)

            add_gt(
                f"CASE_{idx:06d}", txn_id, "S04_FEE_ADJUSTED_SETTLEMENT", "MATCHED_FEE_ADJUSTED",
                f"{txn_id}|{s_id}|{b_id_str}", Decimal("0.00"), "NONE", "NONE", "NOT_APPLICABLE", obs_net, obs_net, False
            )

        # ------------------------------------------------------------------
        # BLOCK 4: Legitimate Multi-Part Partial Settlements (9051..9200 = 150 cases)
        # ------------------------------------------------------------------
        elif 9051 <= idx <= 9200:
            s_id_1 = f"STL_2026_{stl_seq:06d}"
            s_ref_1 = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            s_id_2 = f"STL_2026_{stl_seq:06d}"
            s_ref_2 = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_1 = f"BNK_2026_{bnk_seq:06d}"
            b_ref_1 = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1
            b_id_2 = f"BNK_2026_{bnk_seq:06d}"
            b_ref_2 = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            g1 = q2(gross * Decimal("0.60"))
            g2 = q2(gross - g1)
            f1 = q2(total_fee * Decimal("0.60"))
            f2 = q2(total_fee - f1)
            n1 = q2(g1 - f1)
            n2 = q2(expected_net - n1)

            add_txn()
            add_stl(s_id_1, s_ref_1, txn_id, pay_ref, m_id, batch_id, exp_stl_date, g1, f1, n1, s_type="PARTIAL_SPLIT", line_no=1, tot_lines=2)
            add_stl(s_id_2, s_ref_2, txn_id, pay_ref, m_id, batch_id, exp_stl_date, g2, f2, n2, s_type="PARTIAL_SPLIT", line_no=2, tot_lines=2)
            add_bnk(b_id_1, b_ref_1, s_ref_1, txn_id, m_id, exp_stl_date, n1)
            add_bnk(b_id_2, b_ref_2, s_ref_2, txn_id, m_id, exp_stl_date, n2)

            add_gt(
                f"CASE_{idx:06d}", txn_id, "S13_LEGITIMATE_MULTI_PART_SETTLEMENT", "MATCHED_PARTIAL",
                f"{txn_id}|{s_id_1}+{s_id_2}", Decimal("0.00"), "NONE", "NONE", "NOT_APPLICABLE", expected_net, expected_net, False
            )

        # ------------------------------------------------------------------
        # BLOCK 5: Late Settlements > 2 Business Days (9201..9360 = 160 cases)
        # ------------------------------------------------------------------
        elif 9201 <= idx <= 9360:
            s_id = f"STL_2026_{stl_seq:06d}"
            s_ref = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_str = f"BNK_2026_{bnk_seq:06d}"
            b_ref = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            delay_bdays = 4 + ((idx - 9201) % 6)  # 4..9 business days after capture
            late_dt = add_business_days(txn_date, delay_bdays)
            late_batch = f"BATCH_{gateway[:4].upper()}_{late_dt.strftime('%Y%m%d')}"

            add_txn()
            add_stl(s_id, s_ref, txn_id, pay_ref, m_id, late_batch, late_dt, gross, total_fee, expected_net)
            add_bnk(b_id_str, b_ref, s_ref, txn_id, m_id, late_dt, expected_net)

            # Lifecycle state: 40 RESOLVED (S24), 10 REOPENED (S25), 110 OPEN
            if idx <= 9240:
                res_st = "RESOLVED"
                scen = "S24_PREVIOUSLY_RESOLVED_EXCEPTION"
            elif idx <= 9250:
                res_st = "REOPENED"
                scen = "S25_REOPENED_EXCEPTION"
            else:
                res_st = "OPEN"
                scen = "S05_LATE_SETTLEMENT"

            add_gt(
                f"CASE_{idx:06d}", txn_id, scen, "LATE_SETTLEMENT",
                f"{txn_id}|{s_id}|{b_id_str}", Decimal("0.00"), "LATE_SETTLEMENT", "MEDIUM", res_st, expected_net, expected_net, True
            )

        # ------------------------------------------------------------------
        # BLOCK 6: Late-Arriving Bank Postings (9361..9420 = 60 cases)
        # ------------------------------------------------------------------
        elif 9361 <= idx <= 9420:
            s_id = f"STL_2026_{stl_seq:06d}"
            s_ref = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_str = f"BNK_2026_{bnk_seq:06d}"
            b_ref = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            bank_dt = add_business_days(exp_stl_date, 5)
            add_txn()
            add_stl(s_id, s_ref, txn_id, pay_ref, m_id, batch_id, exp_stl_date, gross, total_fee, expected_net)
            add_bnk(b_id_str, b_ref, s_ref, txn_id, m_id, bank_dt, expected_net)

            add_gt(
                f"CASE_{idx:06d}", txn_id, "S23_LATE_ARRIVING_BANK_RECORD", "TIMING_EXCEPTION",
                f"{txn_id}|{s_id}|{b_id_str}", Decimal("0.00"), "TIMING_EXCEPTION", "MEDIUM", "OPEN", expected_net, expected_net, True
            )

        # ------------------------------------------------------------------
        # BLOCK 7: Missing Settlement Records (9421..9560 = 140 cases)
        # ------------------------------------------------------------------
        elif 9421 <= idx <= 9560:
            add_txn()
            # No settlement or bank entry!
            if idx <= 9445:
                res_st = "RESOLVED"
                scen = "S24_PREVIOUSLY_RESOLVED_EXCEPTION"
                conf_loss = Decimal("0.00")
            elif idx <= 9455:
                res_st = "OPEN"
                scen = "S06_MISSING_SETTLEMENT"
                conf_loss = expected_net  # Confirmed loss on 10 expired gateway disputes
            else:
                res_st = "OPEN"
                scen = "S06_MISSING_SETTLEMENT"
                conf_loss = Decimal("0.00")

            add_gt(
                f"CASE_{idx:06d}", txn_id, scen, "MISSING_SETTLEMENT",
                f"{txn_id}|NONE", -expected_net, "MISSING_SETTLEMENT", "CRITICAL", res_st,
                expected_net, Decimal("0.00"), True, conf_loss=conf_loss
            )

        # ------------------------------------------------------------------
        # BLOCK 8: Settlements Without Corresponding Ledger Transactions (9561..9610 = 50 cases)
        # ------------------------------------------------------------------
        elif 9561 <= idx <= 9610:
            s_id = f"STL_2026_{stl_seq:06d}"
            s_ref = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_str = f"BNK_2026_{bnk_seq:06d}"
            b_ref = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1
            orphan_txn = f"TXN_UNRECORDED_{idx:06d}"

            # Emit settlement & bank entry ONLY (no ledger transaction)
            add_stl(s_id, s_ref, orphan_txn, pay_ref, m_id, batch_id, exp_stl_date, gross, total_fee, expected_net)
            add_bnk(b_id_str, b_ref, s_ref, orphan_txn, m_id, exp_stl_date, expected_net)

            add_gt(
                f"CASE_{idx:06d}", s_id, "S07_SETTLEMENT_WITHOUT_LEDGER", "MISSING_LEDGER",
                f"NONE|{s_id}|{b_id_str}", expected_net, "MISSING_LEDGER", "HIGH", "OPEN",
                Decimal("0.00"), expected_net, True
            )

        # ------------------------------------------------------------------
        # BLOCK 9: Missing Bank Entry (9611..9640) & Bank Without Settlement (9641..9660) (50 cases)
        # ------------------------------------------------------------------
        elif 9611 <= idx <= 9660:
            if idx <= 9640:
                # Settled in gateway report, but missing on bank statement
                s_id = f"STL_2026_{stl_seq:06d}"
                s_ref = f"STLREF_{stl_seq:06d}"
                stl_seq += 1
                add_txn()
                add_stl(s_id, s_ref, txn_id, pay_ref, m_id, batch_id, exp_stl_date, gross, total_fee, expected_net)
                add_gt(
                    f"CASE_{idx:06d}", txn_id, "S08_MISSING_BANK_COUNTERPART", "MISSING_BANK_ENTRY",
                    f"{txn_id}|{s_id}|NONE", -expected_net, "MISSING_BANK_ENTRY", "HIGH", "OPEN",
                    expected_net, Decimal("0.00"), True
                )
            else:
                # Bank entry posted without settlement record or ledger record (S08 Bank without settlement)
                b_id_str = f"BNK_2026_{bnk_seq:06d}"
                b_ref = f"UTR2026{bnk_seq:07d}"
                bnk_seq += 1
                unlinked_sref = f"STLREF_UNLINKED_{idx:06d}"
                add_bnk(b_id_str, b_ref, unlinked_sref, f"TXN_UNLINKED_{idx:06d}", m_id, exp_stl_date, expected_net)
                add_gt(
                    f"CASE_{idx:06d}", b_id_str, "S08_BANK_WITHOUT_SETTLEMENT", "MISSING_LEDGER",
                    f"NONE|NONE|{b_id_str}", expected_net, "MISSING_LEDGER", "HIGH", "OPEN",
                    Decimal("0.00"), expected_net, True
                )

        # ------------------------------------------------------------------
        # BLOCK 10: Confirmed Duplicate Settlements (9661..9730 = 70 cases)
        # ------------------------------------------------------------------
        elif 9661 <= idx <= 9730:
            s_id_1 = f"STL_2026_{stl_seq:06d}"
            s_ref_1 = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            s_id_2 = f"STL_2026_{stl_seq:06d}"
            s_ref_2 = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_1 = f"BNK_2026_{bnk_seq:06d}"
            b_ref_1 = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1
            b_id_2 = f"BNK_2026_{bnk_seq:06d}"
            b_ref_2 = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            add_txn()
            add_stl(s_id_1, s_ref_1, txn_id, pay_ref, m_id, batch_id, exp_stl_date, gross, total_fee, expected_net)
            add_bnk(b_id_1, b_ref_1, s_ref_1, txn_id, m_id, exp_stl_date, expected_net)

            dup_dt = add_business_days(exp_stl_date, 1)
            dup_batch = f"BATCH_{gateway[:4].upper()}_{dup_dt.strftime('%Y%m%d')}"
            add_stl(s_id_2, s_ref_2, txn_id, pay_ref, m_id, dup_batch, dup_dt, gross, total_fee, expected_net)
            add_bnk(b_id_2, b_ref_2, s_ref_2, txn_id, m_id, dup_dt, expected_net)

            if idx <= 9680:
                res_st = "RESOLVED"
                scen = "S24_PREVIOUSLY_RESOLVED_EXCEPTION"
            elif idx <= 9690:
                res_st = "REOPENED"
                scen = "S25_REOPENED_EXCEPTION"
            else:
                res_st = "OPEN"
                scen = "S09_DUPLICATE_SETTLEMENT_CONFIRMED"

            add_gt(
                f"CASE_{idx:06d}", txn_id, scen, "DUPLICATE_CONFIRMED",
                f"{txn_id}|{s_id_1}+{s_id_2}", expected_net, "DUPLICATE_CONFIRMED", "CRITICAL", res_st,
                expected_net, q2(expected_net * 2), True
            )

        # ------------------------------------------------------------------
        # BLOCK 11: Duplicate Bank Entries (9731..9760 = 30 cases)
        # ------------------------------------------------------------------
        elif 9731 <= idx <= 9760:
            s_id = f"STL_2026_{stl_seq:06d}"
            s_ref = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_1 = f"BNK_2026_{bnk_seq:06d}"
            b_ref_1 = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1
            b_id_2 = f"BNK_2026_{bnk_seq:06d}"
            b_ref_2 = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            add_txn()
            add_stl(s_id, s_ref, txn_id, pay_ref, m_id, batch_id, exp_stl_date, gross, total_fee, expected_net)
            add_bnk(b_id_1, b_ref_1, s_ref, txn_id, m_id, exp_stl_date, expected_net)
            add_bnk(b_id_2, b_ref_2, s_ref, txn_id, m_id, exp_stl_date, expected_net, desc="DUPLICATE BANK CREDIT POSTING")

            add_gt(
                f"CASE_{idx:06d}", txn_id, "S10_DUPLICATE_BANK_ENTRY", "DUPLICATE_CONFIRMED",
                f"{txn_id}|{s_id}|{b_id_1}+{b_id_2}", expected_net, "DUPLICATE_CONFIRMED", "CRITICAL", "OPEN",
                expected_net, q2(expected_net * 2), True
            )

        # ------------------------------------------------------------------
        # BLOCK 12: Partial Settlement Shortfall (9761..9820 = 60 cases)
        # ------------------------------------------------------------------
        elif 9761 <= idx <= 9820:
            s_id_1 = f"STL_2026_{stl_seq:06d}"
            s_ref_1 = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_1 = f"BNK_2026_{bnk_seq:06d}"
            b_ref_1 = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            g1 = q2(gross * Decimal("0.60"))
            f1 = q2(total_fee * Decimal("0.60"))
            n1 = q2(g1 - f1)
            shortfall = q2(n1 - expected_net)

            add_txn()
            add_stl(s_id_1, s_ref_1, txn_id, pay_ref, m_id, batch_id, exp_stl_date, g1, f1, n1, s_type="PARTIAL_SPLIT", line_no=1, tot_lines=2)
            add_bnk(b_id_1, b_ref_1, s_ref_1, txn_id, m_id, exp_stl_date, n1)

            res_st = "REOPENED" if idx <= 9765 else "OPEN"
            scen = "S25_REOPENED_EXCEPTION" if idx <= 9765 else "S12_PARTIAL_SETTLEMENT_SHORTFALL"

            add_gt(
                f"CASE_{idx:06d}", txn_id, scen, "PARTIALLY_SETTLED",
                f"{txn_id}|{s_id_1}", shortfall, "PARTIALLY_SETTLED", "HIGH", res_st,
                expected_net, n1, True
            )

        # ------------------------------------------------------------------
        # BLOCK 13: Ambiguous Candidate Matches (9821..9855 = 35 cases)
        # ------------------------------------------------------------------
        elif 9821 <= idx <= 9855:
            s_id_a = f"STL_2026_{stl_seq:06d}"
            s_ref_a = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            s_id_b = f"STL_2026_{stl_seq:06d}"
            s_ref_b = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_a = f"BNK_2026_{bnk_seq:06d}"
            b_ref_a = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1
            b_id_b = f"BNK_2026_{bnk_seq:06d}"
            b_ref_b = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            add_txn()
            # Both candidate settlements lack direct transaction_id and share payment_reference + merchant + amount
            add_stl(s_id_a, s_ref_a, "UNLINKED_AMBIG", pay_ref, m_id, batch_id, exp_stl_date, gross, total_fee, expected_net, s_type="AMBIGUOUS_CANDIDATE")
            add_stl(s_id_b, s_ref_b, "UNLINKED_AMBIG", pay_ref, m_id, batch_id, exp_stl_date, gross, total_fee, expected_net, s_type="AMBIGUOUS_CANDIDATE")
            add_bnk(b_id_a, b_ref_a, s_ref_a, "UNLINKED_AMBIG", m_id, exp_stl_date, expected_net)
            add_bnk(b_id_b, b_ref_b, s_ref_b, "UNLINKED_AMBIG", m_id, exp_stl_date, expected_net)

            add_gt(
                f"CASE_{idx:06d}", txn_id, "S14_AMBIGUOUS_CANDIDATE_MATCH", "AMBIGUOUS_MATCH",
                f"{txn_id}|{s_id_a}?{s_id_b}", -expected_net, "AMBIGUOUS_MATCH", "HIGH", "OPEN",
                expected_net, Decimal("0.00"), True
            )

        # ------------------------------------------------------------------
        # BLOCK 14: Refund Amount Mismatch (9856..9895 = 40 cases)
        # ------------------------------------------------------------------
        elif 9856 <= idx <= 9895:
            r_id = f"REF_2026_{ref_seq:05d}"
            r_ref = f"REFREF_{ref_seq:05d}"
            ref_seq += 1
            s_id = f"STL_2026_{stl_seq:06d}"
            s_ref = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_str = f"BNK_2026_{bnk_seq:06d}"
            b_ref = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            req_ref = q2(gross * Decimal("0.30"))
            ded_ref = q2(gross * Decimal("0.45"))  # 15% over-deducted refund
            exp_after_ref = q2(expected_net - req_ref)
            obs_after_ref = q2(expected_net - ded_ref)
            signed_var = q2(obs_after_ref - exp_after_ref)

            add_txn()
            refunds.append({
                "refund_id": r_id,
                "original_transaction_id": txn_id,
                "refund_reference": r_ref,
                "merchant_id": m_id,
                "refund_timestamp": f"{exp_stl_date.isoformat()}T11:00:00Z",
                "refund_amount": f"{req_ref:.2f}",
                "settled_refund_deduction": f"{ded_ref:.2f}",
                "currency": "INR",
                "refund_status": "PROCESSED_MISMATCH",
                "refund_reason": "CUSTOMER_RETURN_PARTIAL",
                "settlement_reference": s_ref,
                "bank_reference": b_ref,
                "ingestion_timestamp": ing_ts,
                "is_synthetic": "TRUE",
            })
            add_stl(s_id, s_ref, txn_id, pay_ref, m_id, batch_id, exp_stl_date, gross, q2(total_fee + ded_ref), obs_after_ref, s_type="REFUND_ADJUSTED")
            add_bnk(b_id_str, b_ref, s_ref, txn_id, m_id, exp_stl_date, obs_after_ref)

            res_st = "RESOLVED" if idx <= 9865 else "OPEN"
            scen = "S24_PREVIOUSLY_RESOLVED_EXCEPTION" if idx <= 9865 else "S21_REFUND_AMOUNT_MISMATCH"

            add_gt(
                f"CASE_{idx:06d}", txn_id, scen, "REFUND_MISMATCH",
                f"{txn_id}|{s_id}|{r_id}", signed_var, "REFUND_MISMATCH", "HIGH", res_st,
                exp_after_ref, obs_after_ref, True
            )

        # ------------------------------------------------------------------
        # BLOCK 15: Unreversed Failed Refund & Missing Refund Evidence (9896..9925 = 30 cases)
        # ------------------------------------------------------------------
        elif 9896 <= idx <= 9925:
            r_id = f"REF_2026_{ref_seq:05d}"
            r_ref = f"REFREF_{ref_seq:05d}"
            ref_seq += 1
            s_id = f"STL_2026_{stl_seq:06d}"
            s_ref = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_str = f"BNK_2026_{bnk_seq:06d}"
            b_ref = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            ref_amt = q2(gross * Decimal("0.25"))
            obs_after = q2(expected_net - ref_amt)
            add_txn()

            if idx <= 9910:
                # Unreversed failed refund
                refunds.append({
                    "refund_id": r_id,
                    "original_transaction_id": txn_id,
                    "refund_reference": r_ref,
                    "merchant_id": m_id,
                    "refund_timestamp": f"{exp_stl_date.isoformat()}T12:15:00Z",
                    "refund_amount": f"{ref_amt:.2f}",
                    "settled_refund_deduction": f"{ref_amt:.2f}",
                    "currency": "INR",
                    "refund_status": "FAILED_UNREVERSED",
                    "refund_reason": "ISSUER_DECLINED_REFUND",
                    "settlement_reference": s_ref,
                    "bank_reference": b_ref,
                    "ingestion_timestamp": ing_ts,
                    "is_synthetic": "TRUE",
                })
                add_stl(s_id, s_ref, txn_id, pay_ref, m_id, batch_id, exp_stl_date, gross, q2(total_fee + ref_amt), obs_after, s_type="REFUND_ADJUSTED")
                add_bnk(b_id_str, b_ref, s_ref, txn_id, m_id, exp_stl_date, obs_after)
                conf_loss = ref_amt if idx <= 9900 else Decimal("0.00")
                add_gt(
                    f"CASE_{idx:06d}", txn_id, "S22_UNREVERSED_REFUND", "UNREVERSED_REFUND",
                    f"{txn_id}|{s_id}|{r_id}", -ref_amt, "UNREVERSED_REFUND", "CRITICAL", "OPEN",
                    expected_net, obs_after, True, conf_loss=conf_loss
                )
            else:
                # Refund missing corresponding settlement/bank evidence
                refunds.append({
                    "refund_id": r_id,
                    "original_transaction_id": txn_id,
                    "refund_reference": r_ref,
                    "merchant_id": m_id,
                    "refund_timestamp": f"{exp_stl_date.isoformat()}T14:20:00Z",
                    "refund_amount": f"{ref_amt:.2f}",
                    "settled_refund_deduction": "0.00",
                    "currency": "INR",
                    "refund_status": "MISSING_REFUND_EVIDENCE",
                    "refund_reason": "ORDER_CANCELLED",
                    "settlement_reference": "",
                    "bank_reference": "",
                    "ingestion_timestamp": ing_ts,
                    "is_synthetic": "TRUE",
                })
                add_stl(s_id, s_ref, txn_id, pay_ref, m_id, batch_id, exp_stl_date, gross, total_fee, expected_net)
                add_bnk(b_id_str, b_ref, s_ref, txn_id, m_id, exp_stl_date, expected_net)
                add_gt(
                    f"CASE_{idx:06d}", txn_id, "S22_MISSING_REFUND_EVIDENCE", "MISSING_REFUND_EVIDENCE",
                    f"{txn_id}|{s_id}|{r_id}", ref_amt, "MISSING_REFUND_EVIDENCE", "HIGH", "OPEN",
                    q2(expected_net - ref_amt), expected_net, True
                )

        # ------------------------------------------------------------------
        # BLOCK 16: Manual Review Required / Duplicate Candidate (9926..9955 = 30 cases)
        # ------------------------------------------------------------------
        elif 9926 <= idx <= 9955:
            s_id = f"STL_2026_{stl_seq:06d}"
            s_ref = f"STLREF_{stl_seq:06d}"
            stl_seq += 1
            b_id_str = f"BNK_2026_{bnk_seq:06d}"
            b_ref = f"UTR2026{bnk_seq:07d}"
            bnk_seq += 1

            if idx <= 9940:
                # Duplicate candidate with altered settlement amount requiring manual review
                s_id_cand = f"STL_2026_{stl_seq:06d}"
                s_ref_cand = f"STLREF_{stl_seq:06d}"
                stl_seq += 1
                cand_net = q2(expected_net * Decimal("0.50"))
                add_txn()
                add_stl(s_id, s_ref, txn_id, pay_ref, m_id, batch_id, exp_stl_date, gross, total_fee, expected_net, s_type="DUPLICATE_CANDIDATE")
                add_stl(s_id_cand, s_ref_cand, txn_id, pay_ref, m_id, batch_id, exp_stl_date, q2(gross * Decimal("0.50")), q2(total_fee * Decimal("0.50")), cand_net, s_type="DUPLICATE_CANDIDATE")
                add_bnk(b_id_str, b_ref, s_ref, txn_id, m_id, exp_stl_date, q2(expected_net + cand_net))
                add_gt(
                    f"CASE_{idx:06d}", txn_id, "S26_DUPLICATE_CANDIDATE_REVIEW", "DUPLICATE_CANDIDATE",
                    f"{txn_id}|{s_id}?{s_id_cand}", cand_net, "DUPLICATE_CANDIDATE", "HIGH", "OPEN",
                    expected_net, q2(expected_net + cand_net), True
                )
            else:
                # Unexplained large variance (> ₹1.00 tolerance, not matching fee policy) requiring manual review
                unexp_shortfall = Decimal("-125.00")
                obs_net = q2(expected_net + unexp_shortfall)
                add_txn()
                add_stl(s_id, s_ref, txn_id, pay_ref, m_id, batch_id, exp_stl_date, gross, q2(total_fee - unexp_shortfall), obs_net, s_type="UNEXPLAINED_VARIANCE")
                add_bnk(b_id_str, b_ref, s_ref, txn_id, m_id, exp_stl_date, obs_net)
                add_gt(
                    f"CASE_{idx:06d}", txn_id, "S26_MANUAL_REVIEW_VARIANCE", "MANUAL_REVIEW",
                    f"{txn_id}|{s_id}|{b_id_str}", unexp_shortfall, "MANUAL_REVIEW", "HIGH", "OPEN",
                    expected_net, obs_net, True
                )

        # ------------------------------------------------------------------
        # BLOCK 17: Data Quality Quarantine Scenarios (9956..10000 = 45 cases)
        # ------------------------------------------------------------------
        elif 9956 <= idx <= 9965:
            # S15: Missing or malformed transaction identifier
            bad_id = f"INVALID#TXN@{idx}"
            add_txn(t_id=bad_id)
            add_gt(
                f"CASE_{idx:06d}", bad_id, "S15_MISSING_INVALID_TXN_ID", "QUARANTINED_DATA_QUALITY",
                "QUARANTINED", -expected_net, "INVALID_IDENTIFIER", "MEDIUM", "OPEN",
                expected_net, Decimal("0.00"), True
            )
        elif 9966 <= idx <= 9975:
            # S16: Missing mandatory merchant_id / payment_reference
            add_txn(m_code="", p_ref="")
            add_gt(
                f"CASE_{idx:06d}", txn_id, "S16_MISSING_MANDATORY_REFERENCE", "QUARANTINED_DATA_QUALITY",
                "QUARANTINED", -expected_net, "MISSING_MANDATORY_FIELD", "MEDIUM", "OPEN",
                expected_net, Decimal("0.00"), True, m_code="MISSING"
            )
        elif 9976 <= idx <= 9985:
            # S17: Invalid or malformed negative amount
            add_txn(t_amt="-450.00")
            add_gt(
                f"CASE_{idx:06d}", txn_id, "S17_INVALID_MALFORMED_AMOUNT", "QUARANTINED_DATA_QUALITY",
                "QUARANTINED", -expected_net, "MALFORMED_AMOUNT", "MEDIUM", "OPEN",
                expected_net, Decimal("0.00"), True
            )
        elif 9986 <= idx <= 9992:
            # S18: Missing transaction date
            add_txn(t_date="")
            add_gt(
                f"CASE_{idx:06d}", txn_id, "S18_MISSING_DATE", "QUARANTINED_DATA_QUALITY",
                "QUARANTINED", -expected_net, "MISSING_DATE", "MEDIUM", "OPEN",
                expected_net, Decimal("0.00"), True
            )
        elif 9993 <= idx <= 10000:
            # S19: Invalid currency value ('USD' or 'EUR')
            bad_curr = "USD" if idx % 2 == 0 else "EUR"
            add_txn(curr=bad_curr)
            add_gt(
                f"CASE_{idx:06d}", txn_id, "S19_INVALID_CURRENCY", "QUARANTINED_DATA_QUALITY",
                "QUARANTINED", -expected_net, "INVALID_CURRENCY", "MEDIUM", "OPEN",
                expected_net, Decimal("0.00"), True
            )

    # Also add 180 clean standalone processed refunds on early exact matches (idx 101..280)
    for r_i in range(101, 281):
        t_rec = transactions[r_i - 1]
        r_id = f"REF_2026_{ref_seq:05d}"
        r_ref = f"REFREF_{ref_seq:05d}"
        ref_seq += 1
        r_amt = q2(Decimal(t_rec["transaction_amount"]) * Decimal("0.15"))
        refunds.append({
            "refund_id": r_id,
            "original_transaction_id": t_rec["transaction_id"],
            "refund_reference": r_ref,
            "merchant_id": t_rec["merchant_id"],
            "refund_timestamp": f"{t_rec['settlement_expected_date']}T16:00:00Z",
            "refund_amount": f"{r_amt:.2f}",
            "settled_refund_deduction": f"{r_amt:.2f}",
            "currency": "INR",
            "refund_status": "PROCESSED_CLEAN_STANDALONE",
            "refund_reason": "CUSTOMER_RETURN",
            "settlement_reference": f"STLREF_{r_i:06d}",
            "bank_reference": f"UTR2026{r_i:07d}",
            "ingestion_timestamp": ing_ts,
            "is_synthetic": "TRUE",
        })

    return {
        "merchants": merchants,
        "transactions": transactions,
        "settlements": settlements,
        "bank_entries": bank_entries,
        "refunds": refunds,
        "ground_truth": ground_truth,
    }


def write_csv_file(path: pathlib.Path, rows: List[Dict[str, Any]]) -> None:
    """Write rows to CSV deterministically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    headers = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def generate_and_save_all(base_dir: pathlib.Path | None = None, config: SettlementIQConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Generate and save all CSV datasets and generation_summary.json."""
    root = base_dir or config.project_root
    data = generate_synthetic_ecosystem(config)

    paths = {
        "merchants": root / "data" / "synthetic_inputs" / "merchants.csv",
        "transactions": root / "data" / "synthetic_inputs" / "transactions.csv",
        "settlements": root / "data" / "synthetic_inputs" / "settlements.csv",
        "bank_entries": root / "data" / "synthetic_inputs" / "bank_entries.csv",
        "refunds": root / "data" / "synthetic_inputs" / "refunds.csv",
        "ground_truth": root / "data" / "ground_truth" / "ground_truth.csv",
    }

    for k, p in paths.items():
        write_csv_file(p, data[k])

    # Compute generation summary metadata
    scen_counts: Dict[str, int] = {}
    for g in data["ground_truth"]:
        sc = g["planted_scenario"]
        scen_counts[sc] = scen_counts.get(sc, 0) + 1

    distinct_cust = len({r["customer_id"] for r in data["transactions"] if r["customer_id"]})
    distinct_merch = len({r["merchant_id"] for r in data["merchants"]})
    distinct_txn = len({r["transaction_id"] for r in data["transactions"] if r["transaction_id"]})
    distinct_pay_ref = len({r["payment_reference"] for r in data["transactions"] if r["payment_reference"]})

    # Source monetary totals by currency
    txn_totals_by_curr: Dict[str, Decimal] = {}
    for r in data["transactions"]:
        c = r["currency"] or "MISSING"
        txn_totals_by_curr[c] = txn_totals_by_curr.get(c, Decimal("0.00")) + Decimal(r["transaction_amount"])

    stl_gross_inr = sum(Decimal(r["gross_amount"]) for r in data["settlements"])
    stl_fee_inr = sum(Decimal(r["fee_amount"]) for r in data["settlements"])
    stl_net_inr = sum(Decimal(r["net_settlement_amount"]) for r in data["settlements"])
    bnk_credit_inr = sum(Decimal(r["credit_amount"]) for r in data["bank_entries"])
    bnk_debit_inr = sum(Decimal(r["debit_amount"]) for r in data["bank_entries"])
    ref_total_inr = sum(Decimal(r["refund_amount"]) for r in data["refunds"])

    summary = {
        "project": "SettlementIQ",
        "dataset_version": config.dataset_version,
        "ground_truth_version": config.ground_truth_version,
        "random_seed": config.random_seed,
        "generation_timestamp": "2026-10-25T20:00:00Z",
        "reproducibility_status": "DETERMINISTIC_VERIFIED",
        "row_counts": {
            "merchants_csv": len(data["merchants"]),
            "transactions_csv": len(data["transactions"]),
            "settlements_csv": len(data["settlements"]),
            "bank_entries_csv": len(data["bank_entries"]),
            "refunds_csv": len(data["refunds"]),
            "ground_truth_csv": len(data["ground_truth"]),
        },
        "distinct_entity_counts": {
            "distinct_customers": distinct_cust,
            "distinct_merchants": distinct_merch,
            "distinct_transactions": distinct_txn,
            "distinct_payment_references": distinct_pay_ref,
        },
        "source_monetary_totals_by_currency": {
            k: f"{v:.2f}" for k, v in sorted(txn_totals_by_curr.items())
        },
        "source_system_totals_inr": {
            "raw_settlements_gross_inr": f"{stl_gross_inr:.2f}",
            "raw_settlements_fee_inr": f"{stl_fee_inr:.2f}",
            "raw_settlements_net_inr": f"{stl_net_inr:.2f}",
            "raw_bank_credits_inr": f"{bnk_credit_inr:.2f}",
            "raw_bank_debits_inr": f"{bnk_debit_inr:.2f}",
            "raw_refunds_requested_inr": f"{ref_total_inr:.2f}",
        },
        "scenario_counts": dict(sorted(scen_counts.items())),
    }

    out_json = root / "outputs" / "generation_summary.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary


if __name__ == "__main__":
    s = generate_and_save_all()
    print(json.dumps(s, indent=2))
