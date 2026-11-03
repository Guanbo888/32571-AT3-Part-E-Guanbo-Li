"""Checkout preparation and amount checks for Part E."""

import re

import uuid

from decimal import Decimal

from urllib.parse import urlparse

import pytest

from playwright.sync_api import expect

BASE = 'https://opencart.abstracta.us/index.php?route='

PRODUCTS = {40: 'iPhone', 43: 'MacBook', 28: 'HTC Touch HD'}

def visit(page, route):
    page.goto(BASE + route, wait_until='domcontentloaded', timeout=60000)
    expect(page.locator('#content')).to_be_visible()

def register_account(page):
    """Create a dedicated synthetic account; this is prerequisite work, not Part B."""
    visit(page, 'account/register')
    email = 'a3-de-' + uuid.uuid4().hex[:18] + '@example.net'
    values = {'firstname': 'Automation', 'lastname': 'Test', 'email': email,
              'telephone': '0000000000', 'password': 'PracticeTest42!', 'confirm': 'PracticeTest42!'}
    for field, value in values.items():
        page.locator('#input-' + field).fill(value)
    page.locator('input[name=agree]').check()
    page.locator('input[type=submit]').click()
    expect(page).to_have_url(re.compile(r'route=account/success'))
    expect(page.locator('#content')).to_contain_text('Your new account has been successfully created')
    return email

def product(page, product_id):
    visit(page, f'product/product&product_id={product_id}')
    expect(page.locator('#content h1')).to_have_text(PRODUCTS[product_id])
    model = page.locator('#content li').filter(has_text='Product Code:').inner_text().split(':', 1)[1].strip()
    price_text = page.locator('#content .col-sm-4 ul.list-unstyled h2').inner_text()
    return {'id': product_id, 'name': PRODUCTS[product_id], 'model': model, 'price_text': price_text}

def add_cart(page, product_id=40, quantity=1):
    info = product(page, product_id)
    page.locator('#input-quantity').fill(str(quantity))
    page.locator('#button-cart').click()
    expect(page.locator('.alert-success')).to_be_visible()
    return info

def guest_checkout(page, items=((40, 1),)):
    for pid, qty in items:
        add_cart(page, pid, qty)
    visit(page, 'checkout/cart')
    page.locator('#content .buttons a').filter(has_text='Checkout').click()
    expect(page).to_have_url(re.compile(r'route=checkout/checkout'))
    page.locator('input[name=account][value=guest]').check()
    page.locator('#button-account').click()
    expect(page.locator('#input-payment-firstname')).to_be_visible()

def fill_address(page, prefix='payment', first='Automation', separate=False):
    data = {'firstname': first, 'lastname': 'Test', 'address-1': ('2' if prefix == 'shipping' else '1') + ' Automation Test Road',
            'city': 'Testville', 'postcode': '00000'}
    if prefix == 'payment':
        data.update(email='a3-guest-' + uuid.uuid4().hex[:16] + '@example.net', telephone='0000000000')
    for field, value in data.items():
        page.locator('#input-' + prefix + '-' + field).fill(value)
    page.locator('#input-' + prefix + '-country').select_option(label='United States')
    page.locator('#input-' + prefix + '-zone').select_option(label='California')
    if prefix == 'payment':
        page.locator('#collapse-payment-address input[name=shipping_address]').set_checked(not separate)
    return data

def accept_address(page, separate=False):
    data = fill_address(page, separate=separate)
    page.locator('#button-guest').click()
    shipping = None
    if separate:
        expect(page.locator('#input-shipping-firstname')).to_be_visible()
        shipping = fill_address(page, 'shipping', first='Delivery')
        page.locator('#button-guest-shipping').click()
    expect(page.locator('#button-shipping-method')).to_be_visible()
    return {'billing': data, 'delivery': shipping or data}

def prepare_confirmation(page, items):
    guest_checkout(page, items)
    address = accept_address(page)
    page.locator('#collapse-shipping-method input[value="flat.flat"]').check()
    page.locator('#button-shipping-method').click()
    expect(page.locator('#button-payment-method')).to_be_visible()
    # This practice store exposes a non-payment bank-transfer method labelled Test.
    page.locator('#collapse-payment-method input[value=bank_transfer]').check()
    page.locator('#collapse-payment-method input[name=agree]').check()
    page.locator('#button-payment-method').click()
    expect(page.locator('#button-confirm')).to_be_visible()
    expect(page.locator('.collapsing')).to_have_count(0)
    return address

def amount(text):
    return Decimal(re.sub(r'[^0-9.]', '', text))

def verify_order_review(page, items):
    table = page.locator('#collapse-checkout-confirm table')
    expect(table.locator('tbody tr')).to_have_count(len(items))
    rows = []
    for pid, qty in items:
        row = table.locator('tbody tr').filter(has=page.get_by_role('link', name=PRODUCTS[pid], exact=True))
        expect(row).to_have_count(1)
        cells = row.locator('td')
        assert int(cells.nth(2).inner_text()) == qty
        unit, line = amount(cells.nth(3).inner_text()), amount(cells.nth(4).inner_text())
        assert unit * qty == line, 'Review line amount does not match quantity times unit price'
        rows.append({'product_id': pid, 'name': PRODUCTS[pid], 'quantity': qty, 'unit_price': str(unit), 'line_total': str(line)})
    foot = [(tr.locator('td').first.inner_text().strip(' :'), amount(tr.locator('td').last.inner_text()))
            for tr in table.locator('tfoot tr').all()]
    totals = dict(foot)
    assert totals['Sub-Total'] == sum(Decimal(r['line_total']) for r in rows)
    assert totals['Total'] == sum(v for k, v in foot if k not in ['Total', 'Sub-Total']) + totals['Sub-Total']
    return {'rows': rows, 'totals': {k: str(v) for k, v in foot}}

def submit_demo_order(page, allow_demo_orders, evidence_prefix):
    """Never submit on another host or with actual bank instructions."""
    if not allow_demo_orders:
        pytest.skip('Demo order submission requires explicit --allow-demo-orders')
    assert urlparse(page.url).hostname == 'opencart.abstracta.us'
    payment = page.locator('#collapse-checkout-confirm').inner_text()
    assert 'Bank Transfer Instructions' in payment and re.search(r'\nTest\s*\n', payment)
    # No transfer is made. The practice order contains only synthetic details.
    page.locator('#button-confirm').click()
    expect(page).to_have_url(re.compile(r'route=checkout/success'), timeout=20000)
    expect(page.locator('#content')).to_contain_text('Your order has been placed')
    success_url = page.url
    # Capture the actual success page before checking the emptied cart.
    page.screenshot(path=str(evidence_prefix) + '-success.png', full_page=True)
    page.locator('#content').screenshot(path=str(evidence_prefix) + '-success-content.png')
    success_text = page.locator('#content').inner_text()
    evidence_prefix.with_name(evidence_prefix.name + '-success.html').write_text(page.content())
    visit(page, 'checkout/cart')
    expect(page.locator('#content')).to_contain_text('Your shopping cart is empty!')
    assert page.locator('#content input[name^=quantity]').count() == 0
    return {'success_url': success_url, 'success_text': success_text, 'success_screenshot': evidence_prefix.name + '-success-content.png',
            'cart_cleared': True, 'payment_sent': False, 'order_type': 'synthetic unpaid practice order'}
