"""T015: three synthetic unpaid practice orders; no funds are sent."""
import pytest
from ui_helpers import prepare_confirmation, verify_order_review, submit_demo_order


@pytest.mark.parametrize('scenario', ['T015-S01', 'T015-S02', 'T015-S03'])
def test_order_confirmation(page, record, scenario, pytestconfig):
    items = {'T015-S01': [(40, 1)], 'T015-S02': [(40, 2)], 'T015-S03': [(40, 1), (43, 1)]}[scenario]
    record['input'] = {'items': items, 'addresses': prepare_confirmation(page, items), 'payment_method': 'bank_transfer (Test)', 'funds_sent': False}
    review = verify_order_review(page, items)
    # Validate identities and arithmetic before creating the unpaid practice record.
    review_name = scenario + '-review.png'
    page.screenshot(path=str(pytestconfig.run_dir / review_name), full_page=True)
    record['review_screenshot'] = review_name
    record['observations'] = {'review': review}
    # The helper checks real order success, captures it and verifies the cleared cart.
    result = submit_demo_order(page, pytestconfig.getoption('--allow-demo-orders'), pytestconfig.run_dir / scenario)
    record['observations'].update(result)
