#!/usr/bin/env bash
# Three existing MADR records in docs/decisions, with their own sections and numbering.
set -euo pipefail
mkdir -p docs/decisions
adr() {
    cat >"docs/decisions/$1.md" <<MD
---
status: accepted
date: 2026-0$2-10
deciders: platform team
---

# $3

## Context and Problem Statement

$4

## Considered Options

* $5
* $6

## Decision Outcome

Chosen option: "$5", because $7.

### Consequences

* Good, because $7.
* Bad, because $8.
MD
}
adr 0001-use-markdown-architectural-decision-records 1 "Use Markdown Architectural Decision Records" "We need to record decisions where the code lives." "MADR" "Wiki pages" "it lives in the repo and gets reviewed in PRs" "people must learn the template"
adr 0002-use-postgres-for-app-data 3 "Use Postgres for app data" "The app needs relational data with transactions." "Postgres" "MySQL" "the team already runs it" "we run the upgrades"
adr 0003-deploy-with-github-actions 5 "Deploy with GitHub Actions" "Deploys are manual and take an hour." "GitHub Actions" "Jenkins" "it needs no server of our own" "secrets live in GitHub"
