# cogs/utilities.py

import uuid
import re
import config
import requests
from urllib.parse import urlencode

def generate_unique_id():
    """
    Generates a unique ID for assignments.
    """
    return str(uuid.uuid4())[:8]

def format_message(message):
    """
    Formats a message string (placeholder function).
    """
    # Implement any formatting needed
    return message

def validate_input(input_str, pattern):
    """
    Validates input string against a regex pattern.
    """
    return re.match(pattern, input_str)

def create_payment_links(payment_id, amount):
    """
    Generates secure payment links for PayPal and Stripe.
    """
    amount_str = "{:.2f}".format(amount)
    
    # PayPal Payment Link
    paypal_params = {
        'cmd': '_xclick',
        'business': config.PAYPAL_BUSINESS_EMAIL,
        'item_name': f'Assignment Payment {payment_id}',
        'amount': amount_str,
        'currency_code': 'USD',
        'invoice': payment_id,
        'notify_url': config.PAYPAL_NOTIFY_URL,  # PayPal IPN URL
        'return': config.PAYPAL_RETURN_URL,
        'cancel_return': config.PAYPAL_CANCEL_URL,
    }
    paypal_link = f"https://www.paypal.com/cgi-bin/webscr?{urlencode(paypal_params)}"
    
    # Stripe Payment Link
    stripe_session_url = create_stripe_checkout_session(payment_id, amount)
    
    return {'paypal': paypal_link, 'stripe': stripe_session_url}

def verify_payment(payment_id):
    """
    Verifies the payment status with the payment gateways.
    """
    # Placeholder for actual verification logic
    payment_successful = True
    return payment_successful

def create_stripe_checkout_session(payment_id, amount):
    """
    Creates a Stripe Checkout Session and returns the session URL.
    """
    import stripe
    stripe.api_key = config.STRIPE_API_KEY

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Assignment Payment {payment_id}',
                    },
                    'unit_amount': int(amount * 100),  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=config.STRIPE_SUCCESS_URL,
            cancel_url=config.STRIPE_CANCEL_URL,
            metadata={'payment_id': payment_id},
        )
        return session.url
    except Exception as e:
        print(f"Error creating Stripe Checkout Session: {e}")
        return None
