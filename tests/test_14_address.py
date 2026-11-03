"""T014: required billing fields and separate delivery details."""
import pytest
from playwright.sync_api import expect
from ui_helpers import guest_checkout, accept_address, fill_address


@pytest.mark.parametrize('scenario', ['T014-S01', 'T014-S02', 'T014-S03'])
def test_billing_delivery(page, record, scenario):
    guest_checkout(page)
    if scenario.endswith('02'):
        # Correct rejection of the missing first name is a passing negative test.
        record['input'] = fill_address(page, first='')
        page.locator('#button-guest').click()
        expect(page.locator('#collapse-payment-address .text-danger')).to_contain_text('First Name must be between 1 and 32 characters!')
        assert not page.locator('#button-shipping-method').is_visible()
        expect(page.locator('#input-payment-city')).to_have_value('Testville')
        record['observations'] = {'first_name_validation': True, 'advanced_to_shipping_method': False, 'other_fields_retained': True}
    else:
        addresses = accept_address(page, separate=scenario.endswith('03'))
        record['input'] = addresses
        expect(page.locator('#input-payment-address-1')).to_have_value(addresses['billing']['address-1'])
        if scenario.endswith('03'):
            # Keep billing and delivery values distinct after checkout advances.
            expect(page.locator('#input-shipping-address-1')).to_have_value(addresses['delivery']['address-1'])
            assert addresses['billing']['address-1'] != addresses['delivery']['address-1']
        record['observations'] = {'delivery_method_step_visible': True, 'distinct_addresses': scenario.endswith('03'), 'address_values_retained': True}
