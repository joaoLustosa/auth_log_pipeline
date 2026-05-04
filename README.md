# Auth Log Pipeline

## Overview

This project implements a structured pipeline for parsing, normalizing, storing, and analyzing Linux authentication logs (`auth.log`).

The objective is to transform unstructured system logs into structured data and extract security-relevant signals while preserving real-world imperfections. The system emphasizes:

- ingestion reliability
- data consistency
- observability
- statistical reasoning under imperfect data
- explicit modeling limitations

---

## Data Source

This project uses sample authentication logs provided by Elastic:

https://github.com/elastic/examples/blob/master/Machine%20Learning/Security%20Analytics%20Recipes/suspicious_login_activity/data/auth.log

The dataset is included locally under `data/auth.log`.

### Timestamp Limitation

The dataset does not include year information. During parsing, the year `2026` is injected.

Implications:

- absolute time is synthetic
- relative ordering is preserved
- only short time-window analysis is meaningful

---

## Architecture

Pipeline stages:

read → parse → normalize → store → signal → (next: detect)

---

## Current Implementation

- Raw ingestion from file
- Envelope parsing (timestamp, host, process, message)
- Event classification (authentication success/failure)
- Field extraction (user, IP, failure mode)
- PostgreSQL storage
- Idempotent ingestion (duplicate-safe)
- Ingestion observability (pipeline metrics)
- Time-window signal construction
- Statistical baseline and anomaly scoring (z-score)

---

## Ingestion Reliability

### Idempotency

- Unique constraint on `(timestamp, host, process, raw_message)`
- Duplicate entries ignored via `ON CONFLICT DO NOTHING`

Guarantees:

- deterministic ingestion
- stable aggregations

Trade-off:

- repeated identical events are collapsed, reducing observed intensity

---

## Observability

Each run outputs:


Total lines: X
Parsed events: Y
Inserted events: Z


Enables:

- detection of parsing loss
- measurement of deduplication impact
- ingestion consistency validation

---

## Data Model

- timestamp (TIMESTAMP)
- host (TEXT)
- process (TEXT)
- event_type (TEXT)
- auth_outcome (TEXT)
- user_validity (TEXT)
- failure_mode (TEXT)
- user_name (TEXT)
- ip (INET)
- command (TEXT)
- raw_message (TEXT)

---

## Signal Construction

### Definition

Unit of analysis:

- Entity: IP
- Time window: 5 minutes
- Metrics:
  - failures
  - successes
  - users targeted

Each row represents:

> behavior of one IP within a 5-minute interval

### Constraints

- Only events with IP are included
- ~89% of logs are excluded (no IP)
- Idle windows are not represented

---

## Statistical Modeling

### Baseline

Computed over all IP-window observations:

- Mean failures ≈ 3.86
- Standard deviation ≈ 6.45

Observation:

- stddev > mean → highly skewed distribution

---

### Anomaly Score

Z-score is used:

z = (failures − mean) / stddev

Interpretation:

- high z-score → deviation from typical activity
- near zero → typical behavior

---

## Observed Behavior

### Strong Signals (Detected Well)

- High-intensity bursts:
  - 30–46 failures within 5 minutes
  - z-scores > 4

Interpretation:

- clear brute-force attacks
- strong separation from baseline

---

### Moderate Activity (Ambiguous)

- 15–20 failures per window
- z ≈ 1.8–2.5

Interpretation:

- could be smaller attacks
- classification depends on threshold

---

### Weak Signals (Missed)

- 5–10 failures per window
- z < 1

Interpretation:

- treated as normal behavior
- may include slow brute-force attempts

---

## Model Limitations

### 1. High Variance

- extreme bursts inflate stddev
- reduces sensitivity to moderate anomalies

---

### 2. Global Baseline

- one mean/stddev for all IPs
- ignores per-IP behavior differences

Effect:

- attackers influence baseline
- moderate attacks appear normal

---

### 3. Active-Only Windows

- only windows with activity are modeled
- no representation of idle periods

Effect:

- no contrast between activity and silence

---

### 4. Data Exclusion

- ~89% of events lack IP
- pre-auth activity is ignored

Effect:

- blind to certain attack types

---

## Threshold Sensitivity

Example:

- z > 2 → detects only large bursts
- z > 1 → detects more activity but increases noise

Conclusion:

- thresholds are not inherently meaningful
- must be justified by observed behavior

---

## Evasion Implications (Preliminary)

The current model can be bypassed by:

### Low-and-slow attack
- spreading attempts across time
- staying within statistical baseline

### Distributed attack
- splitting attempts across multiple IPs
- avoiding per-IP thresholds

### Mixed behavior
- combining successful and failed logins
- mimicking legitimate activity

---

## Known Data Imperfections

- Missing IP addresses (~89%)
- Duplicate log entries (removed during ingestion)
- Mixed benign and suspicious behavior
- Synthetic timestamps

These are preserved intentionally.

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

## Next Steps

- Implement rule-based detection (N failures in T window)
- Compare rule-based vs statistical detection
- Evaluate false positives and false negatives
- Perform explicit evasion analysis
- Introduce failure injection

---

## License

Apache License 2.0
