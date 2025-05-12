from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user
from ..models.jobapp import JobApp
from ..instances import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('main/index.html')

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.route('/features')
def features():
    return render_template('main/features.html')

@main_bp.route('/pricing')
def pricing():
    return render_template('main/pricing.html')

@main_bp.route('/fix_db')
def fix_db():
    job_apps = JobApp.query.all()
    for job in job_apps:
        db.session.delete(job)
    return render_template('user/dashboard.html')