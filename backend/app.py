from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from flask_cors import CORS
from celery_worker import export_csv, generate_reports
from flask import send_file
from flask_caching import Cache
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import os

#Making the Flask and SQLALchemy Instances
app = Flask(__name__)

CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['JWT_SECRET_KEY'] = 'your-new-long-32-byte-hex-string-here'

app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
app.config['CACHE_DEFAULT_TIMEOUT'] = 60

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'portalplacement3@gmail.com'
app.config['MAIL_PASSWORD'] = 'jkby zwha elth qpmz'
app.config['MAIL_DEFAULT_SENDER'] = 'portalplacement3@gmail.com'

cache = Cache()
cache.init_app(app)
mail = Mail(app)
db = SQLAlchemy(app)
jwt = JWTManager(app)

#The Tables - User Table , Student_Profile Table , Company_Profile Table & Job_Applications Table
class User(db.Model):
    ids = db.Column(db.Integer , primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    email = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(255), nullable = False)
    role = db.Column(db.String(255), nullable = False)
    is_approved = db.Column(db.Boolean, default=True)
    #Forward Rel^nship
    student_prf_frwrel = db.relationship("StudentProfile", back_populates = "user_br" , uselist=False)

class StudentProfile(db.Model):
    __tablename__ = 'student'
    p_id = db.Column(db.Integer , primary_key = True)
    department = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    resume = db.Column(db.Text)
    education = db.Column(db.String(255))
    skills = db.Column(db.String(255))
    experience = db.Column(db.Text)
    #one to One Rel^n
    user_id = db.Column(db.Integer, db.ForeignKey("user.ids"), unique = True)
    #Back Relationship
    user_br = db.relationship("User", back_populates = "student_prf_frwrel")

class CompanyProfile(db.Model):
    __tablename__ = 'company'

    c_id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150))
    description = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey("user.ids"), unique=True, nullable=False)
    user_br = db.relationship("User")

class JobApplication(db.Model):
    __tablename__ = "job_application"

    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("student.p_id"))
    offer_letter = db.Column(db.String(255))
    status = db.Column(db.String(20), default="applied")
    feedback = db.Column(db.Text)
    interview_date = db.Column(db.String(50))
    interview_link = db.Column(db.String(255))
    reminder_sent = db.Column(db.Boolean, default=False)
    student = db.relationship("StudentProfile")
    job = db.relationship("Job")

class Job(db.Model):
    __tablename__ = "job"
    
    id = db.Column(db.Integer, primary_key=True)
    skills = db.Column(db.String(255))
    title = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150))
    salary = db.Column(db.Integer)
    description = db.Column(db.Text)
    experience = db.Column(db.Integer)
    company_id = db.Column(db.Integer, db.ForeignKey("company.user_id"))
    benefits = db.Column(db.Text)
    status = db.Column(db.String(20), default="active")  


@jwt.unauthorized_loader
def missing_token_callback(err):
    return jsonify({"msg": "Missing or invalid token"}), 401


@app.route('/',methods = ['GET','POST'])
def index():
    return 'this is the index page'

