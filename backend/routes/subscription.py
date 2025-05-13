from flask import Blueprint, flash, request, jsonify, render_template, current_app, redirect, url_for
from flask_login import login_required, current_user
from ..models.user import User, UserSubscription, SubscriptionTier
from ..instances import db
import stripe
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

subscription_bp = Blueprint('subscription', __name__, url_prefix='/subscription')

# Remove this line since we'll use current_app.config instead
# api_key = os.getenv("STRIPE_SECRET_KEY")

def init_stripe(app):
    """Initialize Stripe configuration"""
    stripe.api_key = app.config['STRIP_SECRET_KEY']

TIER_DATA = {
    'free': {
        'name': 'Free',
        'price': 0,
        'stripe_price_id': None
    },
    'gold': {
        'name': 'Gold',
        'monthly': {
            'price': 14.99,
            'stripe_price_id': 'price_1RO964EHTsLg21IfMgSum8Ta'
        },
        'annual': {
            'price': 149.00,
            'stripe_price_id': 'price_1RO972EHTsLg21IfCT7GZehq'
        },
        'features': [
            '5 Resumes',
            '10 Job Applications',
            '10 Monthly Interview Credits'
        ]
    },
    'diamond': {
        'name': 'Diamond',
        'monthly': {
            'price': 29.99,
            'stripe_price_id': 'price_1RO97bEHTsLg21Ifeo9CqI6S'
        },
        'annual': {
            'price': 299.00,
            'stripe_price_id': 'price_1RO99BEHTsLg21IfhRo4OhYg'
        },
        'features': [
            'All Gold Features',
            'Unlimited Interview Credits',
            'AI Resume Reviews & Job Match'
        ]
    }
}

@subscription_bp.route('/upgrade', methods=['GET'])
@login_required
def upgrade():
    return render_template('subscription/upgrade.html', 
                         tiers=TIER_DATA,
                         current_tier=current_user.subscription.tier_id if current_user.subscription else 'free',
                         stripe_public_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))

@subscription_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    tier = request.form.get('tier')
    billing_period = request.form.get('billing_period', 'monthly')

    if not current_user.can_upgrade_to_tier(tier):
        return jsonify({
            'error': 'Cannot downgrade to a lower tier. Please contact support for assistance.'
        }), 400

    if tier not in TIER_DATA:
        return jsonify({'error': 'Invalid tier selected.'}), 400

    if tier == 'free':
        return jsonify({'error': 'Free plan does not require checkout.'}), 400

    tier_data = TIER_DATA[tier]
    if billing_period not in tier_data:
        return jsonify({'error': 'Invalid billing period.'}), 400

    price_id = tier_data[billing_period]['stripe_price_id']

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            allow_promotion_codes=True,
            metadata={
                'user_id': current_user.id,
                'tier': tier,
                'billing_period': billing_period
            },
            success_url=request.host_url + 'subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'subscription/cancel',
        )
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 403

# Update the webhook endpoint to use the correct key
@subscription_bp.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, 
            sig_header, 
            current_app.config['STRIPE_WEBHOOK_SECRET']  # Changed from STRIPE_PUBLISHABLE_KEY
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        if event['type'] == 'invoice.payment_failed':
            # Handle payment failure
            subscription = event['data']['object']
            user = User.query.filter_by(
                stripe_customer_id=subscription['customer']
            ).first()
            if user:
                user.handle_payment_failure()

        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            user_sub = UserSubscription.query.filter_by(
                stripe_subscription_id=subscription['id']
            ).first()
            
            if user_sub:
                # Update subscription dates and status
                user_sub.status = subscription['status']
                user_sub.next_payment_date = datetime.fromtimestamp(subscription['current_period_end'])
                user_sub.last_payment_date = datetime.fromtimestamp(subscription['current_period_start'])
                
                if subscription['cancel_at_period_end']:
                    user_sub.status = 'cancelled'
                    user_sub.end_date = datetime.fromtimestamp(subscription['cancel_at'])
                
                db.session.commit()

        return jsonify({'status': 'success'})
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 400

