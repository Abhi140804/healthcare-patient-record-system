import unittest
from app import app, db
from models import User, Patient, seed_initial_data

class HealthcareSystemTestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated test client with a clean test database."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
            seed_initial_data()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username='admin', password='admin123'):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_health_check_endpoint(self):
        """Verify the cloud health probe /health returns 200 OK and valid JSON."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['status'], 'healthy')
        self.assertEqual(json_data['database'], 'connected')
        self.assertIn('record_count', json_data)

    def test_unauthorized_access_protection(self):
        """Verify unauthorized users are redirected to login."""
        protected_routes = ['/dashboard', '/patients', '/patients/add']
        for route in protected_routes:
            response = self.client.get(route, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login', response.headers['Location'])

    def test_login_flow(self):
        """Verify login works with correct credentials and fails with invalid credentials."""
        # Bad password
        bad_resp = self.login('admin', 'wrongpass')
        self.assertIn(b'Invalid username or password', bad_resp.data)

        # Good login
        good_resp = self.login('admin', 'admin123')
        self.assertIn(b'Welcome back', good_resp.data)
        self.assertIn(b'Clinical Overview', good_resp.data)

    def test_dashboard_patient_count(self):
        """Verify dashboard displays patient count."""
        self.login()
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Total Registered Patients', response.data)
        # 5 sample patients pre-seeded
        self.assertIn(b'5', response.data)

    def test_patient_list_and_search(self):
        """Verify viewing and searching patient records."""
        self.login()
        # View all
        response = self.client.get('/patients')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alice Henderson', response.data)
        self.assertIn(b'PAT-1001', response.data)

        # Search by patient ID
        search_id = self.client.get('/patients?search=PAT-1002')
        self.assertIn(b'James Sterling', search_id.data)

        # Search with non-existent query
        search_none = self.client.get('/patients?search=NONEXISTENT999')
        self.assertIn(b'No Patient Records Found', search_none.data)

    def test_add_patient_valid(self):
        """Verify adding a new valid patient record."""
        self.login()
        new_data = {
            'patient_id': 'PAT-2002',
            'name': 'Robert Brown',
            'age': '48',
            'gender': 'Male',
            'diagnosis': 'Type 2 Diabetes Routine Check',
            'doctor_name': 'Dr. Sarah Jenkins',
            'visit_date': '2026-04-10'
        }
        response = self.client.post('/patients/add', data=new_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Robert Brown', response.data)
        self.assertIn(b'PAT-2002', response.data)
        self.assertIn(b'created successfully', response.data)

        # Confirm in DB
        with app.app_context():
            p = Patient.query.filter_by(patient_id='PAT-2002').first()
            self.assertIsNotNone(p)
            self.assertEqual(p.name, 'Robert Brown')

    def test_add_patient_validation_errors(self):
        """Verify server-side validation catches invalid inputs."""
        self.login()
        # Duplicate patient ID
        dup_data = {
            'patient_id': 'PAT-1001',
            'name': 'Duplicate User',
            'age': '25',
            'gender': 'Male',
            'diagnosis': 'Flu',
            'doctor_name': 'Dr. Test',
            'visit_date': '2026-04-10'
        }
        response = self.client.post('/patients/add', data=dup_data, follow_redirects=True)
        self.assertIn(b'already exists in the system', response.data)

        # Invalid age
        bad_age = dup_data.copy()
        bad_age['patient_id'] = 'PAT-9999'
        bad_age['age'] = '250'
        response2 = self.client.post('/patients/add', data=bad_age, follow_redirects=True)
        self.assertIn(b'Age must be a realistic number between 0 and 130', response2.data)

    def test_edit_patient(self):
        """Verify editing an existing patient record."""
        self.login()
        with app.app_context():
            p = Patient.query.filter_by(patient_id='PAT-1001').first()
            p_id = p.id

        updated_data = {
            'patient_id': 'PAT-1001',
            'name': 'Alice Henderson-Smith',
            'age': '35',
            'gender': 'Female',
            'diagnosis': 'Recovered from Bronchitis',
            'doctor_name': 'Dr. Marcus Lee',
            'visit_date': '2026-03-25'
        }
        response = self.client.post(f'/patients/{p_id}/edit', data=updated_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alice Henderson-Smith', response.data)
        self.assertIn(b'updated successfully', response.data)

        # Check DB
        with app.app_context():
            updated_p = db.session.get(Patient, p_id)
            self.assertEqual(updated_p.name, 'Alice Henderson-Smith')
            self.assertEqual(updated_p.age, 35)

    def test_delete_patient(self):
        """Verify deleting a patient record."""
        self.login()
        with app.app_context():
            p = Patient.query.filter_by(patient_id='PAT-1001').first()
            p_id = p.id

        response = self.client.post(f'/patients/{p_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'permanently deleted', response.data)

        # Confirm deleted from DB
        with app.app_context():
            self.assertIsNone(db.session.get(Patient, p_id))

    def test_logout(self):
        """Verify logout clears session and redirects to login."""
        self.login()
        resp = self.logout()
        self.assertIn(b'You have been securely logged out', resp.data)
        # Attempting dashboard should redirect to login
        dash_resp = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(dash_resp.status_code, 302)


if __name__ == '__main__':
    unittest.main()
