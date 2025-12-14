from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
from datetime import datetime
import re
from functools import wraps
import hashlib
import os
os.environ["LANG"] = "C.UTF-8"
os.environ["LC_ALL"] = "C.UTF-8"

# Load environment variables
# Load .env only if not in production
if os.environ.get("FLASK_ENV") != "production":
    load_dotenv()
# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-123456789')

# Database configuration - use PostgreSQL in production, SQLite in development
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Fix for newer SQLAlchemy versions
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///instance/university_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration for consistent behavior across environments
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Important for cross-origin requests
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
app.config['SESSION_COOKIE_NAME'] = 'viu_admin_session'
# Make sessions expire when browser closes (session cookies only)
app.config['SESSION_PERMANENT'] = False  # This makes sessions non-persistent by default
# Ensure session cookies work in development
app.config['SESSION_COOKIE_DOMAIN'] = None  # Let Flask handle domain automatically

# Import datetime for session management
from datetime import datetime, timedelta

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# Configure CORS for API endpoints only (more permissive for local dev)
# This avoids issues when accessing via VS Code Live Server or LAN IPs
# Simplest and most permissive CORS during local development
CORS(app,
     supports_credentials=True,
     resources={r"/api/*": {
         # Allow common local dev origins (any port) and null for file://
         "origins": [r"http://127\.0\.0\.1:\d+", r"http://localhost:\d+", r"http://192\.168\.\d+\.\d+:\d+", "null"],
         "allow_headers": ["Content-Type", "Authorization"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "supports_credentials": True
     }})

# Database Models
class ContactSubmission(db.Model):
    __tablename__ = 'contact_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='new')  # new, read, replied
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'subject': self.subject,
            'message': self.message,
            'submission_date': self.submission_date.isoformat(),
            'status': self.status
        }

