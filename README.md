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

### Important Limation

- Logs do not contain year
- Year `2026` is injected during parsing

Implications:

- absolute time is artificial
- relative ordering is preserved
- only short-window analysis is valid

---

## Architecture

Pipeline stages:

read → parse → normalize → store → signal → detect → evaluate → stress-test

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
- Window: 5 minutes (fixed, aligned to clock boundaries)

### Metrics

- failures
- successes
- users_targeted

Each row represents:

> behavior of one IP in one 5-minute window

### Constraints

- Only IP-based logs included
- Majority of data excluded
- No idle windows represented
- Strong dependence on time window alignment

---

## Statistical Model

### Baseline (Original Data)

- Mean failures ≈ 3.86
- Stddev ≈ 6.47

Observation:

- stddev > mean → highly skewed distribution
- bursts dominate variance

---

### Anomaly Score

z = (failures − mean) / stddev

---

## Observed Behavior

### Strong Attacks (Detected Reliably)

- 20–46 failures per window
- z-score > 2–6

Interpretation:
- clear brute-force bursts
- robust to moderate noise

---

### Moderate Activity (Unstable)

- 8–15 failures
- z ≈ 0.6–1.5

Interpretation:
- highly sensitive to thresholds
- sensitive to data loss and time shifts

---

### Weak Activity (Missed)

- < 8 failures
- z < 1

Interpretation:
- treated as normal
- indistinguishable from background noise

---

## Rule-Based Detection

### Definition


failures ≥ N within 5-minute window


### Threshold Behavior

- N ≥ 20 → high precision, low recall
- N ≥ 10 → moderate balance
- N ≥ 5 → high recall, high false positives

---

## Model Comparison

### Z-score

- adaptive
- sensitive to variance
- misses moderate attacks

### Rule-based

- interpretable
- consistent
- threshold-dependent

---

## Evaluation Results

### Ground Truth

Attack window:

- IP: `34.204.227.175`
- Peak: 46 failures in one window

---

### Baseline Detection

| Method   | TP | FP | FN |
|----------|----|----|----|
| N ≥ 5    | 1  | 49 | 0  |
| N ≥ 10   | 1  | 7  | 0  |
| N ≥ 20   | 1  | 6  | 0  |
| z > 2    | 1  | 6  | 0  |

---

## Failure Injection Experiments

### Experiment A — Log Loss (30%)

#### Effect on Attack

- 46 → 33
- 40 → 25

#### Detection

| Method   | TP | FP | FN |
|----------|----|----|----|
| N ≥ 5    | 1  | 37 | 0  |
| N ≥ 10   | 1  | 7  | 0  |
| N ≥ 20   | 1  | 4  | 0  |
| z > 2    | 1  | 5  | 0  |

#### Findings

- extreme attacks remain detectable
- moderate signals degrade significantly
- threshold crossings decrease non-linearly

---

### Experiment B — Delayed Ingestion

#### Case 1 — +2 Minutes

- 46 + 40 → 86 (merged into single window)

#### Case 2 — +1 Minute

- 46 + 40 → 73 + 13 (skewed redistribution)

#### Detection (both cases)

| Method   | TP | FP | FN |
|----------|----|----|----|
| N ≥ 5    | 1  | ~49 | 0 |
| N ≥ 10   | 1  | ~6–7 | 0 |
| N ≥ 20   | 1  | ~4–5 | 0 |
| z > 2    | 1  | ~4–5 | 0 |

---

## Critical Findings

### 1. Time Windowing Is Not Stable

Small timestamp shifts produce:

- burst merging
- burst splitting
- asymmetric redistribution

Detection depends on alignment, not behavior.

---

### 2. Detection Is Not Time-Invariant


f(events) ≠ f(events + Δt)


Small temporal shifts significantly change signal representation.

---

### 3. Aggregation Artifacts Distort Reality

- moderate bursts can appear as extreme attacks (merge)
- strong bursts can weaken (split or loss)
- system may overestimate or underestimate severity

---

### 4. Moderate Attacks Are Fragile

Combination of:

- time misalignment
- log loss

causes:

- 10–15 failures → 5–9 failures
- drop below thresholds
- become undetectable

---

### 5. System Detects Alignment, Not Behavior

The system is effectively detecting:

> coincidence between attack bursts and fixed window boundaries

Not:

> intrinsic attacker behavior

---

## Evasion Path (Demonstrated)

An attacker can evade detection by:

- operating in moderate intensity (8–15 failures)
- spreading activity near window boundaries
- relying on natural log loss / ingestion noise

Result:

- signal fragmentation
- threshold bypass
- statistical invisibility

---

## Failure Modes (Updated)

### Statistical Model

- fails under high variance
- insensitive to moderate deviations
- unstable under distribution shifts

### Rule-Based Model

- fails below threshold
- highly sensitive to aggregation artifacts
- non-linear degradation under noise

### System-Level

- time alignment dependency
- no continuity modeling across windows
- ignores 89% of data (NULL IP events)

---

## Known Blind Spots

- pre-auth attacks (no IP)
- distributed attacks across IPs
- low-and-slow attacks
- time-distributed attacks
- cross-window behavioral continuity

---

## Final Conclusion

The system:

### Works for:
- high-intensity brute-force bursts
- clean, aligned data conditions

### Fails for:
- realistic attacker behavior
- noisy or incomplete data
- temporal misalignment

### Core Limitation:

> Fixed-window aggregation creates unstable and misleading representations of behavior.

---

## Next Step

Redesign detection around:

- time-robust signals
- continuity across windows
- reduced dependence on arbitrary thresholds
- resilience to missing data

---

## License

Apache License 2.0
