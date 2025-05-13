from flask import Blueprint, jsonify, render_template, redirect, url_for, request, flash, make_response, send_file
from flask_login import current_user, login_required
from ..models.jobapp import JobApp
from datetime import datetime
from ..instances import db
import json
import uuid

job_app_bp = Blueprint('job_apps', __name__, url_prefix='/job-applications')

# 📄 Dashboard (List Job Applications)
@job_app_bp.route('/')
def dashboard():

    job_apps = current_user.job_applications

    now = datetime.utcnow()
    interview_soon = []
    needs_follow_up = []

    for job in job_apps:
        # Upcoming interview within 3 days
        if job.interview_date and 0 <= (job.interview_date - now).days <= 3:
            interview_soon.append(job)

        # No follow-up recorded & older than 10 days
        if job.follow_up_date is None and (now - job.application_date).days > 10:
            needs_follow_up.append(job)


    return render_template('job_apps/dashboard.html',
                           job_apps=job_apps, interview_soon=interview_soon, needs_follow_up=needs_follow_up)

# ➕ Create Job Application
@job_app_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():

    # Check subscription limits
    if not current_user.can_create_application():
        flash(f'You have reached the maximum number of job applications ({current_user.max_applications}) for your subscription level.', 'error')
        return redirect(url_for('subscription.upgrade'))

    if request.method == 'POST':
        try:
            # --- Job Application Details ---
            owner_id = current_user.id
            company = request.form.get('company')
            position = request.form.get('position')
            location = request.form.get('location')
            application_date_str = request.form.get('application_date')
            status = request.form.get('status')
            contact_person = request.form.get('contact_person')
            contact_email = request.form.get('contact_email')
            phone_number = request.form.get('phone_number')
            interview_date_str = request.form.get('interview_date')
            interview_mode = request.form.get('interview_mode')
            follow_up_date_str = request.form.get('follow_up_date')
            offer_date_str = request.form.get('offer_date')
            salary_offer = request.form.get('salary_offer')
            job_type = request.form.get('job_type')
            application_link = request.form.get('application_link')
            notes = request.form.get('notes')
            result = request.form.get('result')

            # --- Convert dates to datetime ---
            application_date = datetime.strptime(application_date_str, '%Y-%m-%d') if application_date_str else None
            interview_date = datetime.strptime(interview_date_str, '%Y-%m-%d') if interview_date_str else None
            follow_up_date = datetime.strptime(follow_up_date_str, '%Y-%m-%d') if follow_up_date_str else None
            offer_date = datetime.strptime(offer_date_str, '%Y-%m-%d') if offer_date_str else None

            # --- Create Job Application ---
            job_app = JobApp(
                id=str(uuid.uuid4()), # Ensure the UUID is unique
                owner_id=owner_id,  
                company=company,
                position=position,
                location=location,
                application_date=application_date,
                status=status,
                contact_person=contact_person,
                contact_email=contact_email,
                phone_number=phone_number,
                interview_date=interview_date,
                interview_mode=interview_mode,
                follow_up_date=follow_up_date,
                offer_date=offer_date,
                salary_offer=salary_offer,
                job_type=job_type,
                application_link=application_link,
                notes=notes,
                result=result,
            )

            db.session.add(job_app)
            db.session.commit()

            flash('Job Application created successfully!', 'success')
            return redirect(url_for('job_apps.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating Job Application: {str(e)}', 'danger')
            return redirect(url_for('job_apps.create'))

    return render_template('job_apps/create.html')

# ✏ Edit Job Application
@job_app_bp.route('/edit/<string:job_app_id>', methods=['GET', 'POST'])
@login_required
def edit(job_app_id):
    job_app = JobApp.query.get_or_404(job_app_id)
    if job_app.owner_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('job_apps.dashboard'))

    if request.method == 'POST':
        job_app.company = request.form.get('company')
        job_app.position = request.form.get('position')
        job_app.location = request.form.get('location')
        job_app.status = request.form.get('status')
        job_app.contact_person = request.form.get('contact_person')
        job_app.contact_email = request.form.get('contact_email')
        job_app.phone_number = request.form.get('phone_number')
        job_app.interview_date = datetime.strptime(request.form.get('interview_date'), '%Y-%m-%d') if request.form.get('interview_date') else None
        job_app.interview_mode = request.form.get('interview_mode')
        job_app.follow_up_date = datetime.strptime(request.form.get('follow_up_date'), '%Y-%m-%d') if request.form.get('follow_up_date') else None
        job_app.offer_date = datetime.strptime(request.form.get('offer_date'), '%Y-%m-%d') if request.form.get('offer_date') else None
        job_app.salary_offer = request.form.get('salary_offer')
        job_app.job_type = request.form.get('job_type')
        job_app.application_link = request.form.get('application_link')
        job_app.notes = request.form.get('notes')
        job_app.result = request.form.get('result')

        db.session.commit()
        flash('Job Application updated successfully.', 'success')
        return redirect(url_for('job_apps.dashboard'))

    return render_template('job_apps/edit.html', job_app=job_app)