class AdmissionApplication(db.Model):
    __tablename__ = 'admission_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    cnic = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text, nullable=False)
    education = db.Column(db.String(50), nullable=False)
    course = db.Column(db.String(50), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    application_number = db.Column(db.String(20), unique=True)
    
    def __init__(self, **kwargs):
        super(AdmissionApplication, self).__init__(**kwargs)
        # Application number will be set after database flush to get proper ID
    
    def to_dict(self):
        return {
            'id': self.id,
            'application_number': self.application_number,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'father_name': self.father_name,
            'cnic': self.cnic,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'address': self.address,
            'education': self.education,
            'course': self.course,
            'application_date': self.application_date.isoformat(),
            'status': self.status
        }

# Admin authentication
ADMIN_CREDENTIALS = {
    'username': os.getenv('ADMIN_USERNAME', 'admin'),
    'password': os.getenv('ADMIN_PASSWORD', 'admin@123')
}

# Authentication decorator with session timeout check
def require_admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if not session.get('admin_logged_in'):
            # For HTML requests, redirect to login page
            if request.endpoint in ['admin_dashboard']:
                return redirect('/admin_login.html')
            # For API requests, return JSON error
            return jsonify({
                'success': False,
                'error': 'Unauthorized access. Please login as admin.',
                'redirect': '/admin_login.html',
                'reason': 'not_logged_in'
            }), 401
        
        # Check session timeout
        last_activity_str = session.get('last_activity')
        if last_activity_str:
            try:
                last_activity = datetime.fromisoformat(last_activity_str)
                time_diff = datetime.now() - last_activity
                
                # Session timeout after 30 minutes of inactivity
                if time_diff.total_seconds() > 1800:  # 30 minutes
                    session.clear()
                    # For HTML requests, redirect to login page
                    if request.endpoint in ['admin_dashboard']:
                        return redirect('/admin_login.html')
                    # For API requests, return JSON error
                    return jsonify({
                        'success': False,
                        'error': 'Session expired. Please login again.',
                        'redirect': '/admin_login.html',
                        'reason': 'session_expired'
                    }), 401
                
                # Update last activity timestamp
                session['last_activity'] = datetime.now().isoformat()
                
            except ValueError:
                # Invalid timestamp, clear session
                session.clear()
                # For HTML requests, redirect to login page
                if request.endpoint in ['admin_dashboard']:
                    return redirect('/admin_login.html')
                # For API requests, return JSON error
                return jsonify({
                    'success': False,
                    'error': 'Invalid session. Please login again.',
                    'redirect': '/admin_login.html',
                    'reason': 'invalid_session'
                }), 401
        
        return f(*args, **kwargs)
    return decorated_function

# Utility Functions
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_cnic(cnic):
    pattern = r'^\d{5}-\d{7}-\d{1}$'
    return re.match(pattern, cnic) is not None

def validate_phone(phone):
    pattern = r'^\+92[0-9]{10}$'
    return re.match(pattern, phone) is not None

def send_email_notification(to_email, subject, body, html_body=None):
    """Send email notification"""
    try:
        # Check if email configuration is properly set
        if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
            print("Email configuration missing: MAIL_USERNAME or MAIL_PASSWORD not set")
            return False, "Email configuration is not properly set up"
            
        if app.config['MAIL_USERNAME'] == 'your-email@gmail.com' or app.config['MAIL_PASSWORD'] == 'your-gmail-app-password-here':
            print("Email configuration contains placeholder values")
            return False, "Email configuration contains placeholder values. Please update your .env file with actual Gmail credentials."
        
        msg = Message(
            subject=subject,
            sender=app.config['MAIL_USERNAME'],
            recipients=[to_email],
            body=body,
            html=html_body
        )
        mail.send(msg)
        return True, "Email sent successfully"
    except Exception as e:
        error_msg = f"Email error: {str(e)}"
        print(error_msg)
        return False, error_msg

# Routes
@app.route('/api')
@app.route('/api/')
def api_home():
    """API home endpoint"""
    return jsonify({
        "message": "Virtual Islamic University Backend API",
        "university": os.getenv('UNIVERSITY_NAME_URDU', 'ورچوئل اسلامک یونیورسٹی'),
        "status": "active",
        "version": "1.0.0",
        "endpoints": {
            "contact": "/api/submit-contact",
            "admission": "/api/submit-admission",
            "applications": "/api/admin/applications",
            "contacts": "/api/admin/contacts",
            "stats": "/api/admin/stats",
            "login": "/api/admin/login",
            "logout": "/api/admin/logout"
        }
    })

# Serve static HTML files
@app.route('/')
@app.route('/index.html')
def index():
    """Serve main index page"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Index page not found", 404

# Admin Authentication Routes
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'براہ کرم یوزر نیم اور پاس ورڈ درج کریں'
            }), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Check credentials
        if (username == ADMIN_CREDENTIALS['username'] and 
            password == ADMIN_CREDENTIALS['password']):
            
            # Set session with timestamp for timeout management
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['login_time'] = datetime.now().isoformat()
            session['last_activity'] = datetime.now().isoformat()
            # Keep session non-permanent so it expires when browser closes
            session.permanent = False
            
            return jsonify({
                'success': True,
                'message': 'کامیابی سے لاگ ان ہو گئے',
                'redirect': '/admin_dashboard.html'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'غلط یوزر نیم یا پاس ورڈ'
            }), 401
            
    except Exception as e:
        print(f"Admin login error: {e}")
        return jsonify({
            'success': False,
            'error': 'لاگ ان میں خرابی'
        }), 500

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout endpoint"""
    # Clear all session data
    session.clear()
    
    return jsonify({
        'success': True,
        'message': 'کامیابی سے لاگ آؤٹ ہو گئے'
    })

@app.route('/api/admin/check-auth', methods=['GET'])
def check_admin_auth():
    """Check if admin is authenticated"""
    if session.get('admin_logged_in'):
        return jsonify({
            'success': True,
            'authenticated': True,
            'username': session.get('admin_username')
        })
    else:
        return jsonify({
            'success': True,
            'authenticated': False
        })

@app.route('/api/admin/debug-session', methods=['GET'])
def debug_session():
    """Debug session information (development only)"""
    if not app.debug:
        return jsonify({'error': 'Debug mode only'}), 403
    
    return jsonify({
        'session_data': dict(session),
        'session_id': session.get('_id', 'No session ID'),
        'session_permanent': session.permanent,
        'cookies_received': dict(request.cookies),
        'headers': dict(request.headers)
    })

@app.route('/api/admin/clear-session', methods=['POST'])
def clear_session():
    """Clear admin session (development only)"""
    if not app.debug:
        return jsonify({'error': 'Debug mode only'}), 403
    
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Session cleared successfully'
    })

