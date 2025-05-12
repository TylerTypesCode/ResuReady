from datetime import datetime
from ..instances import db
import uuid

class Interview(db.Model):
    __tablename__ = 'interviews'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    conversation = db.Column(db.JSON)
    results = db.Column(db.JSON)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company': self.company,
            'position': self.position,
            'session_id': self.session_id,
            'conversation': self.conversation,
            'results': self.results,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S')
        }