@app.route('/req',methods = ['POST'])
def registration():
    data = request.get_json()
    frontend_name = data.get('name')
    frontend_email = data.get('email')
    frontend_pass = data.get('password')
    dr_role = data.get('role')
    existing_pers = User.query.filter_by(email = frontend_email).first()

    #Removing The Roles Other than Student and Company
    if dr_role not in ['student', 'company']:
        return jsonify({'msg': 'Invalid role'}), 400

    #check Partial Registration Here 
    if not all([frontend_name, frontend_email, frontend_pass, dr_role]):
        return jsonify({'msg' : 'Missing Feilds'}),400
    
    #Check Admin Registration Here
    if dr_role == 'admin':
        return jsonify({'msg' : 'Administrator cant be registered'}),400

    #If the Person is Already Registered
    if existing_pers:
        return jsonify({'msg' : 'Email ALready Exists '}),400

    new_user = User(
        name = frontend_name,
        email = frontend_email,
        password = generate_password_hash(frontend_pass),
        role = dr_role,
        is_approved = False if dr_role == 'company' else True
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({
        'msg' : 'Registration Successfull',
        'user_id' : new_user.ids,
        'role' : new_user.role
    }),201

@app.route('/login',methods = ['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({'msg': 'Invalid JSON'}), 400

    usr = User.query.filter_by(email = data['email']).first()

    #If User Not Found
    if not usr:
        return jsonify({'msg' : 'User Not Found'}),404

    #If Password is Wrong
    if not check_password_hash(usr.password, data['password']):
        return jsonify({'msg': 'Incorrect Password'}), 401

    
    #If User isnt Approved As of Yet
    if not usr.is_approved:
        return jsonify({'msg': 'Account not approved yet'}), 403

    access_token = create_access_token(
        identity = str(usr.ids),
        additional_claims = {"role": usr.role}
    )
    return jsonify({
        "access_token": access_token,
        "role": usr.role,
        "name": usr.name,
        "user_id": usr.ids
    }), 200

@app.route('/student/dashboard' , methods = ['GET'])
@jwt_required()
def student_dashboard():
    user_id = get_jwt_identity()
    claims = get_jwt()

    if claims['role'] != 'student':
        return jsonify({
            'msg': 'Unauthorized'
        }), 403
    
    return jsonify({
        'msg': 'Welcome Student',
        'user_id' : user_id
    })

@app.route('/admin/dashboard' , methods = ['GET'])
@jwt_required()
def admin_dashboard():
    user_id = get_jwt_identity()
    claims = get_jwt()

    if claims['role'] != 'admin':
        return jsonify({'msg': 'Unauthorized'}), 403
    
    students = User.query.filter_by(role='student').all()
    companies = User.query.filter_by(role='company').all()

    total_jobs = Job.query.count()
    total_applications = JobApplication.query.count()

    return jsonify({
        'students': [
            {
                'ids': s.ids,
                'name': s.name,
                'email': s.email,
                'is_approved': s.is_approved
            } for s in students
        ],
        'companies': [
            {
                'ids': c.ids,
                'name': c.name,
                'email': c.email,
                'is_approved': c.is_approved
            } for c in companies
        ],
        'total_students': len(students),
        'total_companies': len(companies),
        'total_jobs': total_jobs,
        'total_applications': total_applications
    })

#The Company Dashboard Route is this
@app.route('/company/dashboard', methods=['GET'])
@jwt_required()
def company_dashboard():

    user_id = int(get_jwt_identity())   # <-- IMPORTANT
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    jobs_posted = Job.query.filter_by(
        company_id=user_id,
        status="active"
    ).count()

    candidates_applied = (
        JobApplication.query
        .join(Job)
        .filter(Job.company_id == user_id)
        .count()
    )

    candidates_shortlisted = (
        JobApplication.query
        .join(Job)
        .filter(
            Job.company_id == user_id,
            JobApplication.status.in_(["shortlisted", "interview", "selected"])
        )
        .count()
    )

    return jsonify({
        "jobs_posted": jobs_posted,
        "candidates_applied": candidates_applied,
        "candidates_shortlisted": candidates_shortlisted
    })

#Admin Will Approve the Company
@app.route('/admin/approve/<int:user_id>', methods=['POST'])
@jwt_required()
def approve_company(user_id):
    claims = get_jwt()

    if claims['role'] != 'admin':
        return jsonify({'msg': 'Unauthorized'}), 403

    user = User.query.get(user_id)

    if not user or user.role != 'company':
        return jsonify({'msg': 'Invalid company user'}), 404

    user.is_approved = True
    db.session.commit()

    return jsonify({'msg': 'Company approved successfully'})

@app.route("/company/jobs", methods=["POST"])
@jwt_required()
def create_job():

    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user.is_approved:
        return jsonify({"msg": "Company not approved"}), 403

    claims = get_jwt()

    data = request.get_json()
    experience = data.get("experience")

    try:
        experience = int(experience)
        if experience < 0:
            return jsonify({"msg": "Experience must be non-negative"}), 400
    except:
        return jsonify({"msg": "Experience must be an integer"}), 400

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    if (
        not data.get("title") or
        not data.get("description") or
        not data.get("skills") or
        not data.get("experience") or
        not data.get("benefits")
    ):
        return jsonify({"msg": "All fields are required"}), 400

    existing_job = Job.query.filter(
        Job.company_id == user_id,
        Job.title.ilike(data["title"].strip()),
        Job.location.ilike(data["location"].strip()),
        Job.skills.ilike(data["skills"].strip())
    ).first()

    if existing_job:
        return jsonify({"msg": "Similar job already exists for this role and location"}), 400

    job = Job(
        title=data["title"],
        location=data["location"],
        salary=data["salary"],
        description=data["description"],
        skills=data.get("skills"),
        experience=experience,
        benefits=data.get("benefits"),
        company_id=user_id
    )   

    db.session.add(job)
    db.session.commit()

    cache.delete_memoized(student_jobs)
    return jsonify({"msg": "Job created Successfull !!"}), 201

@app.route("/company/jobs", methods=["GET"])
@jwt_required()
def get_jobs():
    user_id = get_jwt_identity()
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    jobs = Job.query.filter_by(company_id=user_id).all()

    return jsonify([
    {
        "id": j.id,
        "title": j.title,
        "location": j.location,
        "salary": j.salary,
        "status": j.status,
        "description": j.description,
        "skills": j.skills,
        "experience": j.experience,
        "benefits": j.benefits,
        "applicants": [],
        "shortlisted": []
    }
    for j in jobs
    ])

@app.route("/company/jobs/<int:job_id>", methods=["DELETE"])
@jwt_required()
def delete_job(job_id):
    user_id = get_jwt_identity()
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    job = Job.query.filter_by(id=job_id, company_id=user_id).first()

    if not job:
        return jsonify({"msg": "Job not found or not owned by company"}), 404

    db.session.delete(job)
    db.session.commit()

    return jsonify({
        "msg": "Job deleted successfully",
        "deleted_job_id": job_id
    }), 200

@app.route("/company/jobs/<int:job_id>", methods=["PUT"])
@jwt_required()
def update_job(job_id):
    user_id = get_jwt_identity()
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    job = Job.query.filter_by(id=job_id, company_id=user_id).first()

    if not job:
        return jsonify({"msg": "Job not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"msg": "Invalid JSON"}), 400

    # Validate fields
    if "title" in data:
        if not data["title"].strip():
            return jsonify({"msg": "Title cannot be empty"}), 400
        job.title = data["title"].strip()

    if "location" in data:
        job.location = data["location"].strip()

    if "salary" in data:
        try:
            salary = int(data["salary"])
            if salary <= 0:
                return jsonify({"msg": "Salary must be positive"}), 400
            job.salary = salary
        except ValueError:
            return jsonify({"msg": "Salary must be integer"}), 400

    if "description" in data:
        job.description = data["description"].strip()

    if "experience" in data:
        try:
            exp = int(data["experience"])
            if exp < 0:
                return jsonify({"msg": "Experience must be non-negative"}), 400
            job.experience = exp
        except:
            return jsonify({"msg": "Experience must be integer"}), 400
    
    if "skills" in data:
        job.skills = data["skills"].strip()

    if "benefits" in data:
        job.benefits = data["benefits"].strip()
        db.session.commit()

    return jsonify({
        "msg": "Job updated successfully",
        "job_id": job.id
    }), 200

@app.route('/company/profile', methods=['GET'])
@jwt_required()
def get_company_profile():
    user_id = get_jwt_identity()
    claims = get_jwt()

    if claims['role'] != 'company':
        return jsonify({'msg': 'Unauthorized'}), 403

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "name": user.name,
        "email": user.email
    })

@app.route('/company/profile', methods=['PUT'])
@jwt_required()
def update_company_profile():
    user_id = get_jwt_identity()
    claims = get_jwt()

    if claims['role'] != 'company':
        return jsonify({'msg': 'Unauthorized'}), 403

    user = db.session.get(User, user_id)
    data = request.get_json()

    if not data:
        return jsonify({'msg': 'Invalid JSON'}), 400

    # Update name
    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"msg": "Company name cannot be empty"}), 400
        user.name = name

    # Update email
    if "email" in data:
        email = data["email"].strip()

        if not email:
            return jsonify({"msg": "Email cannot be empty"}), 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.ids != user.ids:
            return jsonify({"msg": "Email already in use"}), 400

        user.email = email

    # Update password
    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            return jsonify({"msg": "Password must be at least 6 characters"}), 400

        user.password = generate_password_hash(data["password"])

    db.session.commit()

    return jsonify({
        "msg": "Profile updated successfully",
        "updated_name": user.name,
        "updated_email": user.email
    }), 200

#Seeing the Company Applicants Button
@app.route("/company/applicants", methods=["GET"])
@jwt_required()
@cache.cached(
    timeout=60,
    key_prefix=lambda: f"company_{get_jwt_identity()}_applicants"
)
def get_company_applicants():

    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403


    # Get all applications for jobs belonging to this company
    applications = JobApplication.query.join(Job).filter(
        Job.company_id == user_id
    ).all()

    result = []

    for app in applications:

        student_profile = app.student
        user = student_profile.user_br

        result.append({
            "application_id": app.id,
            "student_name": user.name,
            "department": student_profile.department,
            "cgpa": student_profile.cgpa,
            "resume": student_profile.resume,
            "job_title": app.job.title,
            "job_id": app.job.id,
            "status": app.status,
            "interview_date": app.interview_date,
            "interview_link": app.interview_link
        })

    return jsonify(result)

#One unified route for shortlisting or rejecting students with particular feedback
@app.route("/company/application/<int:app_id>/decision", methods=["POST"])
@jwt_required()
def decide_application(app_id):

    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.get_json()

    status = data.get("status")
    feedback = data.get("feedback")

    app = JobApplication.query.get(app_id)

    if not app:
        return jsonify({"msg": "Application not found"}), 404

    app.status = status
    app.feedback = feedback

    db.session.commit()
    
    cache.delete_memoized(get_company_applicants)
    return jsonify({"msg": "Application updated"})

#Scheduling the said Interviw of the appropriate candidates
@app.route("/company/application/<int:app_id>/schedule", methods=["PUT"])
@jwt_required()
def schedule_interview(app_id):

    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    application = JobApplication.query.get(app_id)

    if not application:
        return jsonify({"msg": "Application not found"}), 404

    job = Job.query.get(application.job_id)

    if job.company_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403

    if application.status != "shortlisted":
        return jsonify({"msg": "Only shortlisted candidates can be scheduled"}), 400

    data = request.get_json()

    if not data:
        return jsonify({"msg": "Invalid JSON"}), 400

    application.interview_date = data.get("interview_date")
    application.interview_link = data.get("interview_link")
    application.status = "interview"

    db.session.commit()

    cache.delete_memoized(get_company_applicants)
    return jsonify({
        "msg": "Interview scheduled successfully",
        "application_id": application.id
    }), 200

#Adding the View Shortlisted Students Route
@app.route("/company/shortlisted", methods=["GET"])
@jwt_required()
def get_shortlisted_students():
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    apps = JobApplication.query.join(Job).filter(
        Job.company_id == user_id,
        JobApplication.status.in_(["shortlisted", "interview", "offer"])
    ).all()

    result = []
    for a in apps:
        student = a.student
        user = student.user_br

        result.append({
            "application_id": a.id, 
            "name": user.name,
            "department": student.department,
            "cgpa": student.cgpa,
            "resume": student.resume,
            "job_title": a.job.title,
            "status": a.status,
            "interview_date": a.interview_date, 
            "interview_link": a.interview_link
        })

    return jsonify(result)

#Backend API to Close the Job post by the company
@app.route("/company/jobs/<int:job_id>/close", methods=["PUT"])
@jwt_required()
def close_job(job_id):

    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    job = Job.query.filter_by(id=job_id, company_id=user_id).first()

    if not job:
        return jsonify({"msg": "Job not found"}), 404

    job.status = "closed"
    db.session.commit()

    return jsonify({"msg": "Job closed"})

#Backend API to Open or ReOpen the Job Post if closed
@app.route("/company/jobs/<int:job_id>/open", methods=["PUT"])
@jwt_required()
def open_job(job_id):

    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    job = Job.query.filter_by(id=job_id, company_id=user_id).first()

    if not job:
        return jsonify({"msg": "Job not found"}), 404

    job.status = "active"
    db.session.commit()

    return jsonify({"msg": "Job reopened"})

#Backend Route for final decision post interview
@app.route("/company/application/<int:app_id>/final", methods=["PUT"])
@jwt_required()
def final_decision(app_id):
    application = JobApplication.query.get(app_id)

    if not application:
        return jsonify({"msg": "Application not found"}), 404

    job = Job.query.get(application.job_id)

    if job.company_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403

    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.get_json()
    decision = data.get("decision")
    offer_letter = data.get("offer_letter")

    if decision == "selected":
        application.status = "offer"
        application.offer_letter = offer_letter
    else:
        application.status = "rejected"

    if decision not in ["selected", "rejected"]:
        return jsonify({"msg": "Invalid decision"}), 400

    application.status = decision
    db.session.commit()

    cache.delete_memoized(get_company_applicants)
    return jsonify({
        "msg": "Final decision recorded",
        "status": decision
    })

@app.route('/admin/toggle/<int:user_id>', methods=['POST'])
@jwt_required()
def toggle_user(user_id):
    claims = get_jwt()

    if claims['role'] != 'admin':
        return jsonify({'msg': 'Unauthorized'}), 403

    user = User.query.get(user_id)

    if not user:
        return jsonify({'msg': 'User not found'}), 404

    user.is_approved = not user.is_approved
    db.session.commit()

    return jsonify({'msg': 'Status updated'})

@app.route('/admin/jobs', methods=['GET'])
@jwt_required()
@cache.cached(
    timeout=120,
    key_prefix=lambda: f"admin_{get_jwt_identity()}_jobs"
)
def admin_jobs():
    claims = get_jwt()

    if claims['role'] != 'admin':
        return jsonify({'msg': 'Unauthorized'}), 403

    jobs = Job.query.all()

    result = []
    for j in jobs:
        company = User.query.get(j.company_id)

        result.append({
            "id": j.id,
            "title": j.title,
            "location": j.location,
            "salary": j.salary,
            "status": j.status,
            "company_name": company.name if company else "Unknown"
        })

    return jsonify(result)

@app.route('/admin/applications', methods=['GET'])
@jwt_required()
def admin_get_applications():
    claims = get_jwt()

    if claims['role'] != 'admin':
        return jsonify({'msg': 'Unauthorized'}), 403

    apps = JobApplication.query.all()

    result = []

    for a in apps:
        student = a.student
        student_user = student.user_br

        job = a.job
        company = User.query.get(job.company_id)

        result.append({
            "application_id": a.id,
            "student_name": student_user.name,
            "student_email": student_user.email,
            "job_title": job.title,
            "company_name": company.name if company else "Unknown",
            "status": a.status,
            "interview_date": a.interview_date,
            "interview_link": a.interview_link
        })

    return jsonify(result)

@app.route('/admin/jobs/<int:job_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_job(job_id):
    claims = get_jwt()

    if claims['role'] != 'admin':
        return jsonify({'msg': 'Unauthorized'}), 403

    job = Job.query.get(job_id)

    if not job:
        return jsonify({'msg': 'Job not found'}), 404

    JobApplication.query.filter_by(job_id=job_id).delete()

    db.session.delete(job)
    db.session.commit()

    return jsonify({'msg': 'Job deleted successfully'}), 200

@app.route("/student/jobs", methods=["GET"])
@jwt_required()
@cache.cached(
    timeout=60,
    key_prefix=lambda: f"user_{get_jwt_identity()}_jobs",
    query_string=True
)
def student_jobs():
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "student":
        return jsonify({"msg": "Unauthorized"}), 403

    jobs = Job.query.join(User, Job.company_id == User.ids).filter(
        Job.status == "active",
        User.is_approved == True
    ).all() 

    result = []

    student = StudentProfile.query.filter_by(user_id=user_id).first()

    applied_job_ids = set(
        a.job_id for a in JobApplication.query.filter_by(student_id=student.p_id).all()
    ) if student else set()

    for j in jobs:
        company = User.query.get(j.company_id)

        result.append({
            "id": j.id,
            "title": j.title,
            "location": j.location,
            "salary": j.salary,
            "description": j.description,
            "skills": j.skills,
            "experience": j.experience,
            "benefits": j.benefits,
            "company_name": company.name if company else "Unknown",
            "applied": j.id in applied_job_ids 
        })

    return jsonify(result)

@app.route("/student/apply/<int:job_id>", methods=["POST"])
@jwt_required()
def apply_job(job_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "student":
        return jsonify({"msg": "Unauthorized"}), 403

    student = StudentProfile.query.filter_by(user_id=user_id).first()

    if not student:
        return jsonify({"msg": "Student profile not found"}), 404

    if not student.cgpa:
        return jsonify({"msg": "Please complete your profile (CGPA required)"}), 400

    # prevent duplicate apply
    existing = JobApplication.query.filter_by(
        job_id=job_id,
        student_id=student.p_id
    ).first()

    if existing:
        return jsonify({"msg": "Already applied"}), 400

    new_app = JobApplication(
        job_id=job_id,
        student_id=student.p_id
    )

    db.session.add(new_app)
    db.session.commit()
    
    cache.delete_memoized(student_applications) 
    cache.delete_memoized(student_jobs)    
    cache.delete_memoized(get_company_applicants)

    return jsonify({"msg": "Applied successfully"}), 201

@app.route("/student/applications", methods=["GET"])
@jwt_required()
@cache.cached(
    timeout=30,
    key_prefix=lambda: f"user_{get_jwt_identity()}_applications"
)
def student_applications():
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "student":
        return jsonify({"msg": "Unauthorized"}), 403

    student = StudentProfile.query.filter_by(user_id=user_id).first()

    if not student:
        student = StudentProfile(user_id=user_id)
        db.session.add(student)
        db.session.commit()

    apps = JobApplication.query.filter_by(student_id=student.p_id).all()

    result = []
    for a in apps:
        result.append({
            "id": a.id,
            "job_title": a.job.title,
            "job_id": a.job.id, 
            "status": a.status,
            "feedback": a.feedback,
            "interview_date": a.interview_date,
            "interview_link": a.interview_link,
            "offer_letter": a.offer_letter
        })

    return jsonify(result)

@app.route("/student/profile", methods=["GET"])
@jwt_required()
def get_student_profile():
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "student":
        return jsonify({"msg": "Unauthorized Role"}), 403

    student = StudentProfile.query.filter_by(user_id=user_id).first()

    if not student:
        student = StudentProfile(user_id=user_id)
        db.session.add(student)

    user = db.session.get(User, user_id)

    if not student:
        return jsonify({
            "name": user.name,
            "email": user.email,
            "education": "",
            "skills": "",
            "experience": "",
            "department": "",
            "cgpa": "",
            "resume": ""
        })

    return jsonify({
        "name": user.name,
        "email": user.email,
        "education": student.education,
        "skills": student.skills,
        "experience": student.experience,
        "department": student.department,
        "cgpa": student.cgpa,
        "resume": student.resume
    })

@app.route("/student/profile", methods=["PUT"])
@jwt_required()
def update_student_profile():
    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "student":
        return jsonify({"msg": "Unauthorized"}), 403

    data = request.get_json()
    user = db.session.get(User, user_id)
    student = StudentProfile.query.filter_by(user_id=user_id).first()
    student.education = data.get("education")
    student.skills = data.get("skills")
    student.experience = data.get("experience")

    if not student:
        student = StudentProfile(user_id=user_id)
        db.session.add(student)
        db.session.commit()

    if "name" in data:
        if not data["name"].strip():
            return jsonify({"msg": "Name cannot be empty"}), 400
        user.name = data["name"]

    if "email" in data:
        email = data["email"].strip()

        if not email:
            return jsonify({"msg": "Email cannot be empty"}), 400

        existing = User.query.filter_by(email=email).first()
        if existing and existing.ids != user.ids:
            return jsonify({"msg": "Email already in use"}), 400

        user.email = email

    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            return jsonify({"msg": "Password must be at least 6 characters"}), 400

        user.password = generate_password_hash(data["password"])

    student.department = data.get("department")
    student.cgpa = data.get("cgpa")
    student.resume = data.get("resume")

    db.session.add(student)
    db.session.commit()

    cache.clear()
    return jsonify({"msg": "Profile updated successfully"})

@app.route("/company/application/<int:app_id>/place", methods=["PUT"])
@jwt_required()
def mark_placed(app_id):

    user_id = int(get_jwt_identity())
    claims = get_jwt()

    if claims["role"] != "company":
        return jsonify({"msg": "Unauthorized"}), 403

    application = JobApplication.query.get(app_id)

    if not application:
        return jsonify({"msg": "Application not found"}), 404

    job = Job.query.get(application.job_id)

    if job.company_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403

    application.status = "placed"
    db.session.commit()

    return jsonify({"msg": "Student marked as placed"})

@app.route("/student/export", methods=["POST"])
@jwt_required()
def export_data():
    user_id = int(get_jwt_identity())
    student = StudentProfile.query.filter_by(user_id=user_id).first()

    if not student:
        student = StudentProfile(user_id=user_id)
        db.session.add(student)
        db.session.commit()

    filename = export_csv(user_id)

    return jsonify({
        "msg": "Export ready",
        "filename": filename
    })

@app.route("/student/download/<filename>", methods=["GET"])
@jwt_required()
def download_file(filename):
    path = os.path.join("exports", filename)
    return send_file(path, as_attachment=True)

@app.route("/reports/<filename>", methods=["GET"])
def get_report(filename):
    path = os.path.join("reports", filename)
    return send_file(path, as_attachment=True)

@app.route("/company/export", methods=["POST"])
@jwt_required()
def company_export():
    user_id = int(get_jwt_identity())

    from celery_worker import export_company_csv

    export_company_csv.delay(user_id)

    return jsonify({"msg": "Export started"})

@app.route("/company/download/<filename>")
def company_download(filename):
    import os
    from flask import send_file

    path = os.path.join("exports", filename)
    return send_file(path, as_attachment=True)

@app.route("/test-mail")
def test_mail():
    try:
        msg = Message(
            subject="Test Email 🚀",
            recipients=["portalplacement3@gmail.com"],
            body="If you see this, your Placement Portal email system works!"
        )
        mail.send(msg)
        return "Email sent successfully!"
    except Exception as e:
        return str(e)

@app.route("/admin/download-report/<filename>")
def download_report(filename):
    path = os.path.join("reports", filename)
    return send_file(path, as_attachment=True)

@app.route("/admin/generate-report")
def trigger_report():
    filename = generate_reports()
    return jsonify({"filename": filename})

#Running of Flask and Creating the Administrator assuming the superuser doesnt exist yet
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        #Fetch the Administer's Details
        existing_admin = User.query.filter_by(role = "admin").first()
        #If there's no Admin Create it with Hardcoded Predefined Values
        if not existing_admin:
           admin_db = User(
            name='admin',
            password=generate_password_hash('admin123'),
            email='admin@gmail.com',
            role='admin',
            is_approved=True
            )
           db.session.add(admin_db)
           db.session.commit()

    app.run(debug=True)