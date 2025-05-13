from flask import Blueprint, render_template
from flask_login import login_required
from ..models.user import User, UserSubscription, SubscriptionTier
from ..utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    subscription_stats = {
        'free': User.query.join(UserSubscription).filter(UserSubscription.tier_id == 'free').count(),
        'gold': User.query.join(UserSubscription).filter(UserSubscription.tier_id == 'gold').count(),
        'diamond': User.query.join(UserSubscription).filter(UserSubscription.tier_id == 'diamond').count()
    }
    return render_template('admin/dashboard.html', users=users, stats=subscription_stats)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/subscriptions')
@login_required
@admin_required
def subscriptions():
    subscriptions = UserSubscription.query.all()
    return render_template('admin/subscriptions.html', subscriptions=subscriptions)