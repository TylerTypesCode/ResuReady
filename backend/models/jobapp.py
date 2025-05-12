from datetime import datetime
from ..instances import db
import uuid


class JobApp(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    company = db.Column(db.String(500), nullable=False)
    position = db.Column(db.String(250), nullable=False)
    location = db.Column(db.String(500), nullable=False)
    application_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum("Applied", "Interviewing", "Offered", "Rejected"))
    contact_person = db.Column(db.String(200))
    contact_email = db.Column(db.String(250))
    phone_number = db.Column(db.String(12))
    interview_date = db.Column(db.DateTime)
    interview_mode = db.Column(db.Enum("In-Person", "Video(Zoom)", "Phone"))
    follow_up_date = db.Column(db.DateTime)
    offer_date = db.Column(db.DateTime)
    salary_offer = db.Column(db.Float)
    job_type = db.Column(db.Enum("Full-Time", "Contact", "Part-Time"))
    application_link = db.Column(db.String(5000))
    notes = db.Column(db.String(5000))
    result = db.Column(db.Enum("Hired", "Rejected"))

