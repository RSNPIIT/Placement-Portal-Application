import sys
import os
sys.path.append(os.path.dirname(__file__))

import datetime
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
import csv

from flask_mail import Message
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

from celery.schedules import crontab

celery.conf.beat_schedule = {
    "send-reminders-every-minute": {
        "task": "celery_worker.send_interview_reminders",
        "schedule": crontab(minute="*/1"),
    }
}

@celery.task
def export_csv(user_id):
    from app import app, db, JobApplication, StudentProfile
    import time, os, csv

    with app.app_context():

        student = StudentProfile.query.filter_by(user_id=user_id).first()

        if not student:
            return None

        apps = JobApplication.query.filter_by(student_id=student.p_id).all()

        os.makedirs("exports", exist_ok=True)

        filepath = f"exports/export_{user_id}.csv"

        with open(filepath, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Job Title", "Status"])

            for a in apps:
                writer.writerow([a.job.title, a.status])

        print(f"CSV generated: {filepath}")
        return filepath 

@celery.task
def send_interview_reminders():
    from app import app, db, JobApplication
    from datetime import datetime, timedelta
    from flask_mail import Message

    with app.app_context():
        now = datetime.now()
        upcoming = now + timedelta(days = 1)

        interviews = JobApplication.query.filter(
            JobApplication.interview_date != None
        ).all()

        for i in interviews:
            interview_time = i.interview_date

            if isinstance(interview_time, str):
                try:
                    interview_time = datetime.fromisoformat(interview_time)
                except:
                    continue  

            if (
                interview_time and
                now <= interview_time <= upcoming and
                not i.reminder_sent
            ):
                try:
                    msg = Message(
                        subject="Reminder: Interview in 24 Hours ",
                        recipients=[i.student.user_br.email],
                        body=f"""
                        Hello {i.student.user_br.name},

                        You have an interview scheduled!

                        Job: {i.job.title}
                        Time: {interview_time}

                        Best of luck!
                        """
                    )

                    from app import mail
                    mail.send(msg)

                    print(f"📧 Email sent to {i.student.user_br.email}")

                    i.reminder_sent = True

                except Exception as e:
                    print("❌ Email failed:", e)

        db.session.commit()

@celery.task
def generate_reports():
    from app import app, db, Job, JobApplication
    import os, time, shutil   # 🔥 ADD shutil

    with app.app_context():
        print("📊 Generating placement PDF report...")

        jobs = Job.query.all()
        styles = getSampleStyleSheet()

        os.makedirs("reports", exist_ok=True)
        filename = f"reports/placement_report_{int(time.time())}.pdf"

        doc = SimpleDocTemplate(filename)
        elements = []

        elements.append(Paragraph("Placement Report", styles["Title"]))
        elements.append(Spacer(1, 20))

        for job in jobs:
            apps = JobApplication.query.filter_by(job_id=job.id).all()

            total = len(apps)
            selected = len([a for a in apps if a.status == "selected"])
            rejected = len([a for a in apps if a.status == "rejected"])
            shortlisted = len([a for a in apps if a.status == "shortlisted"])

            text = f"""
            Job: {job.title}<br/>
            Location: {job.location}<br/>
            Total Applications: {total}<br/>
            Shortlisted: {shortlisted}<br/>
            Selected: {selected}<br/>
            Rejected: {rejected}<br/><br/>
            """

            elements.append(Paragraph(text, styles["Normal"]))
            elements.append(Spacer(1, 15))

        doc.build(elements)

        print(f"📄 PDF Report generated: {filename}")

        # 🔥 ADD THIS BLOCK (IMPORTANT)
        latest_path = "reports/placement_report_latest.pdf"
        shutil.copy(filename, latest_path)

        print("📄 Latest report updated")

        return filename

@celery.task
def export_company_csv(user_id):
    writer.writerow([
        "Job Title",
        "Location",
        "Total Applicants",
        "Shortlisted",
        "Selected",
        "Rejected"
    ])

    for job in jobs:
        apps = JobApplication.query.filter_by(job_id=job.id).all()

        total = len(apps)
        shortlisted = len([a for a in apps if a.status == "shortlisted"])
        selected = len([a for a in apps if a.status == "selected"])
        rejected = len([a for a in apps if a.status == "rejected"])

        writer.writerow([f"Report Generated At: {datetime.datetime.now()}"])
        writer.writerow([])  

        writer.writerow([
            job.title,
            job.location,
            total,
            shortlisted,
            selected,
            rejected
        ])

def send_email(to, subject, body):
    msg = Message(
        subject=subject,
        recipients=[to],
        body=body
    )
    mail.send(msg)

import celery_worker