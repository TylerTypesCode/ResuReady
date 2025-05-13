from flask import Blueprint, request, jsonify, render_template
from ..utils.ai_services import simulate_mock_interview
import uuid
from flask_login import login_required, current_user
from ..models.interview import Interview
from .. import db
from datetime import datetime

interview_bp = Blueprint('interview', __name__, url_prefix='/interviews')

# API endpoint for starting the mock interview
@interview_bp.route('/mock-interview', methods=['POST'])
def mock_interview():
    try:
        data = request.json
        company = data.get('company')
        position = data.get('position')
        resume_text = data.get('resume_text', '')
        user_response = data.get('user_response', '')
        session_id = data.get('session_id', '')
        question_count = data.get('question_count', 0)
        asked_questions = data.get('asked_questions', [])

        if not company or not position:
            return jsonify({'error': 'company and position are required'}), 400

        # Force interview completion if question limit reached
        force_complete = question_count >= 7

        # If no session_id, start new interview
        if not session_id:
            result = simulate_mock_interview(
                company=company,
                position=position,
                resume_text=resume_text,
                is_start=True,
                asked_questions=asked_questions
            )
            return jsonify({
                'session_id': str(uuid.uuid4()),
                'interviewer_response': result['interviewer_response'],
                'is_complete': False
            })
        
        # Continue existing interview
        result = simulate_mock_interview(
            company=company,
            position=position,
            resume_text=resume_text,
            user_response=user_response,
            session_id=session_id,
            force_complete=force_complete,
            asked_questions=asked_questions
        )
        
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# New route to serve the Mock Interview UI
@interview_bp.route('/new_interview', methods=['GET'])
def new_interview():
    return render_template('interview/mock_interview.html')

@interview_bp.route('/save', methods=['POST'])
@login_required
def save_interview():
    try:
        data = request.json
        
        # Format conversation as a list of message objects
        conversation = []
        for idx, msg in enumerate(data['conversation']):
            if idx % 2 == 0:  # Even indices are interviewer messages
                conversation.append({
                    'role': 'interviewer',
                    'content': msg
                })
            else:  # Odd indices are user responses
                conversation.append({
                    'role': 'user',
                    'content': msg
                })
        
        # Create new interview record
        interview = Interview(
            user_id=current_user.id,
            company=data['company'],
            position=data['position'],
            session_id=data['session_id'],
            conversation=conversation,  # Stored as structured JSON
            results=data['results'],
            date=datetime.utcnow()
        )
        
        db.session.add(interview)
        db.session.commit()
        
        return jsonify({'message': 'Interview saved successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@interview_bp.route('/')
@login_required
def dashboard():
    interviews = Interview.query.filter_by(user_id=current_user.id)\
                              .order_by(Interview.date.desc())\
                              .all()
    return render_template('interview/dashboard.html', interviews=interviews)

@interview_bp.route('/view/<interview_id>')
@login_required
def view(interview_id):
    interview = Interview.query.filter_by(id=interview_id, user_id=current_user.id).first_or_404()
    return render_template('interview/view.html', interview=interview)