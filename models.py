from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """Hospital staff user account for authentication."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='Hospital Staff')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Securely hash and store the staff password using PBKDF2:SHA256."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)


class Patient(db.Model):
    """Patient medical record model."""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    diagnosis = db.Column(db.String(255), nullable=False)
    doctor_name = db.Column(db.String(100), nullable=False)
    visit_date = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialize patient record for structured views."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'diagnosis': self.diagnosis,
            'doctor_name': self.doctor_name,
            'visit_date': self.visit_date,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


def seed_initial_data():
    """Seed sample hospital staff and fictional patient records if empty."""
    # Seed default staff user if none exists
    if not User.query.filter_by(username='admin').first():
        admin_staff = User(
            username='admin',
            full_name='Dr. Sarah Jenkins (Lead Registrar)',
            role='Clinical Administrator'
        )
        admin_staff.set_password('admin123')
        db.session.add(admin_staff)

    # Seed sample fictional patient records if none exist
    if Patient.query.count() == 0:
        sample_patients = [
            Patient(
                patient_id='PAT-1001',
                name='Alice Henderson',
                age=34,
                gender='Female',
                diagnosis='Seasonal Bronchitis',
                doctor_name='Dr. Marcus Lee',
                visit_date='2026-03-15'
            ),
            Patient(
                patient_id='PAT-1002',
                name='James Sterling',
                age=58,
                gender='Male',
                diagnosis='Essential Hypertension (Stage 1)',
                doctor_name='Dr. Angela Rossi',
                visit_date='2026-03-18'
            ),
            Patient(
                patient_id='PAT-1003',
                name='Maria Gomez',
                age=27,
                gender='Female',
                diagnosis='Sprained Right Ankle (Grade II)',
                doctor_name='Dr. Robert Chen',
                visit_date='2026-03-22'
            ),
            Patient(
                patient_id='PAT-1004',
                name='David Kim',
                age=45,
                gender='Male',
                diagnosis='Type 2 Diabetes Mellitus Follow-up',
                doctor_name='Dr. Marcus Lee',
                visit_date='2026-03-29'
            ),
            Patient(
                patient_id='PAT-1005',
                name='Elena Rostova',
                age=62,
                gender='Female',
                diagnosis='Mild Osteoarthritis - Knee',
                doctor_name='Dr. Angela Rossi',
                visit_date='2026-04-02'
            ),
        ]
        db.session.bulk_save_objects(sample_patients)

    db.session.commit()
