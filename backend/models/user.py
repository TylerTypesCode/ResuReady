from flask_login import UserMixin
from datetime import datetime
from ..instances import db
import uuid


class User(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(12), nullable=False, unique=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)

    #resumes = db.relationship('Resume', backref='owner', lazy=True)
    #job_apps = db.relationship('JobApps', backref='owner', lazy=True)
    #interviews = db.relationship('Interviews', backref='owner', lazy=True)

    created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
