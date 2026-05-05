# Auth Log Pipeline

## Overview

This project implements a structured pipeline for parsing, normalizing, storing, and analyzing Linux authentication logs (`auth.log`).

The objective is to build a system that:

- ingests and structures noisy log data
- constructs behavioral signals
- detects anomalous authentication patterns
- explicitly models failure, evasion, and data imperfections

This is not a “working script”, but a system designed to be **defensible under scrutiny**.

---

## Data Source

Elastic sample authentication logs:

https://github.com/elastic/examples/blob/master/Machine%20Learning/Security%20Analytics%20Recipes/suspicious_login_activity/data/auth.log

### Important Limitation

- Logs do not contain year
- Year `2026` is injected during parsing

Implications:

- absolute time is artificial
- relative ordering is preserved
- only short-window analysis is valid

---

## Architecture

Pipeline stages:

read → parse → normalize → store → signal → detect → evaluate

---

## Current Implementation

### Ingestion Layer
- raw log reading
- parsing into structured envelope
- event classification (AUTH SUCCESS / FAILURE / OTHER)
- field extraction (user, IP, failure mode)

### Storage Layer
- PostgreSQL storage
- idempotent ingestion via unique constraint
- duplicate suppression (`ON CONFLICT DO NOTHING`)

### Observability
- total lines processed
- parsed events
- inserted events

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

## Data Imperfections

- ~89% of events have NULL IP
- duplicate logs (removed during ingestion)
- mixed benign and malicious behavior
- missing fields (user/IP)
- synthetic timestamps

These are not cleaned.

---

## Signal Construction

### Unit of Analysis

- Entity: IP
- Window: 5 minutes
- Metrics:
  - failures
  - successes
  - users_targeted

Each row represents:

> behavior of one IP in one 5-minute window

### Constraints

- Only IP-based logs included
- Majority of data excluded
- No idle windows represented

---

## Statistical Model

### Baseline

- Mean failures ≈ 3.86
- Stddev ≈ 6.45

Observation:

- stddev > mean → highly skewed distribution

---

### Anomaly Score

z = (failures − mean) / stddev

Interpretation:

- high z → deviation from dataset norm
- low z → typical activity

---

## Observed Behavior

### Strong Attacks (Detected Well)

- 20–46 failures per window
- z-score > 2–6

Interpretation:
- clear brute-force bursts

---

### Moderate Activity (Ambiguous)

- 10–20 failures
- z ≈ 1–2

Interpretation:
- uncertain classification
- threshold-dependent

---

### Weak Activity (Missed)

- 5–10 failures
- z < 1

Interpretation:
- treated as normal
- may include low-and-slow attacks

---

## Rule-Based Detection

### Definition


failures ≥ N within 5-minute window


### Threshold Behavior

- N ≥ 20 → high precision, low recall
- N ≥ 10 → moderate balance
- N ≥ 5 → high recall, low precision

---

## Model Comparison

### Z-score

- adaptive
- influenced by variance
- misses moderate attacks

### Rule-based

- interpretable
- consistent
- threshold-sensitive

---

## Key Trade-off

- statistical → adaptive but unstable under skew
- rule-based → stable but arbitrary

---

## Evasion Analysis

### Low-and-slow attack
- keep attempts below threshold

### Distributed attack
- spread attempts across IPs

### Mixed behavior
- combine success + failure

### Time spreading
- avoid spikes

---

## Failure Modes

### Statistical model fails when:
- variance is high
- attackers inflate baseline

### Rule-based fails when:
- attacker operates below threshold

### Both fail when:
- attack is distributed or slow

---

## Known Blind Spots

- pre-auth attacks (no IP)
- idle behavior (not modeled)
- user-level targeting incomplete

---

## Evaluation (Next Step)

Will include:

- manually defined attack window
- normal window
- comparison of:
  - true positives
  - false positives
  - threshold sensitivity

---

## Next Steps

- Ground truth labeling
- Detection evaluation
- Formal evasion analysis
- Failure injection (pipeline degradation)

---

## License

Apache License 2.0
