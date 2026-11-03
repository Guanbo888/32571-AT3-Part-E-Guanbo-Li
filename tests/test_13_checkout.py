"""T013: empty-cart, guest and signed-in checkout entry."""
import re
import pytest
from playwright.sync_api import expect
from ui_helpers import visit, guest_checkout, register_account, add_cart


@pytest.mark.parametrize('scenario', ['T013-S01', 'T013-S02', 'T013-S03'])
def test_checkout_navigation(page, record, scenario):
    record['input'] = {'cart_product_id': None if scenario.endswith('01') else 40}
    if scenario.endswith('01'):
        # An empty cart must not expose a checkout address form.
        visit(page, 'checkout/checkout')
        expect(page).to_have_url(re.compile(r'route=checkout/cart'))
        expect(page.locator('#content')).to_contain_text('Your shopping cart is empty!')
        assert page.locator('#input-payment-firstname').count() == 0
        record['observations'] = {'checkout_blocked_for_empty_cart': True, 'address_form_count': 0}
    elif scenario.endswith('02'):
        guest_checkout(page)
        expect(page.locator('#input-payment-email')).to_be_visible()
        expect(page.locator('#button-guest')).to_be_visible()
        record['observations'] = {'guest_billing_form_visible': True, 'account_registration_required': False}
    else:
        # A registered customer should reach billing without guest/login choices.
        record['input']['account_email'] = register_account(page)
        add_cart(page)
        page.locator('#top-links a[title=Checkout]').click()
        expect(page).to_have_url(re.compile(r'route=checkout/checkout'))
        expect(page.locator('#button-payment-address')).to_be_visible()
        expect(page.locator('#input-payment-firstname')).to_be_visible()
        assert page.locator('a[href*="route=account/logout"]').count() > 0
        assert page.locator('input[name=account][value=guest]:visible').count() == 0
        record['observations'] = {'signed_in_billing_step_visible': True, 'authenticated_account': True}
