# Checkout Test Source - Part E

Assigned scope: Guanbo Li, F13-F15.

The checkout checks are organised around the stages a customer reaches:

| Stage | Module | Scenarios |
|---|---|---:|
| Enter checkout | tests/test_13_checkout.py | 3 |
| Billing and delivery details | tests/test_14_address.py | 3 |
| Review and confirm an order | tests/test_15_confirmation.py | 3 |

Address validation checks both the warning and the retained values. Order checks
use Decimal arithmetic, then verify the success page and the emptied cart when
practice order submission is enabled.

## Getting started

Python 3.12 is required. Open a terminal in the extracted folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m pytest --collect-only -q
```

For Windows, replace the activation command with `.venv\Scripts\activate`.
The collection command should list nine scenarios without opening a browser.

## Execution choices

For checkout entry and address checks:

```sh
python -m pytest tests/test_13_checkout.py tests/test_14_address.py --operator "Guanbo Li"
```

For review checks without creating another practice order:

```sh
python -m pytest tests/test_15_confirmation.py --operator "Guanbo Li"
```

This second command validates the review, then reports the three confirmation
scenarios as Blocked/skipped because submission is disabled. It does not claim
that confirmation passed. The report contains the earlier three completed unpaid
practice orders; those records are not repeated by checking this package.

Only when a new practice submission is intended, use:

```sh
python -m pytest tests/test_15_confirmation.py --allow-demo-orders --slowmo 1000 --operator "Guanbo Li"
```

That command can create three additional unpaid test orders on
https://opencart.abstracta.us/. The helper checks the exact host and the Test-only
bank-transfer instructions. It never sends a payment. Use the actual runner's
name for `--operator`.

## Files and records

Each live execution writes its own evidence folder with source hashes, actual
environment details, screenshots and scenario results. The report's 24 October
selection was nine Pass results; this source packaging revision does not add new
website results.

The test modules match the report screenshots. The group fixture and UI support
are included with only the checkout dependencies and Part E scenario data.
Collection is read-only, and live runs require a runner name. See the short prompt
record for the assistance and packaging scope.
