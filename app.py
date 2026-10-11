import os
import re
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from config import Config
from models import db, User, Patient, seed_initial_data

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database with app context
db.init_app(app)

with app.app_context():
    db.create_all()
    seed_initial_data()


# -------------------------------------------------------------
# Security & Authentication Helpers
# -------------------------------------------------------------
def login_required(f):
    """Decorator to require authenticated staff session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Access restricted. Please log in with authorized staff credentials.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_current_user():
    """Inject current logged-in user into all templates."""
    current_user = None
    if 'user_id' in session:
        current_user = db.session.get(User, session['user_id'])
    return {'current_user': current_user}


# -------------------------------------------------------------
# Health Check Endpoint (Cloud Container & Load Balancer Probe)
# -------------------------------------------------------------
@app.route('/health')
def health_check():
    """Cloud readiness and liveness health probe."""
    try:
        # Simple DB ping
        patient_count = Patient.query.count()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'record_count': patient_count,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# -------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Staff login portal."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Server-side validation
        if not username or not password:
            flash('Both username and password are required.', 'danger')
            return render_template('login.html', username=username)

        user = User.query.filter_by(username=username).first()

        # Secure password verification
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['role'] = user.role
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Staff logout - invalidates session."""
    session.clear()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('login'))


# -------------------------------------------------------------
# Core Application Routes
# -------------------------------------------------------------
@app.route('/')
@login_required
def root():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard displaying total records, recent registrations, and quick stats."""
    total_patients = Patient.query.count()
    recent_patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()

    # Calculate basic summary metrics for the clinical dashboard
    gender_counts = {
        'Male': Patient.query.filter_by(gender='Male').count(),
        'Female': Patient.query.filter_by(gender='Female').count(),
        'Other': Patient.query.filter_by(gender='Other').count()
    }

    return render_template(
        'dashboard.html',
        total_patients=total_patients,
        recent_patients=recent_patients,
        gender_counts=gender_counts
    )


@app.route('/patients')
@login_required
def list_patients():
    """Search and display all patient records."""
    search_query = request.args.get('search', '').strip()

    query = Patient.query
    if search_query:
        # Parameterized search against Patient ID or Patient Name to prevent SQL injection
        search_filter = f"%{search_query}%"
        query = query.filter(
            (Patient.patient_id.ilike(search_filter)) |
            (Patient.name.ilike(search_filter))
        )

    patients = query.order_by(Patient.id.desc()).all()
    total_count = Patient.query.count()

    return render_template(
        'patients.html',
        patients=patients,
        search_query=search_query,
        total_count=total_count
    )


@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    """Form to register a new patient record."""
    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip().upper()
        name = request.form.get('name', '').strip()
        age_str = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        diagnosis = request.form.get('diagnosis', '').strip()
        doctor_name = request.form.get('doctor_name', '').strip()
        visit_date = request.form.get('visit_date', '').strip()

        # Strict Server-side Validation
        errors = []
        if not patient_id:
            errors.append('Patient ID is required.')
        elif not re.match(r'^[A-Z0-9\-]{3,20}$', patient_id):
            errors.append('Patient ID must be 3-20 alphanumeric characters or hyphens (e.g., PAT-2041).')
        elif Patient.query.filter_by(patient_id=patient_id).first():
            errors.append(f'A patient with ID "{patient_id}" already exists in the system.')

        if not name or len(name) < 2 or len(name) > 100:
            errors.append('Patient name must be between 2 and 100 characters.')

        try:
            age = int(age_str)
            if age < 0 or age > 130:
                errors.append('Age must be a realistic number between 0 and 130.')
        except (ValueError, TypeError):
            errors.append('Valid age is required.')

        if gender not in ['Male', 'Female', 'Other']:
            errors.append('Please select a valid gender option.')

        if not diagnosis or len(diagnosis) < 2:
            errors.append('Clinical diagnosis/symptoms are required.')

        if not doctor_name or len(doctor_name) < 2:
            errors.append('Attending doctor name is required.')

        if not visit_date:
            errors.append('Visit date is required.')
        else:
            try:
                datetime.strptime(visit_date, '%Y-%m-%d')
            except ValueError:
                errors.append('Visit date must be in YYYY-MM-DD format.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'add_patient.html',
                form_data=request.form
            )

        # Save to database using parameterized ORM operations
        new_patient = Patient(
            patient_id=patient_id,
            name=name,
            age=age,
            gender=gender,
            diagnosis=diagnosis,
            doctor_name=doctor_name,
            visit_date=visit_date
        )

        try:
            db.session.add(new_patient)
            db.session.commit()
            flash(f'Patient record for {name} ({patient_id}) created successfully.', 'success')
            return redirect(url_for('list_patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Database error while saving record: {str(e)}', 'danger')
            return render_template('add_patient.html', form_data=request.form)

    return render_template('add_patient.html', form_data={})


@app.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    """Form to edit an existing patient record."""
    patient = db.session.get(Patient, id)
    if not patient:
        flash('Patient record not found.', 'danger')
        return redirect(url_for('list_patients'))

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip().upper()
        name = request.form.get('name', '').strip()
        age_str = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        diagnosis = request.form.get('diagnosis', '').strip()
        doctor_name = request.form.get('doctor_name', '').strip()
        visit_date = request.form.get('visit_date', '').strip()

        # Validation
        errors = []
        if not patient_id:
            errors.append('Patient ID is required.')
        elif not re.match(r'^[A-Z0-9\-]{3,20}$', patient_id):
            errors.append('Patient ID must be 3-20 alphanumeric characters or hyphens.')
        else:
            existing = Patient.query.filter_by(patient_id=patient_id).first()
            if existing and existing.id != patient.id:
                errors.append(f'Patient ID "{patient_id}" is already assigned to another patient.')

        if not name or len(name) < 2 or len(name) > 100:
            errors.append('Patient name must be between 2 and 100 characters.')

        try:
            age = int(age_str)
            if age < 0 or age > 130:
                errors.append('Age must be between 0 and 130.')
        except (ValueError, TypeError):
            errors.append('Valid age is required.')

        if gender not in ['Male', 'Female', 'Other']:
            errors.append('Please select a valid gender option.')

        if not diagnosis or len(diagnosis) < 2:
            errors.append('Clinical diagnosis is required.')

        if not doctor_name or len(doctor_name) < 2:
            errors.append('Doctor name is required.')

        if not visit_date:
            errors.append('Visit date is required.')
        else:
            try:
                datetime.strptime(visit_date, '%Y-%m-%d')
            except ValueError:
                errors.append('Visit date must be in YYYY-MM-DD format.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('edit_patient.html', patient=patient, form_data=request.form)

        # Update record
        try:
            patient.patient_id = patient_id
            patient.name = name
            patient.age = age
            patient.gender = gender
            patient.diagnosis = diagnosis
            patient.doctor_name = doctor_name
            patient.visit_date = visit_date
            db.session.commit()
            flash(f'Patient record for {name} ({patient_id}) updated successfully.', 'success')
            return redirect(url_for('list_patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Database error while updating record: {str(e)}', 'danger')

    return render_template('edit_patient.html', patient=patient, form_data=patient.to_dict())


@app.route('/patients/<int:id>/delete', methods=['POST'])
@login_required
def delete_patient(id):
    """Safely delete patient record after confirmation."""
    patient = db.session.get(Patient, id)
    if not patient:
        flash('Patient record not found.', 'danger')
        return redirect(url_for('list_patients'))

    patient_name = patient.name
    patient_id = patient.patient_id
    try:
        db.session.delete(patient)
        db.session.commit()
        flash(f'Record for patient {patient_name} ({patient_id}) was permanently deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting patient record: {str(e)}', 'danger')

    return redirect(url_for('list_patients'))


@app.route('/cloud-architecture')
@login_required
def cloud_architecture():
    """Information page explaining cloud computing concepts and system architecture."""
    return render_template('cloud_architecture.html')


# -------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    debug_mode = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    print(f"Server starting on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
