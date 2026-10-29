# SettlementIQ — Comprehensive Data Dictionary

## 1. Source CSV Files & Validated Database Entities

### 1.1 `merchants.csv` / `validated.merchants` (25 Rows)
| Field Name | Data Type | Key / Nullability | Allowed Values / Validation Rule | Business Description |
| :--- | :--- | :--- | :--- | :--- |
| `merchant_id` | `VARCHAR(32)` | `PRIMARY KEY`, `NOT NULL` | `^MERCH_[0-9]{4}$` | Unique merchant identifier (`MERCH_1001`..`MERCH_1025`) |
| `merchant_name` | `VARCHAR(150)` | `NOT NULL` | Non-empty string | Legal business name of synthetic merchant |
| `merchant_category` | `VARCHAR(100)` | `NOT NULL` | Retail, SaaS, Grocery, Logistics, etc. | Industry vertical |
| `onboarding_date` | `DATE` | `NOT NULL` | `YYYY-MM-DD` | Date merchant joined the payment platform |
| `merchant_status` | `VARCHAR(30)` | `NOT NULL` | `ACTIVE`, `SUSPENDED`, `CLOSED` | Current operational status |
| `settlement_frequency` | `VARCHAR(16)` | `NOT NULL` | `T+1`, `T+2` | Contractual payout cycle |
| `contractual_fee_rate` | `NUMERIC(8,4)` | `NOT NULL` | `0.0000` to `0.1500` | Contracted Merchant Discount Rate (MDR) |
| `contractual_fixed_fee` | `NUMERIC(18,2)` | `NOT NULL` | `>= 0.00` | Fixed gateway fee per transaction in INR |
| `currency` | `CHAR(3)` | `NOT NULL` | `'INR'` | Approved settlement currency |
| `region` | `VARCHAR(40)` | `NOT NULL` | `North`, `South`, `East`, `West`, `Central` | Geographic operating region |
| `operational_classification` | `VARCHAR(50)` | `NOT NULL` | `Tier1_Standard`, `Tier2_Monitored`, `Tier3_HighExposure` | Operational monitoring tier |
| `default_payment_gateway` | `VARCHAR(80)` | `NOT NULL` | `AxisPay_Gateway`, `HDFC_SmartHub`, `ICICI_PaySeal`, `RazorFlow_India` | Primary acquiring gateway |
| `settlement_sla_days` | `INTEGER` | `NOT NULL` | `1` or `2` | Contractual business-day SLA |
| `is_synthetic` | `BOOLEAN` | `NOT NULL` | `TRUE` | Explicit synthetic-data marker |

### 1.2 `transactions.csv` / `validated.transactions` (9,955 Raw / 9,885 Validated Rows)
| Field Name | Data Type | Key / Nullability | Allowed Values / Validation Rule | Business Description |
| :--- | :--- | :--- | :--- | :--- |
| `transaction_id` | `VARCHAR(64)` | `PRIMARY KEY`, `NOT NULL` | `^TXN_[0-9]{4}_[0-9]{6}$` | Unique switch transaction ID (Quarantined if invalid: `S15`) |
| `customer_id` | `VARCHAR(64)` | `NOT NULL` | `^CUST_[0-9]{5}$` | Synthetic customer ID (`3,200` distinct customers) |
| `merchant_id` | `VARCHAR(32)` | `FOREIGN KEY`, `NOT NULL` | Must exist in `merchants` | Merchant reference (Quarantined if blank: `S16`) |
| `payment_reference` | `VARCHAR(64)` | `NOT NULL` | `^PAYREF_[0-9]+$` | Gateway payment reference (Quarantined if blank: `S16`) |
| `order_reference` | `VARCHAR(64)` | `NOT NULL` | `^ORD_.*$` | Merchant order reference (May repeat on split orders: `S11`) |
| `transaction_timestamp` | `TIMESTAMPTZ` | `NOT NULL` | ISO-8601 UTC timestamp | Exact capture timestamp |
| `transaction_date` | `DATE` | `NOT NULL` | `YYYY-MM-DD` | Capture calendar date (Quarantined if blank: `S18`) |
| `transaction_amount` | `NUMERIC(18,2)` | `NOT NULL` | `> 0.00` | Gross transaction value (Quarantined if `<= 0`: `S17`) |
| `currency` | `CHAR(3)` | `NOT NULL` | `'INR'` | Transaction currency (Quarantined if `USD`/`EUR`: `S19`) |
| `payment_method` | `VARCHAR(40)` | `NOT NULL` | `UPI`, `CREDIT_CARD`, `DEBIT_CARD`, `NET_BANKING` | Payment instrument |
| `payment_status` | `VARCHAR(30)` | `NOT NULL` | `CAPTURED` | Switch capture status |
| `payment_gateway` | `VARCHAR(80)` | `NOT NULL` | Gateway identifier | Acquiring payment gateway |
| `settlement_expected_date` | `DATE` | `NOT NULL` | `YYYY-MM-DD` | Expected payout date (`transaction_date` + SLA business days) |
| `transaction_fee` | `NUMERIC(18,2)` | `NOT NULL` | `>= 0.00` | Expected total fee (`MDR + 18% GST`) |
| `expected_net_amount` | `NUMERIC(18,2)` | `NOT NULL` | `> 0.00` | Expected net payout (`transaction_amount - transaction_fee`) |
| `source_system` | `VARCHAR(80)` | `NOT NULL` | `CORE_SWITCH_LEDGER` | Originating ledger system |
| `record_version` | `INTEGER` | `NOT NULL` | `1` | Record schema version |
