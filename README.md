# Auth Log Pipeline

## Overview

This project implements a structured pipeline for parsing, normalizing, storing, and analyzing Linux authentication logs (`auth.log`). The objective is to transform unstructured system logs into structured data and extract security-relevant signals such as brute-force attempts, while explicitly handling imperfect data.

---

## Data Source

This project uses sample authentication logs provided by Elastic:

https://github.com/elastic/examples/blob/master/Machine%20Learning/Security%20Analytics%20Recipes/suspicious_login_activity/data/auth.log

The dataset has been included locally in the `data/` directory for reproducibility.

### Important Note on Timestamps

The original dataset does not include year information.

During parsing, the year `2026` is artificially added to enable insertion into PostgreSQL.

Implications:

- Absolute timestamps are synthetic
- Relative ordering is preserved
- Long-term temporal analysis is unreliable
- Only short time-window analysis is meaningful

---

## Architecture

The pipeline follows a staged design:

read → parse → normalize → store → (next: signal → detect)

---

## Current Implementation (V2)

* Raw log ingestion from file
* Envelope parsing (timestamp, host, process, message)
* Event classification (authentication success/failure)
* Field extraction (user, IP, failure mode)
* Storage in PostgreSQL
* Idempotent ingestion (duplicate-safe)
* Ingestion observability (pipeline metrics)
* Basic analytical queries

---

## Ingestion Reliability

### Idempotency

The pipeline enforces deterministic ingestion:

- Unique constraint on:
  - (timestamp, host, process, raw_message)
- Duplicate entries are ignored via:
  - ON CONFLICT DO NOTHING

This guarantees:

- Repeated pipeline runs do not change results
- Aggregation queries remain stable

### Trade-off

If identical log entries occur legitimately, they are collapsed into one record, potentially reducing observed intensity of repeated events.

---

## Observability

Each pipeline run outputs:

Total lines: X
Parsed events: Y
Inserted events: Z

This enables detection of:

- Parsing loss → parsed < total
- Deduplication impact → inserted < parsed
- Ingestion stability across runs

---

## Project Structure

```
.
├── data/
│   └── auth.log
├── src/
│   ├── db.py
│   ├── parse_envelope.py
│   ├── read_raw.py
│   ├── run.py
│   └── insert_db.py
├── README.md
├── requirements.txt
└── LICENSE
```

---


---

## Data Model

Logs are stored in PostgreSQL with the following schema:

* timestamp (TIMESTAMP)
* host (TEXT)
* process (TEXT)
* event_type (TEXT)
* auth_outcome (TEXT)
* user_validity (TEXT)
* failure_mode (TEXT)
* user_name (TEXT)
* ip (INET)
* command (TEXT)
* raw_message (TEXT)

---

## Event Classification

The pipeline currently identifies:

* AUTH SUCCESS
  * Example: accepted public key login

* AUTH FAILURE
  * Invalid user attempts
  * Maximum authentication attempts exceeded
  * Pre-auth invalid user probes

* OTHER
  * Non-authentication logs (preserved but not classified)

---

## Observed Data Characteristics (Measured)

### Missing IP Addresses (Dominant)

- Approximately 5963 out of 6697 stored events (~89%) have NULL IP

Interpretation:

- Majority of events occur in pre-authentication phase
- Many events cannot be attributed to a source IP
- IP-based analysis operates on a limited subset of data

---

### Duplicate Log Entries

- 424 duplicate entries detected during ingestion
- Removed by uniqueness constraint

Implication:

- Source dataset contains duplicated logs
- Deduplication alters observed frequency of repeated events

---

### Behavioral Patterns per IP

#### Pure failure IPs
- High number of failures
- No successful logins
- Likely automated brute-force attempts

#### Mixed behavior IPs
- Combination of failures and successes
- Example: low failures, high successes

Interpretation:

- May represent legitimate users
- Or compromised accounts
- Breaks naive detection assumptions

---

### Pre-authentication Activity

- Significant number of failures without IP
- Typically associated with invalid user probing

Implication:

- Some attack activity is not attributable
- Detection models based solely on IP will miss this behavior

---

## Key Observations (from data)

* High concentration of failed login attempts from specific IPs
* Large number of invalid user probes (likely automated scanning)
* Many events without IP (pre-auth stage behavior)
* Very low success rate for external IPs

---

## Setup

### 1. Environment

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. PostgreSQL (Docker)

```
docker run --name auth-log-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=auth_logs \
  -p 127.0.0.1:5432:5432 \
  -d postgres:15
```

### 3. Run pipeline

```
python -m src.run
```

---

## Example Queries

Top IPs by failed authentication:

SELECT ip, COUNT()
FROM logs
WHERE auth_outcome = 'FAILURE'
GROUP BY ip
ORDER BY COUNT() DESC;

Failures vs successes per IP:

SELECT ip,
COUNT() FILTER (WHERE auth_outcome = 'FAILURE') AS failures,
COUNT() FILTER (WHERE auth_outcome = 'SUCCESS') AS successes
FROM logs
GROUP BY ip
ORDER BY failures DESC;

---

## Known Limitations

- IP-based analysis excludes ~89% of events
- Synthetic timestamps limit temporal validity
- Deduplication may suppress repeated identical attacks
- Pre-auth events cannot be attributed to a source

These limitations are preserved intentionally to reflect real-world imperfect data.

---

## Next Steps

* Construct time-window aggregation signals
* Build per-IP behavioral summaries
* Prepare data for detection logic
* Evaluate detection under imperfect conditions

---

## License

Apache License 2.0