@job_app_bp.route('/update-job', methods=['POST'])
def update_job():
    data = request.get_json()
    job_id = data['job_id']
    column = data['column']
    new_value = data['value']

    # Validate and process input data
    if column not in ['company', 'position', 'location', 'status', 'salary_offer', 'job_type', 'interview_date', 'interview_mode', 'notes', 'follow_up_date']:
        return jsonify({'success': False, 'message': 'Invalid column name'}), 400

    job = JobApp.query.get(job_id)
    if not job:
        return jsonify({'success': False, 'message': 'Job not found'}), 404

    # Handle specific column types
    if column == 'interview_date':
        # Attempt to parse the date
        try:
            new_value = datetime.strptime(new_value, '%Y-%m-%d') if new_value != 'N/A' else None
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400

    elif column == 'salary_offer' and new_value:
        # Convert salary_offer to a float
        try:
            new_value = float(new_value)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid salary offer value'}), 400

    elif column == 'follow_up_date' and new_value:
        try:
            new_value = datetime.strptime(new_value, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid salary offer value'}), 400

    # Update the job application based on the column
    setattr(job, column, new_value)

    db.session.commit()

    return jsonify({'success': True})

# 🗑 Delete Job Application
@job_app_bp.route('/delete/<string:job_app_id>', methods=['POST'])
@login_required
def delete(job_app_id):
    job_app = JobApp.query.get_or_404(job_app_id)
    if job_app.owner_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('job_apps.dashboard'))

    db.session.delete(job_app)
    db.session.commit()
    flash('Job Application deleted.', 'success')
    return redirect(url_for('job_apps.dashboard'))

# 📄 View Job Application Details
@job_app_bp.route('/view/<string:job_app_id>')
@login_required
def view(job_app_id):
    job_app = JobApp.query.get_or_404(job_app_id)
    if job_app.owner_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('job_apps.dashboard'))

    return render_template('job_apps/view.html', job_app=job_app)

# 📥 Export Job Application as JSON
@job_app_bp.route('/export/<string:job_app_id>', methods=['GET'])
@login_required
def export_job_app(job_app_id):
    job_app = JobApp.query.get_or_404(job_app_id)
    if job_app.owner_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('job_apps.dashboard'))

    try:
        # Export Job Application as JSON
        job_app_data = {
            'company': job_app.company,
            'position': job_app.position,
            'location': job_app.location,
            'application_date': job_app.application_date.strftime('%Y-%m-%d') if job_app.application_date else None,
            'status': job_app.status,
            'contact_person': job_app.contact_person,
            'contact_email': job_app.contact_email,
            'phone_number': job_app.phone_number,
            'interview_date': job_app.interview_date.strftime('%Y-%m-%d') if job_app.interview_date else None,
            'interview_mode': job_app.interview_mode,
            'follow_up_date': job_app.follow_up_date.strftime('%Y-%m-%d') if job_app.follow_up_date else None,
            'offer_date': job_app.offer_date.strftime('%Y-%m-%d') if job_app.offer_date else None,
            'salary_offer': job_app.salary_offer,
            'job_type': job_app.job_type,
            'application_link': job_app.application_link,
            'notes': job_app.notes,
            'result': job_app.result,
        }

        response = make_response(json.dumps(job_app_data, indent=4))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename={job_app.company}_job_application.json'
        return response

    except Exception as e:
        flash(f'Error exporting Job Application: {str(e)}', 'danger')
        return redirect(url_for('job_apps.dashboard'))