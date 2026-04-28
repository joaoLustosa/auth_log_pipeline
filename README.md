# Auth Log Pipeline

## Overview

This project implements a minimal pipeline for parsing Linux authentication logs into structured data for analysis and detection.

The system ingests raw log lines, extracts relevant fields, classifies events, and stores them in a PostgreSQL database for querying.

## Objectives

* Parse semi-structured auth logs (e.g., sshd, sudo)
* Normalize events into a structured schema
* Enable SQL-based detection (e.g., failed attempts per IP)

## Data Source

Sample log data is derived from public datasets provided by Elastic, licensed under the Apache License 2.0.

## Stack

* Python (parsing, ETL)
* PostgreSQL (storage, querying)
* Pandas (data handling)
* SQLAlchemy (DB interface)

## Status

Environment setup and database integration in progress.