@subscription_bp.route('/success')
@login_required
def success():
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect(url_for('user.dashboard'))
        
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == "paid":
            # Get subscription details
            stripe_subscription = stripe.Subscription.retrieve(session.subscription)
            current_app.logger.debug(f"Retrieved subscription: {stripe_subscription}")
            
            # Get the price ID from the first subscription item
            subscription_item = stripe_subscription['items']['data'][0]
            price_id = subscription_item['price']['id']
            current_app.logger.debug(f"Retrieved price_id: {price_id}")
            
            # Find the tier based on price ID
            selected_tier = None
            selected_period = None
            for tier, data in TIER_DATA.items():
                if tier == 'free':
                    continue
                for period in ['monthly', 'annual']:
                    if period in data and data[period]['stripe_price_id'] == price_id:
                        selected_tier = tier
                        selected_period = period
                        break
                if selected_tier:
                    break

            if selected_tier:
                try:
                    # Update user's subscription
                    if not current_user.subscription:
                        user_sub = UserSubscription(user_id=current_user.id)
                    else:
                        user_sub = current_user.subscription

                    user_sub.tier_id = selected_tier
                    user_sub.stripe_subscription_id = stripe_subscription['id']
                    user_sub.stripe_customer_id = stripe_subscription['customer']
                    user_sub.status = stripe_subscription['status']
                    
                    # Fix: Access timestamps from subscription_item
                    user_sub.start_date = datetime.fromtimestamp(subscription_item['current_period_start'])
                    user_sub.end_date = datetime.fromtimestamp(subscription_item['current_period_end'])
                    
                    # Set correct interview credits based on tier
                    if selected_tier == 'gold':
                        user_sub.remaining_interview_credits = 10  # Gold gets 10 credits
                    elif selected_tier == 'diamond':
                        user_sub.remaining_interview_credits = 999999  # Unlimited
                    else:
                        user_sub.remaining_interview_credits = 3  # Free gets 3 credits

                    current_app.logger.info(f"Updating subscription for user {current_user.id} to {selected_tier}")
                    db.session.add(user_sub)
                    db.session.commit()
                    current_app.logger.info("Subscription updated successfully")

                    flash(f'Successfully upgraded to {selected_tier.title()} plan!', 'success')
                    return render_template('subscription/success.html', 
                                        tier=selected_tier,
                                        billing_period=selected_period)
                except Exception as e:
                    current_app.logger.error(f"Database error: {str(e)}")
                    db.session.rollback()
                    raise
            else:
                error_msg = f"Could not determine tier from price ID: {price_id}"
                current_app.logger.error(error_msg)
                raise ValueError(error_msg)

    except Exception as e:
        current_app.logger.error(f"Error verifying subscription: {str(e)}")
        flash('There was an error processing your subscription. Please contact support.', 'error')
    
    return redirect(url_for('subscription.upgrade'))

@subscription_bp.route('/cancel')
@login_required
def cancel():
    return render_template('subscription/cancel.html')

@subscription_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    try:
        if current_user.schedule_subscription_cancellation():
            flash('Your subscription will be cancelled at the end of the billing period.', 'success')
        else:
            flash('No active subscription to cancel.', 'error')
    except Exception as e:
        current_app.logger.error(f"Error cancelling subscription: {str(e)}")
        flash('An error occurred while cancelling your subscription.', 'error')
    
    return redirect(url_for('user.dashboard'))

@subscription_bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        password = request.form.get('password')
        if not current_user.check_password(password):
            flash('Incorrect password.', 'error')
            return redirect(url_for('user.settings'))

        try:
            current_user.delete_account()
            logout_user()
            flash('Your account has been successfully deleted.', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            current_app.logger.error(f"Error deleting account: {str(e)}")
            flash('An error occurred while deleting your account.', 'error')
            
    return render_template('user/delete_account.html')

def fulfill_subscription(session):
    """Helper function to fulfill the subscription after successful payment"""
    try:
        # Get subscription details from session
        subscription = stripe.Subscription.retrieve(session.subscription)
        customer = stripe.Customer.retrieve(session.customer)
        
        # Get the price ID to determine tier
        price_id = subscription.items.data[0].price.id
        tier_id = next(
            (tier for tier, data in TIER_DATA.items() 
             if data['stripe_price_id'] == price_id),
            None
        )
        
        if not tier_id:
            raise ValueError("Invalid price ID")

        # Update or create user subscription
        user_sub = UserSubscription.query.filter_by(
            user_id=current_user.id
        ).first() or UserSubscription(user_id=current_user.id)
        
        user_sub.tier_id = tier_id
        user_sub.stripe_subscription_id = subscription.id
        user_sub.stripe_customer_id = customer.id
        user_sub.status = 'active'
        user_sub.start_date = datetime.fromtimestamp(subscription.current_period_start)
        user_sub.end_date = datetime.fromtimestamp(subscription.current_period_end)
        user_sub.remaining_interview_credits = TIER_DATA[tier_id]['monthly_interview_credits']
        
        db.session.add(user_sub)
        db.session.commit()
        
    except Exception as e:
        current_app.logger.error(f"Error fulfilling subscription: {str(e)}")
        raise