from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import sqlite3
import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "your-email@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "your-app-password"    # Replace with your app password
ADMIN_EMAIL = "admin@virtualislamicuniversity.com"  # Where to receive submissions

# Database setup
def init_db():
    conn = sqlite3.connect('university_data.db')
    cursor = conn.cursor()
    
    # Contact submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Admission applications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admission_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            father_name TEXT NOT NULL,
            cnic TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            date_of_birth DATE NOT NULL,
            gender TEXT NOT NULL,
            address TEXT NOT NULL,
            education TEXT NOT NULL,
            course TEXT NOT NULL,
            application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    conn.commit()
    conn.close()

def send_email(to_email, subject, body, is_html=False):
    """Send email notification"""
    try:
        msg = MimeMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if is_html:
            msg.attach(MimeText(body, 'html'))
        else:
            msg.attach(MimeText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@app.route('/')
def home():
    return jsonify({
        "message": "Virtual Islamic University Backend API",
        "status": "active",
        "endpoints": {
            "contact": "/submit-contact",
            "admission": "/submit-admission",
            "applications": "/admin/applications",
            "contacts": "/admin/contacts"
        }
    })

@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    """Handle contact form submissions from index.html"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Save to database
        conn = sqlite3.connect('university_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contact_submissions (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data['email'], data['subject'], data['message']))
        
        submission_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Send notification email to admin
        admin_subject = f"New Contact Form Submission - {data['subject']}"
        admin_body = f"""
        نیا رابطہ پیغام موصول ہوا:
        
        نام: {data['name']}
        ای میل: {data['email']}
        موضوع: {data['subject']}
        پیغام: {data['message']}
        
        وقت: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Submission ID: {submission_id}
        """
        
        send_email(ADMIN_EMAIL, admin_subject, admin_body)
        
        # Send confirmation email to user
        user_subject = "آپ کا پیغام موصول ہوا - Virtual Islamic University"
        user_body = f"""
        السلام علیکم {data['name']},
        
        آپ کا پیغام کامیابی سے موصول ہوا ہے۔
        موضوع: {data['subject']}
        
        ہم جلد ہی آپ سے رابطہ کریں گے۔
        
        شکریہ!
        Virtual Islamic University Team
        info@virtualislamicuniversity.com
        +92 (345) 555-6654
        """
        
        send_email(data['email'], user_subject, user_body)
        
        return jsonify({
            'success': True,
            'message': 'پیغام کامیابی سے بھیج دیا گیا',
            'submission_id': submission_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit-admission', methods=['POST'])
def submit_admission():
    """Handle admission form submissions from admission.html"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'fatherName', 'cnic', 'email', 
                          'phone', 'dateOfBirth', 'gender', 'address', 'education', 'course']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Save to database
        conn = sqlite3.connect('university_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO admission_applications 
            (first_name, last_name, father_name, cnic, email, phone, 
             date_of_birth, gender, address, education, course)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['firstName'], data['lastName'], data['fatherName'], 
            data['cnic'], data['email'], data['phone'], data['dateOfBirth'],
            data['gender'], data['address'], data['education'], data['course']
        ))
        
        application_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Send notification email to admin
        admin_subject = f"New Admission Application - {data['firstName']} {data['lastName']}"
        admin_body = f"""
        نئی داخلہ درخواست موصول ہوئی:
        
        نام: {data['firstName']} {data['lastName']}
        والد کا نام: {data['fatherName']}
        CNIC: {data['cnic']}
        ای میل: {data['email']}
        فون: {data['phone']}
        تاریخ پیدائش: {data['dateOfBirth']}
        جنس: {data['gender']}
        پتہ: {data['address']}
        تعلیم: {data['education']}
        کورس: {data['course']}
        
        Application ID: {application_id}
        وقت: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        send_email(ADMIN_EMAIL, admin_subject, admin_body)
        
        # Send confirmation email to applicant
        user_subject = "داخلہ درخواست موصول ہوئی - Virtual Islamic University"
        user_body = f"""
        السلام علیکم {data['firstName']} {data['lastName']},
        
        آپ کی داخلہ درخواست کامیابی سے موصول ہوئی ہے۔
        
        Application ID: VIU-{application_id:06d}
        منتخب کردہ کورس: {data['course']}
        
        ہم جلد ہی آپ کی درخواست کا جائزہ لے کر آپ سے رابطہ کریں گے۔
        اپنا Application ID محفوظ رکھیں۔
        
        شکریہ!
        Virtual Islamic University Admissions Team
        info@virtualislamicuniversity.com
        +92 (345) 555-6654
        """
        
        send_email(data['email'], user_subject, user_body)
        
        return jsonify({
            'success': True,
            'message': 'داخلہ درخواست کامیابی سے جمع ہوئی',
            'application_id': f'VIU-{application_id:06d}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/applications', methods=['GET'])
def get_applications():
    """Get all admission applications (Admin only)"""
    try:
        conn = sqlite3.connect('university_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM admission_applications 
            ORDER BY application_date DESC
        ''')
        
        columns = [description[0] for description in cursor.description]
        applications = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'applications': applications,
            'total': len(applications)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/contacts', methods=['GET'])
def get_contacts():
    """Get all contact submissions (Admin only)"""
    try:
        conn = sqlite3.connect('university_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM contact_submissions 
            ORDER BY submission_date DESC
        ''')
        
        columns = [description[0] for description in cursor.description]
        contacts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'contacts': contacts,
            'total': len(contacts)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the server
    app.run(debug=True, host='0.0.0.0', port=5000)

"""
Setup Instructions for Flask Backend:

1. Install required packages:
   pip install flask flask-cors

2. Configure email settings:
   - Use Gmail App Password (not regular password)
   - Enable 2-factor authentication
   - Generate app password: https://support.google.com/accounts/answer/185833

3. Update the following variables:
   - EMAIL_ADDRESS: Your Gmail address
   - EMAIL_PASSWORD: Your Gmail app password
   - ADMIN_EMAIL: Where to receive form submissions

4. Run the server:
   python flask-backend.py

5. Update your HTML forms to use these endpoints:
   - Contact form: POST to http://localhost:5000/submit-contact
   - Admission form: POST to http://localhost:5000/submit-admission

6. For production deployment, consider:
   - Using environment variables for sensitive data
   - Adding authentication for admin endpoints
   - Using a production WSGI server like Gunicorn
   - Setting up a reverse proxy with Nginx
"""
