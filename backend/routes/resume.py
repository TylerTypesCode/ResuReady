from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response, send_file
from flask_login import current_user, login_required
from ..models.resume import Resume, WorkExperience, EducationHistory, Certification
from ..utils.ai_services import analyze_resume_with_ai
from ..utils.serializers import serialize_resume
from datetime import datetime
from ..instances import db
import json

resume_bp = Blueprint('resumes', __name__, url_prefix='/resumes')

# 📄 Dashboard (List Resumes)
@resume_bp.route('/')
@login_required
def dashboard():
    resumes = Resume.query.filter_by(owner_id=current_user.id).all()
    return render_template('resumes/dashboard.html', resumes=resumes)

# ➕ Create Resume
@resume_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        try:
            # --- Personal Info ---
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phone_number = request.form.get('phone_number')
            address = request.form.get('address')
            city = request.form.get('city')
            date_of_birth_str = request.form.get('date_of_birth')
            skills = request.form.get('skills')

            if not first_name or not last_name or not email:
                flash('First Name, Last Name, and Email are required.', 'danger')
                return redirect(url_for('resumes.create'))

            date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date() if date_of_birth_str else None

            # --- Create Resume ---
            resume = Resume(
                owner_id=current_user.id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                address=address,
                city=city,
                date_of_birth=date_of_birth,
                skills=skills
            )
            db.session.add(resume)
            db.session.flush()

            # --- Work Experience ---
            for i in range(10):
                position = request.form.get(f'work_experiences[{i}][position]')
                if position:
                    company = request.form.get(f'work_experiences[{i}][company]')
                    location = request.form.get(f'work_experiences[{i}][location]')
                    duties = request.form.get(f'work_experiences[{i}][duties]')
                    start_date_str = request.form.get(f'work_experiences[{i}][start_date]')
                    end_date_str = request.form.get(f'work_experiences[{i}][end_date]')
                    is_present = request.form.get(f'work_experiences[{i}][is_present]') == 'on'

                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

                    work = WorkExperience(
                        resume_id=resume.id,
                        position=position,
                        company=company,
                        location=location,
                        duties=duties,
                        start_date=start_date,
                        end_date=end_date,
                        is_present=is_present
                    )
                    db.session.add(work)

            # --- Education History ---
            for i in range(10):
                title = request.form.get(f'education_history[{i}][title]')
                if title:
                    school = request.form.get(f'education_history[{i}][school]')
                    location = request.form.get(f'education_history[{i}][location]')
                    achievements = request.form.get(f'education_history[{i}][achievements]')
                    start_date_str = request.form.get(f'education_history[{i}][start_date]')
                    graduation_date_str = request.form.get(f'education_history[{i}][graduation_date]')
                    in_progress = request.form.get(f'education_history[{i}][in_progress]') == 'on'

                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
                    graduation_date = datetime.strptime(graduation_date_str, '%Y-%m-%d') if graduation_date_str else None

                    edu = EducationHistory(
                        resume_id=resume.id,
                        title=title,
                        school=school,
                        location=location,
                        achievements=achievements,
                        start_date=start_date,
                        graduation_date=graduation_date,
                        in_progress=in_progress
                    )
                    db.session.add(edu)

            # --- Certifications ---
            for i in range(10):
                cert_title = request.form.get(f'certifications[{i}][title]')
                if cert_title:
                    issuer = request.form.get(f'certifications[{i}][issuer]')
                    completed_date_str = request.form.get(f'certifications[{i}][completed_date]')
                    expiry_date_str = request.form.get(f'certifications[{i}][expiry_date]')

                    completed_date = datetime.strptime(completed_date_str, '%Y-%m-%d') if completed_date_str else None
                    expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d') if expiry_date_str else None

                    cert = Certification(
                        resume_id=resume.id,
                        title=cert_title,
                        issuer=issuer,
                        completed_date=completed_date,
                        expiry_date=expiry_date
                    )
                    db.session.add(cert)

            # --- Finalize ---
            db.session.commit()
            flash('Resume created successfully!', 'success')
            return redirect(url_for('resumes.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating resume: {str(e)}', 'danger')
            return redirect(url_for('resumes.create'))

    return render_template('resumes/create.html')

# ✏ Edit Resume
@resume_bp.route('/edit/<string:resume_id>', methods=['GET', 'POST'])
@login_required
def edit(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.owner_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('resumes.dashboard'))

    if request.method == 'POST':
        resume.title = request.form.get('title')
        resume.content = request.form.get('content')
        db.session.commit()
        flash('Resume updated successfully.', 'success')
        return redirect(url_for('resumes.dashboard'))

    return render_template('resumes/edit.html', resume=resume)

# 🗑 Delete Resume
@resume_bp.route('/delete/<string:resume_id>', methods=['POST'])
@login_required
def delete(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.owner_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('resumes.dashboard'))

    db.session.delete(resume)
    db.session.commit()
    flash('Resume deleted.', 'success')
    return redirect(url_for('resumes.dashboard'))

# 🤖 AI Analysis
# Route for Resume Analysis
@resume_bp.route('/<string:resume_id>/analyze', methods=['GET'])
@login_required
def analyze(resume_id):
    resume = Resume.query.filter_by(id=resume_id, owner_id=current_user.id).first()
    if not resume:
        flash('Resume not found.', 'danger')
        return redirect(url_for('resumes.dashboard'))

    # Get resume content
    resume_content = serialize_resume(resume)

    # Analyze resume with AI (assumed to return dict or str)
    analysis_result = analyze_resume_with_ai(resume_content)

    # Ensure formatted_analysis is always a string for logs, APIs, etc.
    if isinstance(analysis_result, dict):
        formatted_analysis = json.dumps(analysis_result, indent=2)
        parsed_analysis = analysis_result  # already dict
    else:
        formatted_analysis = analysis_result  # fallback for plain text error message
        parsed_analysis = {}  # fallback empty dict to avoid breaking the template

    return render_template('resumes/analysis.html', analysis=parsed_analysis, resume=resume)

# 📄 View Resume
@resume_bp.route('/view/<string:resume_id>')
@login_required
def view(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.owner_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('resumes.dashboard'))

    work_experiences = WorkExperience.query.filter_by(resume_id=resume.id).all()
    education_histories = EducationHistory.query.filter_by(resume_id=resume.id).all()
    certifications = Certification.query.filter_by(resume_id=resume.id).all()

    return render_template('resumes/view.html', resume=resume,
                           work_experiences=work_experiences,
                           education_histories=education_histories,
                           certifications=certifications)

# 📥 Export Resume as JSON
@resume_bp.route('/export/<string:resume_id>', methods=['GET'])
@login_required
def export_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.owner_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('resumes.dashboard'))

    try:
            # Export Resume as JSON
            resume_data = {
                'first_name': resume.first_name,
                'last_name': resume.last_name,
                'email': resume.email,
                'phone_number': resume.phone_number,
                'address': resume.address,
                'city': resume.city,
                'date_of_birth': resume.date_of_birth.strftime('%Y-%m-%d'),
                'skills': resume.skills,
                'work_experience': [{'position': work.position, 'company': work.company, 'location': work.location,
                                     'start_date': work.start_date.strftime('%Y-%m-%d'),
                                     'end_date': work.end_date.strftime('%Y-%m-%d') if work.end_date else None,
                                     'is_present': work.is_present, 'duties': work.duties} for work in resume.work_experiences]
            }

            response = make_response(json.dumps(resume_data, indent=4))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename={resume.first_name}_{resume.last_name}_resume.json'
            return response

    except Exception as e:
        flash(f'Error exporting resume: {str(e)}', 'danger')
        return redirect(url_for('resumes.dashboard'))
    
