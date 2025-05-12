from datetime import datetime
from ..instances import db
import uuid


class Resume(db.Model):
    __tablename__ = 'resume'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(12), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    skills = db.Column(db.String(500), nullable=False)
    analysis = db.Column(db.String(5000))
    optimized_version = db.Column(db.String(10000))

    work_experiences = db.relationship('WorkExperience', backref='resume', lazy=True, cascade="all, delete-orphan")
    education_history = db.relationship('EducationHistory', backref='resume', lazy=True, cascade="all, delete-orphan")
    certificates = db.relationship('Certification', backref='resume', lazy=True, cascade="all, delete-orphan")


class WorkExperience(db.Model):
    __tablename__ = 'work_experience'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resume.id'), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(500), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    is_present = db.Column(db.Boolean, nullable=False, default=True)
    duties = db.Column(db.String(500), nullable=False)


class EducationHistory(db.Model):
    __tablename__ = 'education_history'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resume.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    school = db.Column(db.String(250), nullable=False)
    location = db.Column(db.String(500), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    graduation_date = db.Column(db.DateTime)
    in_progress = db.Column(db.Boolean, nullable=False, default=False)
    achievements = db.Column(db.String(500), nullable=False)


class Certification(db.Model):
    __tablename__ = 'certification'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = db.Column(db.String(36), db.ForeignKey('resume.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(250), nullable=False)
    completed_date = db.Column(db.DateTime, nullable=False)
    expiry_date = db.Column(db.DateTime)