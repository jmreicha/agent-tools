#!/usr/bin/env bash
# An app whose behavior specs are Gherkin features run by pytest-bdd.
set -euo pipefail
mkdir -p features tests
cat >features/login.feature <<'FEATURE'
Feature: Login
  Users sign in with an email and a password.

  Scenario: Correct password signs the user in
    Given a user "ana@example.com" with password "s3cret"
    When they sign in with "ana@example.com" and "s3cret"
    Then they see their dashboard

  Scenario: Wrong password is rejected without saying which part was wrong
    Given a user "ana@example.com" with password "s3cret"
    When they sign in with "ana@example.com" and "wrong"
    Then they see "Email or password is incorrect"
FEATURE
cat >tests/test_login.py <<'PY'
from pytest_bdd import scenarios

scenarios("../features/login.feature")
PY
printf 'pytest-bdd\n' >requirements-dev.txt
