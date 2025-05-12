from datetime import datetime
from ..instances import db
import uuid

class MockInterview(db.Model):
    __tablename__ = 'mock_interviews'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    
    company = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    experience_level = db.Column(db.String(50))  # Optional: intern, junior, mid, etc.

    chat_transcript = db.Column(db.Text)  # JSON or plaintext chat history
    ai_feedback = db.Column(db.Text)      # Feedback from Gemini
    score_communication = db.Column(db.Integer)
    score_content = db.Column(db.Integer)
    score_confidence = db.Column(db.Integer)
    total_score = db.Column(db.Float)     # Average of above scores

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Optional relationship to resume if needed
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'))

    user = db.relationship('User', backref=db.backref('mock_interviews', lazy=True))
    resume = db.relationship('Resume', backref=db.backref('mock_interviews', lazy=True))