from flask_login import UserMixin
from datetime import datetime, timedelta
from ..instances import login_manager, db
import uuid

@login_manager.user_loader
def user_loader(user_id):
    if user_id:
        user = User.query.get(user_id)
        db.session.commit()
        return user
    return None

class SubscriptionTier(db.Model):
    __tablename__ = 'subscription_tiers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), nullable=False)
    stripe_price_id = db.Column(db.String(100), nullable=False)
    max_resumes = db.Column(db.Integer, nullable=False)
    max_applications = db.Column(db.Integer, nullable=False)
    monthly_interview_credits = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    tier_id = db.Column(db.String(36), db.ForeignKey('subscription_tiers.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(100))
    stripe_customer_id = db.Column(db.String(100))
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, cancelled, past_due, grace_period
    remaining_interview_credits = db.Column(db.Integer)
    grace_period_end = db.Column(db.DateTime)
    last_payment_date = db.Column(db.DateTime)
    next_payment_date = db.Column(db.DateTime)

    @property
    def is_active(self):
        """Check if subscription is active"""
        return self.status == 'active'

    @property
    def is_in_grace_period(self):
        """Check if subscription is in grace period"""
        if not self.grace_period_end:
            return False
        return datetime.utcnow() <= self.grace_period_end

    @property
    def days_remaining_in_grace_period(self):
        """Get days remaining in grace period"""
        if not self.grace_period_end:
            return 0
        delta = self.grace_period_end - datetime.utcnow()
        return max(0, delta.days)

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(12), nullable=False, unique=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)

    resumes = db.relationship('Resume', backref='owner', lazy=True, cascade="all, delete-orphan")
    job_applications = db.relationship('JobApp', backref='owner', lazy=True)
    
    # Fix: Remove the conflicting backref from here
    interviews = db.relationship('Interview', lazy=True)

    created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add subscription relationship
    subscription = db.relationship('UserSubscription', backref='user', lazy=True, uselist=False)
    
    @property
    def subscription_tier(self):
        """Safe way to get subscription tier"""
        if not self.subscription:
            self.create_free_subscription()
            db.session.refresh(self)
        return self.subscription.tier_id

    @property
    def max_resumes(self):
        """Get max resumes allowed for current tier"""
        if not self.subscription or not self.subscription.tier_id:
            return 1  # Free tier default
        if self.subscription.tier_id == 'diamond':
            return float('inf')  # Unlimited for Diamond
        elif self.subscription.tier_id == 'gold':
            return 5  # Gold tier gets 5 resumes
        return 1  # Free tier default

    @property 
    def max_applications(self):
        """Get max job applications allowed for current tier"""
        if not self.subscription or not self.subscription.tier_id:
            return 3  # Free tier default
        if self.subscription.tier_id == 'diamond':
            return float('inf')  # Unlimited for Diamond
        elif self.subscription.tier_id == 'gold':
            return 10  # Gold tier gets 10 applications
        return 3  # Free tier default

    @property
    def remaining_interviews(self):
        """Get remaining interview credits"""
        if not self.subscription:
            return 0
        if self.subscription.tier_id == 'diamond':
            return float('inf')  # Unlimited for Diamond
        elif self.subscription.tier_id == 'gold':
            return self.subscription.remaining_interview_credits or 0  # Gold tier gets 10 credits
        return self.subscription.remaining_interview_credits or 0  # Free tier gets 3 credits

    def can_create_resume(self):
        """Check if user can create a new resume"""
        if self.subscription and self.subscription.tier_id == 'diamond':
            return True  # Diamond tier can always create resumes
        return len(self.resumes) < self.max_resumes

    def can_create_application(self):
        """Check if user can create a new job application"""
        if self.subscription and self.subscription.tier_id == 'diamond':
            return True  # Diamond tier can always create applications
        return len(self.job_applications) < self.max_applications

    def can_start_interview(self):
        """Check if user can start a new interview"""
        if self.subscription and self.subscription.tier_id == 'diamond':
            return True  # Diamond tier can always start interviews
        return self.remaining_interviews > 0

    def create_free_subscription(self):
        if not self.subscription:
            try:
                # First check if free tier exists
                free_tier = SubscriptionTier.query.filter_by(name='Free').first()
                if not free_tier:
                    # Create free tier if it doesn't exist
                    free_tier = SubscriptionTier(
                        id='free',
                        name='Free',
                        stripe_price_id='',
                        max_resumes=1,
                        max_applications=3,
                        monthly_interview_credits=3,
                        price=0.00
                    )
                    db.session.add(free_tier)
                    db.session.flush()  # Flush to get the ID

                # Create subscription
                subscription = UserSubscription(
                    tier_id=free_tier.id,
                    remaining_interview_credits=3
                )
                # Set bidirectional relationship
                subscription.user = self
                self.subscription = subscription
                
                # Note: Don't commit here, let the caller handle the transaction
                db.session.add(subscription)
                db.session.flush()
                
            except Exception as e:
                db.session.rollback()
                raise e

    def can_upgrade_to_tier(self, target_tier):
        """Check if user can upgrade to the specified tier"""
        if not self.subscription:
            return True
            
        current_tier = self.subscription.tier_id
        
        # Prevent downgrades from higher tiers
        if current_tier == 'diamond' and target_tier in ['gold', 'free']:
            return False
        if current_tier == 'gold' and target_tier == 'free':
            return False
            
        return True

    def schedule_subscription_cancellation(self):
        """Schedule subscription to be cancelled at period end"""
        if not self.subscription or self.subscription.tier_id == 'free':
            return False

        try:
            if self.subscription.stripe_subscription_id:
                # Cancel Stripe subscription at period end
                stripe.Subscription.modify(
                    self.subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            
            # Mark subscription for cancellation
            self.subscription.status = 'canceling'
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def delete_account(self):
        """Delete user account and all associated data"""
        try:
            # Cancel any active subscriptions
            if self.subscription and self.subscription.stripe_subscription_id:
                try:
                    stripe.Subscription.delete(self.subscription.stripe_subscription_id)
                except:
                    pass  # Continue with deletion even if Stripe call fails

            # Delete all associated data
            # Note: cascade="all, delete-orphan" handles resumes
            # We need to manually delete other relationships
            for app in self.job_applications:
                db.session.delete(app)
            
            for interview in self.interviews:
                db.session.delete(interview)
                
            if self.subscription:
                db.session.delete(self.subscription)

            # Finally delete the user
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def handle_payment_failure(self):
        """Handle failed payment by setting grace period"""
        if self.subscription:
            self.subscription.status = 'past_due'
            self.subscription.grace_period_end = datetime.utcnow() + timedelta(days=7)  # 7-day grace period
            db.session.commit()

    def handle_subscription_expiration(self):
        """Handle subscription expiration after grace period"""
        if self.subscription and not self.subscription.is_in_grace_period:
            # Store the old tier for logging
            old_tier = self.subscription.tier_id
            
            # Create new free subscription
            self.create_free_subscription()
            
            # Log the downgrade
            current_app.logger.info(f"User {self.id} downgraded from {old_tier} to free tier due to payment failure")
            
            # Notify user
            # TODO: Implement notification system
            
            db.session.commit()

    def check_subscription_status(self):
        """Check and update subscription status"""
        if not self.subscription:
            return

        now = datetime.utcnow()

        # Check if subscription is past due
        if self.subscription.next_payment_date and now > self.subscription.next_payment_date:
            if not self.subscription.is_in_grace_period:
                self.handle_subscription_expiration()
            elif self.subscription.status != 'past_due':
                self.handle_payment_failure()

        # Check if cancelled subscription has ended
        if self.subscription.status == 'cancelled' and self.subscription.end_date and now > self.subscription.end_date:
            self.create_free_subscription()