# Auth Log Pipeline

## Overview

This project implements a structured pipeline for parsing, normalizing, storing, and analyzing Linux authentication logs (`auth.log`). The objective is to transform unstructured system logs into structured data and extract security-relevant signals such as brute-force attempts.

## Data Source

This project uses sample authentication logs provided by Elastic:

https://github.com/elastic/examples/blob/master/Machine%20Learning/Security%20Analytics%20Recipes/suspicious_login_activity/data/auth.log

The dataset has been included locally in the `data/` directory for reproducibility.

---

## Architecture

The pipeline follows a staged design:

read → parse → normalize → store → (next: detect)

### Current Implementation (V1)

* Raw log ingestion from file
* Envelope parsing (timestamp, host, process, message)
* Event classification (authentication success/failure)
* Field extraction (user, IP, failure mode)
* Storage in PostgreSQL
* Basic analytical queries

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

```
SELECT ip, COUNT(*)
FROM logs
WHERE auth_outcome = 'FAILURE'
GROUP BY ip
ORDER BY COUNT(*) DESC;
```

Failures vs successes per IP:

```
SELECT ip,
       COUNT(*) FILTER (WHERE auth_outcome = 'FAILURE') AS failures,
       COUNT(*) FILTER (WHERE auth_outcome = 'SUCCESS') AS successes
FROM logs
GROUP BY ip
ORDER BY failures DESC;
```

---

## Next Steps

* Implement detection layer (brute-force detection)
* Add time-window analysis (e.g., failures per 5 minutes)
* Generate structured security alerts
* Improve parsing coverage for additional log types

---

## License

Apache License 2.0
