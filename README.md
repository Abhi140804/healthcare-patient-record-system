# Healthcare Data Management and Secure Patient Record System

A secure, beginner-friendly, working web application built with **Python Flask**, **SQLite/SQLAlchemy**, and a responsive clinical frontend. Designed to demonstrate fundamental **cloud computing concepts** (containerization, ephemeral vs. persistent storage, environment-driven configuration, 3-tier architecture, and basic web security) for academic evaluation and demonstrations.

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Cloud Architecture & Concepts](#cloud-architecture--concepts)
3. [Technology Stack](#technology-stack)
4. [Security Measures](#security-measures)
5. [Local Development Setup](#local-development-setup)
6. [Cloud Deployment Setup](#cloud-deployment-setup)
7. [Local vs. Cloud Differences](#local-vs-cloud-differences)
8. [Testing & Evaluation Checklist](#testing--evaluation-checklist)
9. [Performance, Scalability & Cost Considerations](#performance-scalability--cost-considerations)
10. [Academic & Healthcare Disclaimer](#academic--healthcare-disclaimer)

---

## 🏥 1. Project Overview

The **Healthcare Data Management and Secure Patient Record System** enables authorized hospital staff (doctors, nurses, medical registrars) to:
- **Dashboard:** Monitor the total number of registered patients, demographic summaries, and recent admissions in real time.
- **Add Patient:** Register new patient records with full clinical intake fields (`Patient ID`, `Name`, `Age`, `Gender`, `Diagnosis`, `Doctor Name`, and `Visit Date`).
- **View Patients:** Inspect all patient records in a structured, responsive medical table.
- **Search Patients:** Query patient records by **Patient ID** (e.g., `PAT-1001`) or **Patient Name** with server-side parameterized filters and live client-side matching.
- **Edit Patient:** Update patient diagnosis, attending doctor, and clinical information.
- **Delete Patient:** Safely delete obsolete records after an explicit confirmation dialog.
- **Role-Based Authentication:** Protect all medical endpoints with secure server-side login sessions.

> **Note:** All pre-loaded patient profiles and case notes are entirely fictional.

---

## ☁️ 2. Cloud Architecture & Concepts

### Three-Tier Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                 1. CLIENT TIER                                    |
|   Hospital Staff Browser (Desktop / Tablet / Mobile)                             |
|   - HTML5, CSS3, JavaScript Client                                                |
|   - Session Cookies & Client-Side Validation                                      |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ HTTPS / TLS (Port 443)
+-----------------------------------------------------------------------------------+
|                        2. APPLICATION TIER (CLOUD COMPUTE)                        |
|   Containerized Flask WSGI Service (Google Cloud Run / AWS / Azure / Docker)      |
|   - Gunicorn Production Server (Multi-threaded workers)                           |
|   - Server-side Session Management & Route Authentication (@login_required)       |
|   - PBKDF2:SHA-256 Password Hash Verification                                     |
|   - Liveness & Readiness Health Probes (`/health`)                                 |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ Parameterized SQL (Port 5432 / File I/O)
+-----------------------------------------------------------------------------------+
|                           3. DATA TIER (CLOUD STORAGE)                            |
|   Database Layer                                                                  |
|   - Local Dev: Embedded SQLite file (`healthcare.db`)                             |
|   - Cloud Prod: Managed Relational DB (Google Cloud SQL / AWS RDS PostgreSQL)    |
|   - Parameterized queries to prevent SQL injection                                 |
+-----------------------------------------------------------------------------------+
```

### Cloud Computing Concepts Demonstrated

1. **Containerization (Docker):**
   - Packages source code, system binaries, and Python packages into an immutable container image (`Dockerfile`).
   - Ensures identical behavior between a student's local laptop and cloud servers (*"works everywhere"*).

2. **Ephemeral vs. Persistent Storage:**
   - Cloud containers are **ephemeral** (stateless)—when a container restarts or scales down, local disk changes are lost.
   - For local development, **SQLite** runs inside the file system for zero-friction setup.
   - For cloud production, state is decoupled: patient records are stored in a **Managed Cloud Database** (e.g., PostgreSQL or MySQL on AWS RDS / Google Cloud SQL) passed via the `DATABASE_URL` environment variable.

3. **12-Factor App & Environment Variables:**
   - Configuration items such as `SECRET_KEY`, `PORT`, and `DATABASE_URL` are injected at runtime via environment variables rather than hardcoded in source control.

4. **Health Checking & Cloud Probes:**
   - The application provides a lightweight `/health` endpoint returning `HTTP 200 OK` and JSON status. Cloud orchestrators (Kubernetes, AWS ECS, Google Cloud Run) query this probe to ensure healthy traffic routing.

---

## 🛠️ 3. Technology Stack

| Layer | Component | Choice & Justification |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JS | Lightweight, clean hospital aesthetic, zero npm build step, universally compatible. |
| **Backend** | Python 3 + Flask | Minimalist, readable micro-framework ideal for learning and demonstrating cloud patterns. |
| **WSGI Server** | Gunicorn | Production-grade WSGI server running concurrent workers and threads inside Docker. |
| **ORM / Database** | Flask-SQLAlchemy | Abstracted ORM providing parameterized queries and seamless switching between SQLite and PostgreSQL/MySQL. |
| **Database** | SQLite (Dev) / PostgreSQL (Cloud) | SQLite enables instant local execution without installing a database server; PostgreSQL provides production persistence. |
| **Container** | Docker | Linux container based on `python:3.9-slim` with a multi-worker production entrypoint. |

---

## 🔒 4. Security Measures

- **Password Hashing:** Passwords are never stored in plain text. They are hashed using **PBKDF2 with SHA-256** and cryptographic salt via `werkzeug.security`.
- **Server-Side Session Management:** Authenticated staff credentials are kept in encrypted server-side session cookies with `HttpOnly` and `SameSite=Lax` flags enabled to protect against XSS and session hijacking.
- **Route Authorization:** Protected endpoints use a `@login_required` decorator that redirects unauthenticated requests to the login page.
- **Parameterized SQL Queries:** Queries are executed through SQLAlchemy ORM, automatically parameterizing user inputs and eliminating SQL injection vulnerabilities.
- **Server-Side Validation:** All fields (Patient ID format, age bounds `0–130`, date formatting, string lengths) are verified on the backend before database commits.
- **Secret Isolation:** Application secrets are read from environment variables with sensible defaults for local development.

---

## 🚀 5. Local Development Setup

### Prerequisites
- Python 3.9+ installed on your system.
- Git (optional).

### Step-by-Step Instructions

1. **Navigate to the Project Directory:**
   ```bash
   cd cloud_project
   ```

2. **Create and Activate a Virtual Environment:**
   - On macOS / Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - On Windows:
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application:**
   ```bash
   python app.py
   ```

5. **Open in Browser:**
   Navigate to [http://localhost:5000](http://localhost:5000)

### Pre-Seeded Evaluation Credentials
The database automatically initializes upon first run with:
- **Username:** `admin`
- **Password:** `admin123`
- **Sample Records:** 5 pre-loaded fictional patients with realistic diagnoses.

---

## ☁️ 6. Cloud Deployment Setup

### Option A: Deployment with Docker (Any Cloud Platform)

1. **Build the Container Image:**
   ```bash
   docker build -t healthcare-record-system .
   ```

2. **Run the Container Locally:**
   ```bash
   docker run -p 5000:5000 -e SECRET_KEY="my-production-secret" healthcare-record-system
   ```

---

### Option B: Deploy to Google Cloud Run (Serverless Container)

1. **Authenticate with Google Cloud SDK:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_GCP_PROJECT_ID
   ```

2. **Build and Submit Container to Google Artifact Registry:**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/healthcare-system
   ```

3. **Deploy Container to Cloud Run:**
   ```bash
   gcloud run deploy healthcare-system \
       --image gcr.io/YOUR_GCP_PROJECT_ID/healthcare-system \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated \
       --set-env-vars SECRET_KEY="cloud-secure-secret-key"
   ```
   *Google Cloud Run will output a public HTTPS URL (e.g. `https://healthcare-system-xyz-uc.a.run.app`).*

---

### Option C: Deploy to AWS App Runner (Recommended for AWS)

**AWS App Runner** is Amazon's fully managed container application service (equivalent to Google Cloud Run). It connects directly to your GitHub repository and automatically deploys using the included `apprunner.yaml`:

1. Open the **[AWS App Runner Console](https://console.aws.amazon.com/apprunner)**.
2. Click **Create service**.
3. Under **Repository type**, select **Source code repository**.
4. Connect your GitHub account and select:
   - **Repository:** `Abhi140804/healthcare-patient-record-system`
   - **Branch:** `main`
5. Under **Deployment trigger**, select **Automatic** (so git pushes trigger new deployments).
6. Under **Configuration settings**, choose **"Use a configuration file"** (App Runner will automatically detect `apprunner.yaml`).
7. Click **Next** and **Create & Deploy**.
8. AWS App Runner will provision the container, route traffic, configure TLS, and output your live application URL (e.g. `https://xxxxxx.us-east-1.awsapprunner.com`).

---

### Option D: Deploy to AWS Elastic Beanstalk

**AWS Elastic Beanstalk** is widely taught in university cloud computing courses. The repository includes `Dockerrun.aws.json` for turn-key deployment:

1. Open the **[AWS Elastic Beanstalk Console](https://console.aws.amazon.com/elasticbeanstalk)**.
2. Click **Create Application**.
3. Set **Application Name:** `healthcare-patient-record-system`.
4. Under **Platform**, select:
   - **Platform:** `Docker`
   - **Platform branch:** `Docker running on 64bit Amazon Linux 2`
5. Under **Application code**, select **Upload your code** and upload a zip containing the repository files (or connect via AWS CodePipeline using `buildspec.yml`).
6. Click **Create app**. Elastic Beanstalk automatically spins up an EC2 instance, configures an Elastic Load Balancer (ELB), and runs your Docker container.

---

### Option E: Deploy to AWS ECS (Elastic Container Service with Fargate)

For serverless container orchestration:
1. Build and push your image to **Amazon ECR** (Elastic Container Registry):
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
   docker build -t healthcare-system .
   docker tag healthcare-system:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/healthcare-system:latest
   docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/healthcare-system:latest
   ```
2. Register the task definition in AWS ECS using the provided `aws-ecs-task-definition.json`:
   ```bash
   aws ecs register-task-definition --cli-input-json file://aws-ecs-task-definition.json
   ```
3. Create a Fargate Service with an Application Load Balancer targeting container port `5000` and health check `/health`.

---

### Option F: Connecting to Amazon RDS (PostgreSQL Database)

For persistent patient records across container restarts on AWS:
1. Create a PostgreSQL instance in **Amazon RDS** (Free Tier `db.t4g.micro`).
2. Set the `DATABASE_URL` environment variable in AWS App Runner, Elastic Beanstalk, or ECS:
   ```bash
   DATABASE_URL="postgresql://postgres:<YOUR_RDS_PASSWORD>@<YOUR_RDS_ENDPOINT>:5432/healthcare_db"
   ```
3. The Flask application automatically switches from local SQLite to the RDS PostgreSQL database without any code changes!

---

## ⚖️ 7. Local vs. Cloud Deployment Setup

| Feature | Local Development Setup | Cloud Production Deployment |
| :--- | :--- | :--- |
| **Database** | Embedded SQLite (`instance/healthcare.db`) file | Managed Cloud Database (e.g. PostgreSQL on AWS RDS or Google Cloud SQL) |
| **Storage Nature** | Saved on local computer hard drive | Persistent external storage volume / managed DB |
| **Server Engine** | Flask built-in development server (`app.run()`) | Production WSGI Server (`gunicorn` with multiple worker processes) |
| **Containerization** | Direct Python interpreter execution | Packaged inside lightweight Docker container |
| **Networking & TLS** | Plain HTTP (`http://localhost:5000`) | Managed HTTPS / TLS terminated by Cloud Load Balancer |
| **Configuration** | Default fallback values in `config.py` | Injected via Cloud Environment Variables (`DATABASE_URL`, `SECRET_KEY`) |

### Switching to a Cloud Database
No application code changes are required to connect to a cloud database. Simply set the `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql://dbuser:securepassword@cloud-db-host:5432/healthcaredb"
```
The SQLAlchemy configuration in [config.py](file:///Users/siddhartharanjanjena/Desktop/cloud_project/config.py) automatically switches database drivers based on this connection string.

---

## ✅ 8. Testing & Evaluation Checklist

### Running the Automated Test Suite
An automated test suite covering all functional requirements, security guards, input validation, and health checks is included:
```bash
python tests.py
```
*Expected Output:*
```text
Ran 10 tests in ~3-6s
OK
```

### Manual Demonstration Checklist for College Presentations

| Test # | Test Scenario | Steps to Execute | Expected Result |
| :---: | :--- | :--- | :--- |
| **T-1** | **Unauthorized Access** | Try opening `http://localhost:5000/patients` directly in an incognito window. | Redirected to `/login` with an amber *"Access restricted"* notice. |
| **T-2** | **Staff Authentication** | Enter username `admin` and password `admin123`. | Successfully logs in and lands on Dashboard with welcome greeting. |
| **T-3** | **Total Patient Count** | Verify the number on the **Total Registered Patients** card. | Correctly displays `5` (or current count). |
| **T-4** | **Search by Patient ID** | Go to **Patient Records**, type `PAT-1002` into the search bar, click Search. | Only James Sterling's record is displayed. |
| **T-5** | **Search by Patient Name** | Search for `Alice`. | Displays Alice Henderson's record. |
| **T-6** | **Register New Patient** | Click **Add Patient**, enter valid fields (`PAT-3001`, `John Doe`, age `40`, `Male`, `Fever`, `Dr. Lee`, today's date). | Green success alert appears, patient shows up in registry and count increments. |
| **T-7** | **Input Validation** | Attempt to register with age `250` or a duplicate patient ID. | Submission is rejected with an error explanation banner. |
| **T-8** | **Edit Patient Record** | Click **Edit** on any record, change diagnosis to `Fully Recovered`, submit. | Record updates in the database and reflects immediately on the table. |
| **T-9** | **Delete with Confirmation** | Click **Delete** on a record. A confirmation modal appears. Click Confirm. | Patient is permanently deleted, and a notification banner confirms deletion. |
| **T-10**| **Cloud Health Probe** | Visit `http://localhost:5000/health`. | Returns clean JSON with `"status": "healthy"` and `"database": "connected"`. |
| **T-11**| **Staff Logout** | Click the **Logout** button in the header. | Session is cleared and user is redirected to the login page. |

---

## 📊 9. Performance, Scalability & Cost Considerations

### Performance
- **Local Dev Response Time:** Under normal local execution, response times for database lookups and page renders are typically **under 15–30 milliseconds** due to in-memory SQLite caching and minimal server overhead.
- **Latency Testing:** You can test latency directly by querying the `/health` endpoint or invoking `measureServerLatency()` in the browser developer console.

### Scalability
- **Horizontal Scaling:** Because the Flask application is stateless (session state is signed into cookies rather than kept in server RAM), multiple container instances can run behind a Cloud Load Balancer simultaneously.
- **Database Connection Pooling:** In a large cloud deployment, connecting through a database connection pooler (like AWS RDS Proxy or PgBouncer) prevents database saturation during high concurrency.

### Approximate Cloud Cost Considerations
- **Free Tier / Development Tier:**
  - **Google Cloud Run:** 2 million free requests per month (effectively **$0.00/month** for a college demo).
  - **Render / Railway:** Free starter credits or free tiers available for web containers.
- **Small Production Setup:**
  - Container compute (e.g. 0.5 vCPU, 512MB RAM): ~$5 – $10 / month.
  - Basic Managed Database (e.g., AWS RDS db.t4g.micro or Google Cloud SQL micro instance): ~$12 – $18 / month.
  - Domain + TLS Certificate: Free automated TLS via Let's Encrypt or Cloudflare.

---

## ⚠️ 10. Academic & Healthcare Disclaimer

> **IMPORTANT DISCLAIMER:**  
> This web application is an **academic project designed exclusively for college coursework, cloud computing demonstrations, and technical evaluation**.
> 
> - **Fictional Data Only:** All patient records, diagnoses, and medical staff names are entirely fictional and randomly generated.
> - **Not for Real Hospital Use:** This system is **NOT** compliant with HIPAA, GDPR-Health, or official medical data regulations and must **NOT** be used for actual clinical patient management or real personal health information.