# Route to serve admin dashboard with authentication check
@app.route('/admin_dashboard.html')
@require_admin_auth
def admin_dashboard():
    """Serve admin dashboard with authentication check"""
    try:
        with open('admin_dashboard.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Admin dashboard file not found", 404

@app.route('/admin_login.html')
def admin_login_page():
    """Serve admin login page"""
    try:
        with open('admin_login.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Admin login file not found", 404

@app.route('/admission.html')
def admission():
    """Serve admission page"""
    try:
        with open('admission.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Admission page not found", 404

@app.route('/courses.html')
def courses():
    """Serve courses page"""
    try:
        with open('courses.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Courses page not found", 404

@app.route('/faculty.html')
def faculty():
    """Serve faculty page"""
    try:
        with open('faculty.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Faculty page not found", 404

@app.route('/donation.html')
def donation():
    """Serve donation page"""
    try:
        with open('donation.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Donation page not found", 404

@app.route('/api/submit-contact', methods=['POST'])
def submit_contact():
    """Handle contact form submissions from index.html"""
    try:
        # Debug logging to confirm requests reach the server
        print("/api/submit-contact called | Origin:", request.headers.get('Origin'), "| IP:", request.remote_addr)
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({
                    'success': False,
                    'error': f'فیلڈ {field} لازمی ہے'
                }), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'error': 'براہ کرم صحیح ای میل ایڈریس درج کریں'
            }), 400
        
        # Create contact submission
        contact = ContactSubmission(
            name=data['name'].strip(),
            email=data['email'].strip().lower(),
            subject=data['subject'].strip(),
            message=data['message'].strip()
        )
        
        db.session.add(contact)
        db.session.commit()
        
        # Email notifications disabled temporarily to prevent timeout
        # TODO: Configure email settings properly and re-enable
        print(f"Contact form submitted by {data['name']} <{data['email']}>: {data['subject']}")
        print(f"Message: {data['message']}")
        
        # You can uncomment these lines once email is properly configured:
        # send_email_notification(os.getenv('ADMIN_EMAIL'), admin_subject, admin_body)
        # send_email_notification(data['email'], user_subject, user_body)
        
        return jsonify({
            'success': True,
            'message': 'آپ کا پیغام کامیابی سے بھیج دیا گیا',
            'submission_id': contact.id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Contact submission error: {e}")
        return jsonify({
            'success': False,
            'error': 'سرور میں خرابی، براہ کرم دوبارہ کوشش کریں'
        }), 500

@app.route('/api/submit-admission', methods=['POST'])
def submit_admission():
    """Handle admission form submissions from admission.html"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'firstName', 'lastName', 'fatherName', 'cnic', 'email',
            'phone', 'dateOfBirth', 'gender', 'address', 'education', 'course'
        ]
        
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({
                    'success': False,
                    'error': f'فیلڈ {field} لازمی ہے'
                }), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'error': 'براہ کرم صحیح ای میل ایڈریس درج کریں'
            }), 400
        
        # Validate CNIC format
        if not validate_cnic(data['cnic']):
            return jsonify({
                'success': False,
                'error': 'براہ کرم CNIC صحیح فارمیٹ میں درج کریں (12345-1234567-1)'
            }), 400
        
        # Validate phone format
        if not validate_phone(data['phone']):
            return jsonify({
                'success': False,
                'error': 'براہ کرم فون نمبر صحیح فارمیٹ میں درج کریں (+923001234567)'
            }), 400
        
        # Check if CNIC or email already exists
        existing_app = AdmissionApplication.query.filter(
            (AdmissionApplication.cnic == data['cnic']) |
            (AdmissionApplication.email == data['email'].lower())
        ).first()
        
        if existing_app:
            return jsonify({
                'success': False,
                'error': 'اس CNIC یا ای میل سے پہلے سے درخواست موجود ہے'
            }), 400
        
        # Parse date
        try:
            dob = datetime.strptime(data['dateOfBirth'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'براہ کرم صحیح تاریخ پیدائش درج کریں'
            }), 400
        
        # Create admission application
        application = AdmissionApplication(
            first_name=data['firstName'].strip(),
            last_name=data['lastName'].strip(),
            father_name=data['fatherName'].strip(),
            cnic=data['cnic'].strip(),
            email=data['email'].strip().lower(),
            phone=data['phone'].strip(),
            date_of_birth=dob,
            gender=data['gender'],
            address=data['address'].strip(),
            education=data['education'],
            course=data['course']
        )
        
        db.session.add(application)
        db.session.flush()  # To get the ID
        
        # Generate application number with correct format
        application.application_number = f"VIU-{datetime.now().year}-{application.id:06d}"
        
        db.session.commit()
        
        # Send notification email to admin
        admin_subject = f"نئی داخلہ درخواست - {data['firstName']} {data['lastName']}"
        admin_body = f"""
نئی داخلہ درخواست موصول ہوئی:

Application Number: {application.application_number}

طالب علم کی تفصیلات:
نام: {data['firstName']} {data['lastName']}
والد کا نام: {data['fatherName']}
CNIC: {data['cnic']}
ای میل: {data['email']}
فون: {data['phone']}
تاریخ پیدائش: {data['dateOfBirth']}
جنس: {data['gender']}
پتہ: {data['address']}
تعلیمی قابلیت: {data['education']}
منتخب کردہ کورس: {data['course']}

درخواست کی تاریخ: {application.application_date.strftime('%Y-%m-%d %H:%M:%S')}

Virtual Islamic University Admissions
        """
        
        send_email_notification(
            os.getenv('ADMIN_EMAIL'),
            admin_subject,
            admin_body
        )
        
        # Send confirmation email to applicant
        course_names = {
            'quran': 'فہم القرآن',
            'arabic': 'اللغة العربية',
            'islamic-studies': 'علوم الدین'
        }
        
        user_subject = "داخلہ درخواست موصول ہوئی - Virtual Islamic University"
        user_body = f"""
السلام علیکم {data['firstName']} {data['lastName']},

آپ کی داخلہ درخواست کامیابی سے موصول ہوئی ہے۔

Application Number: {application.application_number}
منتخب کردہ کورس: {course_names.get(data['course'], data['course'])}

ہم جلد ہی آپ کی درخواست کا جائزہ لے کر آپ سے رابطہ کریں گے۔
اپنا Application Number محفوظ رکھیں۔

شکریہ!
Virtual Islamic University Admissions Team
{os.getenv('UNIVERSITY_EMAIL')}
{os.getenv('UNIVERSITY_PHONE')}
        """
        
        send_email_notification(data['email'], user_subject, user_body)
        
        return jsonify({
            'success': True,
            'message': 'آپ کی داخلہ درخواست کامیابی سے جمع ہوئی',
            'application_number': application.application_number,
            'application_id': application.id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Admission submission error: {e}")
        return jsonify({
            'success': False,
            'error': 'سرور میں خرابی، براہ کرم دوبارہ کوشش کریں'
        }), 500

@app.route('/api/admin/applications', methods=['GET'])
@require_admin_auth
def get_applications():
    """Get all admission applications (Admin endpoint)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', None)
        
        query = AdmissionApplication.query
        
        if status:
            query = query.filter(AdmissionApplication.status == status)
        
        applications = query.order_by(AdmissionApplication.application_date.desc())\
                          .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'applications': [app.to_dict() for app in applications.items],
            'total': applications.total,
            'pages': applications.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        print(f"Get applications error: {e}")
        return jsonify({
            'success': False,
            'error': 'ڈیٹا لوڈ کرنے میں خرابی'
        }), 500

@app.route('/api/admin/contacts', methods=['GET'])
@require_admin_auth
def get_contacts():
    """Get all contact submissions (Admin endpoint)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', None)
        
        query = ContactSubmission.query
        
        if status:
            query = query.filter(ContactSubmission.status == status)
        
        contacts = query.order_by(ContactSubmission.submission_date.desc())\
                       .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'contacts': [contact.to_dict() for contact in contacts.items],
            'total': contacts.total,
            'pages': contacts.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        print(f"Get contacts error: {e}")
        return jsonify({
            'success': False,
            'error': 'ڈیٹا لوڈ کرنے میں خرابی'
        }), 500

@app.route('/api/admin/stats', methods=['GET'])
@require_admin_auth
def get_stats():
    """Get dashboard statistics (Admin endpoint)"""
    try:
        total_applications = AdmissionApplication.query.count()
        pending_applications = AdmissionApplication.query.filter_by(status='pending').count()
        approved_applications = AdmissionApplication.query.filter_by(status='approved').count()
        rejected_applications = AdmissionApplication.query.filter_by(status='rejected').count()
        total_contacts = ContactSubmission.query.count()
        new_contacts = ContactSubmission.query.filter_by(status='new').count()
        
        # Applications by course
        course_stats = db.session.query(
            AdmissionApplication.course,
            db.func.count(AdmissionApplication.id)
        ).group_by(AdmissionApplication.course).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_applications': total_applications,
                'pending_applications': pending_applications,
                'approved_applications': approved_applications,
                'rejected_applications': rejected_applications,
                'total_contacts': total_contacts,
                'new_contacts': new_contacts,
                'course_distribution': [
                    {'course': course, 'count': count} for course, count in course_stats
                ]
            }
        })
        
    except Exception as e:
        print(f"Get stats error: {e}")
        return jsonify({
            'success': False,
            'error': 'اعداد و شمار لوڈ کرنے میں خرابی'
        }), 500

@app.route('/api/admin/applications/<int:app_id>/approve', methods=['POST'])
@require_admin_auth
def approve_application(app_id):
    """Approve an admission application"""
    try:
        application = AdmissionApplication.query.get_or_404(app_id)
        application.status = 'approved'
        db.session.commit()
        
        # Send approval email to applicant
        course_names = {
            'quran': 'فہم القرآن',
            'arabic': 'اللغة العربية',
            'islamic-studies': 'علوم الدین'
        }
        
        subject = "داخلہ منظور! - Virtual Islamic University"
        body = f"""
السلام علیکم {application.first_name} {application.last_name},

مبارک ہو! آپ کی داخلہ درخواست منظور ہو گئی ہے۔

Application Number: {application.application_number}
منتخب کردہ کورس: {course_names.get(application.course, application.course)}

ہم جلد ہی آپ کو کورس کی تفصیلات اور شروعات کی تاریخ کے بارے میں مطلع کریں گے۔

خوش آمدید Virtual Islamic University میں!

Virtual Islamic University Admissions Team
{os.getenv('UNIVERSITY_EMAIL')}
{os.getenv('UNIVERSITY_PHONE')}
        """
        
        send_email_notification(application.email, subject, body)
        
        return jsonify({
            'success': True,
            'message': 'درخواست منظور کر دی گئی'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Approve application error: {e}")
        return jsonify({
            'success': False,
            'error': 'درخواست منظور کرنے میں خرابی'
        }), 500

@app.route('/api/admin/applications/<int:app_id>/reject', methods=['POST'])
@require_admin_auth
def reject_application(app_id):
    """Reject an admission application"""
    try:
        data = request.get_json() or {}
        rejection_reason = data.get('reason', 'شرائط پوری نہیں ہونا')
        
        application = AdmissionApplication.query.get_or_404(app_id)
        application.status = 'rejected'
        db.session.commit()
        
        # Send rejection email to applicant
        subject = "داخلہ درخواست - Virtual Islamic University"
        body = f"""
السلام علیکم {application.first_name} {application.last_name},

ہمیں افسوس ہے کہ اس وقت آپ کی داخلہ درخواست منظور نہیں کی جا سکی۔

Application Number: {application.application_number}
وجہ: {rejection_reason}

آپ مستقبل میں دوبارہ درخواست دے سکتے ہیں۔

شکریہ!
Virtual Islamic University Admissions Team
{os.getenv('UNIVERSITY_EMAIL')}
{os.getenv('UNIVERSITY_PHONE')}
        """
        
        send_email_notification(application.email, subject, body)
        
        return jsonify({
            'success': True,
            'message': 'درخواست مسترد کر دی گئی'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Reject application error: {e}")
        return jsonify({
            'success': False,
            'error': 'درخواست مسترد کرنے میں خرابی'
        }), 500

@app.route('/api/admin/applications/<int:app_id>', methods=['DELETE'])
@require_admin_auth
def delete_application(app_id):
    """Delete an admission application"""
    try:
        application = AdmissionApplication.query.get_or_404(app_id)
        db.session.delete(application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'درخواست ڈیلیٹ کر دی گئی'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete application error: {e}")
        return jsonify({
            'success': False,
            'error': 'درخواست ڈیلیٹ کرنے میں خرابی'
        }), 500

@app.route('/api/admin/contacts/<int:contact_id>', methods=['DELETE'])
@require_admin_auth
def delete_contact(contact_id):
    """Delete a contact message"""
    try:
        contact = ContactSubmission.query.get_or_404(contact_id)
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'پیغام ڈیلیٹ کر دیا گیا'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete contact error: {e}")
        return jsonify({
            'success': False,
            'error': 'پیغام ڈیلیٹ کرنے میں خرابی'
        }), 500

@app.route('/api/admin/contacts/<int:contact_id>/mark-read', methods=['POST'])
@require_admin_auth
def mark_contact_read(contact_id):
    """Mark a contact message as read"""
    try:
        contact = ContactSubmission.query.get_or_404(contact_id)
        contact.status = 'read'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'پیغام پڑھا ہوا نشان زد کر دیا گیا'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Mark contact read error: {e}")
        return jsonify({
            'success': False,
            'error': 'پیغام اپڈیٹ کرنے میں خرابی'
        }), 500

@app.route('/api/admin/contacts/<int:contact_id>/reply', methods=['POST'])
@require_admin_auth
def reply_to_contact(contact_id):
    """Send a reply to a contact message"""
    try:
        data = request.get_json()
        
        if not data or not data.get('reply_message'):
            return jsonify({
                'success': False,
                'error': 'جواب کا پیغام لازمی ہے'
            }), 400
        
        reply_message = data['reply_message'].strip()
        if not reply_message:
            return jsonify({
                'success': False,
                'error': 'جواب کا پیغام لازمی ہے'
            }), 400
        
        # Get the original contact message
        contact = ContactSubmission.query.get_or_404(contact_id)
        
        # Send reply email to the user
        subject = f"جواب: {contact.subject} - Virtual Islamic University"
        body = f"""
السلام علیکم {contact.name},

آپ کے پیغام کا جواب:

اصل پیغام: "{contact.subject}"
آپ کا پیغام: "{contact.message}"

--- ہمارا جواب ---
{reply_message}
--- جواب کا اختتام ---

اگر آپ کے کوئی اور سوالات ہیں تو براہ کرم ہم سے رابطہ کریں۔

شکریہ!
Virtual Islamic University Team
{os.getenv('UNIVERSITY_EMAIL')}
{os.getenv('UNIVERSITY_PHONE')}
        """
        
        # Send the reply email
        email_sent, email_message = send_email_notification(contact.email, subject, body)
        
        if email_sent:
            # Mark the contact as replied
            contact.status = 'replied'
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'جواب کامیابی سے بھیج دیا گیا'
            })
        else:
            return jsonify({
                'success': False,
                'error': email_message or 'ای میل بھیجنے میں خرابی ہوئی'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        print(f"Reply to contact error: {e}")
        return jsonify({
            'success': False,
            'error': 'جواب بھیجنے میں خرابی'
        }), 500

# Static file serving routes
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve static assets (CSS, JS, images, fonts)"""
    try:
        return send_from_directory('assets', filename)
    except FileNotFoundError:
        abort(404)

# Serve Mehr Nastaliq Web fonts from hyphenated folder (canonical path used in CSS)
@app.route('/mehr-nastaliq-web-font-v2.0/<path:filename>')
def serve_mehr_fonts_hyphenated(filename):
    """Serve Mehr Nastaliq Web font files from hyphenated folder"""
    try:
        return send_from_directory('mehr-nastaliq-web-font-v2.0', filename)
    except FileNotFoundError:
        abort(404)

@app.route('/mehr nastaliq web font v 2.0/<path:filename>')
def serve_fonts(filename):
    """Serve font files"""
    try:
        return send_from_directory('mehr nastaliq web font v 2.0', filename)
    except FileNotFoundError:
        abort(404)

# Serve Jameel Noori Nastaleeq fonts root
@app.route('/jameel-noori-nastaleeq/<path:filename>')
def serve_jameel_fonts(filename):
    """Serve Jameel Noori Nastaleeq font files"""
    try:
        return send_from_directory('jameel-noori-nastaleeq', filename)
    except FileNotFoundError:
        abort(404)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    try:
        return send_from_directory('static', filename)
    except FileNotFoundError:
        abort(404)

@app.route('/Images/<path:filename>')
def serve_images(filename):
    """Serve image files from Images directory"""
    try:
        return send_from_directory('Images', filename)
    except FileNotFoundError:
        abort(404)

@app.route('/<path:filename>')
def serve_html_files(filename):
    """Serve HTML files and other course-related files"""
    # Only serve .html files and not conflicting paths
    if filename.endswith('.html') and not filename.startswith('api/'):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            abort(404)
    else:
        abort(404)

# Health check endpoint for Railway
@app.route('/health')
def health_check():
    """Health check endpoint for Railway monitoring"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'university': os.getenv('UNIVERSITY_NAME', 'Virtual Islamic University')
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'صفحہ موجود نہیں'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'error': 'سرور میں خرابی'
    }), 500

# Initialize database will be done in startup script

# Initialize database tables
def init_db():
    """Initialize database tables"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the application
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8000))
    )

# For production deployment (Gunicorn will import this)
# Database initialization is handled by start.py or startup scripts