# 📥 Import Resume from JSON
@resume_bp.route('/import', methods=['POST'])
@login_required
def import_resume():
    file = request.files.get('file')
    if not file:
        flash("No file uploaded.", "danger")
        return redirect(url_for('resumes.dashboard'))

    try:
        # Handle JSON import
        if file.filename.endswith('.json'):
            data = json.load(file)

            # Check if the top-level structure is a list (multiple resumes) or a dict (single resume)
            if isinstance(data, list):  # If it's a list of resumes
                for resume_data in data:
                    resume = Resume(
                        owner_id=current_user.id,
                        first_name=resume_data['first_name'],
                        last_name=resume_data['last_name'],
                        email=resume_data['email'],
                        phone_number=resume_data['phone_number'],
                        address=resume_data['address'],
                        city=resume_data['city'],
                        date_of_birth=datetime.strptime(resume_data['date_of_birth'], '%Y-%m-%d').date(),
                        skills=resume_data['skills']
                    )
                    db.session.add(resume)
                    db.session.commit()  # Commit to generate resume.id

                    # Add Work Experience from JSON
                    for work_data in resume_data.get('work_experience', []):
                        work = WorkExperience(
                            resume_id=resume.id,  # Now resume_id is properly assigned
                            position=work_data['position'],
                            company=work_data['company'],
                            location=work_data['location'],
                            start_date=datetime.strptime(work_data['start_date'], '%Y-%m-%d'),
                            end_date=datetime.strptime(work_data['end_date'], '%Y-%m-%d') if work_data.get('end_date') else None,
                            is_present=work_data['is_present'],
                            duties=work_data['duties']
                        )
                        db.session.add(work)

                db.session.commit()  # Commit the work experiences
                flash('Resume imported successfully!', 'success')

            elif isinstance(data, dict):  # If it's a single resume (e.g. {"resume": {...}})
                resume_data = data.get('resume', {})
                resume = Resume(
                    owner_id=current_user.id,
                    first_name=resume_data['first_name'],
                    last_name=resume_data['last_name'],
                    email=resume_data['email'],
                    phone_number=resume_data['phone_number'],
                    address=resume_data['address'],
                    city=resume_data['city'],
                    date_of_birth=datetime.strptime(resume_data['date_of_birth'], '%Y-%m-%d').date(),
                    skills=resume_data['skills']
                )
                db.session.add(resume)
                db.session.commit()  # Commit to generate resume.id

                # Add Work Experience from JSON
                for work_data in resume_data.get('work_experience', []):
                    work = WorkExperience(
                        resume_id=resume.id,  # Now resume_id is properly assigned
                        position=work_data['position'],
                        company=work_data['company'],
                        location=work_data['location'],
                        start_date=datetime.strptime(work_data['start_date'], '%Y-%m-%d'),
                        end_date=datetime.strptime(work_data['end_date'], '%Y-%m-%d') if work_data.get('end_date') else None,
                        is_present=work_data['is_present'],
                        duties=work_data['duties']
                    )
                    db.session.add(work)

                db.session.commit()  # Commit the work experiences
                flash('Resume imported successfully!', 'success')

            else:
                raise ValueError("Invalid JSON structure")

            return redirect(url_for('resumes.dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error importing resume: {str(e)}', 'danger')
        return redirect(url_for('resumes.dashboard'))