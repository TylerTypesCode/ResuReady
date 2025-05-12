from flask import Blueprint, render_template, redirect, url_for, request, flash
from ..utils.ai_services import get_job_market_trends
from flask_login import current_user, login_required
from ..utils.weather import get_current_weather
from ..instances import db
from ..models.user import User
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    user = current_user

    weather = get_current_weather(user.city)
    trends = get_job_market_trends()
    print(f"GOT TRENDS: {trends}")

    # Correct usage of datetime and formatting
    date_time = datetime.utcnow()
    date_time_str = date_time.strftime('%Y-%m-%d %H:%M:%S')

    return render_template('user/dashboard.html', weather=weather, trends=trends, date_time=date_time_str)


    