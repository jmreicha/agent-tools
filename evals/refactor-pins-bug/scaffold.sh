#!/usr/bin/env bash
# invoice_total uses > where the others use >=, so a naive merge changes its result at exactly 100.
set -euo pipefail
cat >pricing.py <<'PY'
def checkout_total(subtotal):
    if subtotal >= 100:
        return round(subtotal * 0.9, 2)
    return subtotal


def invoice_total(subtotal):
    if subtotal > 100:
        return round(subtotal * 0.9, 2)
    return subtotal


def quote_total(subtotal):
    if subtotal >= 100:
        return round(subtotal * 0.9, 2)
    return subtotal
PY
cat >test_pricing.py <<'PY'
from pricing import checkout_total, invoice_total, quote_total


def test_small_orders_pay_full_price():
    assert checkout_total(50) == 50
    assert invoice_total(50) == 50
    assert quote_total(50) == 50


def test_large_orders_get_ten_percent_off():
    assert checkout_total(200) == 180
    assert invoice_total(200) == 180
    assert quote_total(200) == 180
PY
