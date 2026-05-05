# Auth Log Pipeline

## Overview

This project implements a structured pipeline for parsing, normalizing, storing, and analyzing Linux authentication logs (`auth.log`).

The objective is to build a system that:

- ingests and structures noisy log data
- constructs behavioral signals
- detects anomalous authentication patterns
- explicitly models failure, evasion, and data imperfections

This is not a “working script”, but a system designed to be **defensible under scrutiny**, including demonstrating where and why it fails.

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

read → parse → normalize → store → signal → detect → evaluate → evade → degrade

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

### Metrics

- failures
- successes
- users_targeted

Each row represents:

> behavior of one IP in one 5-minute window

### Constraints

- Only IP-based logs included
- Majority of data excluded (~89%)
- No idle windows represented
- No temporal continuity modeled

---

## Statistical Model

### Baseline

- Mean failures ≈ 3.86
- Stddev ≈ 6.47

Observation:

- stddev > mean → highly skewed distribution
- variance dominated by burst activity

---

### Anomaly Score

z = (failures − mean) / stddev

In practice:


z > 2 ≈ failures ≥ ~20


This collapses z-score into an **extreme-event detector**, not a general anomaly model.

---

## Detection Models

### Rule-Based


failures ≥ N per 5-minute window


Thresholds tested:

- N ≥ 5
- N ≥ 10
- N ≥ 20

---

### Statistical (Z-score)


z > 2


---

## Evaluation Results

Total windows: 181
Ground truth: single high-intensity attack window (46 failures)

| Method   | TP | FP | FN |
|----------|----|----|----|
| N ≥ 5    | 1  | 49 | 0  |
| N ≥ 10   | 1  | 7  | 0  |
| N ≥ 20   | 1  | 6  | 0  |
| z > 2    | 1  | 6  | 0  |

---

## Key Findings

### 1. All models detect extreme bursts

- 40–46 failures
- trivial detection case
- not a meaningful benchmark

---

### 2. No stable threshold exists

- N ≥ 5 → high recall, unusable FP (~27%)
- N ≥ 10 → moderate balance
- N ≥ 20 / z > 2 → high precision, low recall

This is not tuning failure. It is **feature insufficiency**.

---

### 3. Critical failure region identified


failures: 8–15
z_score: < 2


Properties:

- frequent in dataset
- invisible to z-score
- inconsistently detected by rules
- indistinguishable from benign activity

---

### 4. Z-score is structurally ineffective

Due to high variance:

- moderate attacks collapse into “normal”
- model behaves like a fixed high threshold

---

### 5. System is memoryless

Detection operates on:

> one IP, one window, isolated

It does not model:

- temporal continuity
- repeated behavior
- cumulative activity

---

### 6. Dataset bias is structural

- ~89% of failures excluded (no IP)
- detection operates on partial observability
- blind spots are systemic, not incidental

---

## Evasion Analysis (Empirical)

### 1. Low-and-Slow (Single IP)

Observed:

- 16 failures across 3 windows
- never exceeds threshold

Effect:

- bypasses N ≥ 10, N ≥ 20, z-score
- only detectable in high-FP regime

---

### 2. Moderate Burst Masking

Observed:

- 8–9 failures per window
- z < 1

Effect:

- invisible to statistical model
- below practical rule thresholds

---

### 3. Distributed Attack

Observed:

- windows with 20–33 total failures
- no single IP dominant

Effect:

- no per-IP detection triggered
- system misses high-volume attack

---

### 4. Temporal Smearing

Observed pattern:

- repeated sub-threshold activity across windows

Effect:

- no accumulation
- no detection

---

### 5. Pre-auth Blind Spot

Measured:

- 178 failures with NULL IP

Effect:

- completely excluded from detection
- attacker can operate fully undetected

---

## Cross-Model Failure Matrix

| Attack Type           | N ≥ 5 | N ≥ 10 | N ≥ 20 | z > 2 |
|----------------------|------|--------|--------|-------|
| High burst           | ✓    | ✓      | ✓      | ✓     |
| Moderate burst       | ✓    | ✗      | ✗      | ✗     |
| Low-and-slow         | ✓    | ✗      | ✗      | ✗     |
| Distributed          | ✗    | ✗      | ✗      | ✗     |
| Temporal smear       | ✗    | ✗      | ✗      | ✗     |
| Pre-auth             | ✗    | ✗      | ✗      | ✗     |

---

## Structural Limitations

The system fails due to:

- IP-only modeling (no cross-entity reasoning)
- lack of temporal state
- variance-sensitive statistics
- partial observability (missing IPs)

These are design constraints, not implementation errors.

---

## Failure Injection (Next Step)

The system will be stress-tested under:

### Log Loss
- simulate 20–30% data removal
- evaluate degradation in detection

### Delayed Ingestion
- shift timestamps across windows
- observe fragmentation of bursts

Goal:

> quantify how quickly detection collapses under realistic system failure

---

## Project Philosophy

This project does not aim to:

- maximize detection rates
- optimize metrics in isolation

It aims to:

> build a system whose behavior — including its failures — is measurable, explainable, and defensible.

---

## License

Apache License 2.0
