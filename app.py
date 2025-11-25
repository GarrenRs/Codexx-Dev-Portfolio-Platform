import os
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from datetime import datetime, timedelta
from functools import wraps
import io
import requests
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET",
                                "CHANGE-THIS-SECRET-KEY-IN-PRODUCTION")

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'static/assets/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['JSON_AS_ASCII'] = False
app.config['SESSION_COOKIE_SECURE'] = True  # Use HTTPS in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('backups', exist_ok=True)

# Initialize APScheduler for automatic backups
scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# Advanced Security System
# Rate Limiting: Track requests per IP
RATE_LIMIT_REQUESTS = {}  # {ip: [(timestamp, endpoint), ...]}
RATE_LIMIT_MAX_REQUESTS = 10  # Max 10 requests
RATE_LIMIT_WINDOW = 60  # Per 60 seconds

# IP Logging for security tracking
IP_LOG_FILE = 'security/ip_log.json'
os.makedirs('security', exist_ok=True)

def get_client_ip():
    """Get real client IP address"""
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))

def check_rate_limit(endpoint='contact'):
    """Check if IP is within rate limit"""
    client_ip = get_client_ip()
    current_time = time.time()
    
    if client_ip not in RATE_LIMIT_REQUESTS:
        RATE_LIMIT_REQUESTS[client_ip] = []
    
    # Clean old requests outside the window
    RATE_LIMIT_REQUESTS[client_ip] = [
        (ts, ep) for ts, ep in RATE_LIMIT_REQUESTS[client_ip]
        if current_time - ts < RATE_LIMIT_WINDOW
    ]
    
    # Check if limit exceeded
    endpoint_requests = [ep for ts, ep in RATE_LIMIT_REQUESTS[client_ip] if ep == endpoint]
    if len(endpoint_requests) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    # Add current request
    RATE_LIMIT_REQUESTS[client_ip].append((current_time, endpoint))
    return True

def log_ip_activity(activity_type, details=''):
    """Log IP activity for security tracking"""
    try:
        client_ip = get_client_ip()
        log_data = {
            'ip': client_ip,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'activity': activity_type,
            'details': details,
            'user_agent': request.headers.get('User-Agent', 'Unknown')[:100]
        }
        
        # Load existing logs
        try:
            with open(IP_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        
        logs.append(log_data)
        
        # Keep only last 1000 logs
        logs = logs[-1000:]
        
        with open(IP_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.error(f"Error logging IP activity: {str(e)}")

# Admin credentials (should be environment variables in production)
ADMIN_CREDENTIALS = {
    'username':
    os.environ.get('ADMIN_USERNAME', 'admin'),
    'password_hash':
    generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))
}

# LIVE DEMO EDITION: Demo user credentials (restricted access for live preview)
DEMO_USER_CREDENTIALS = {
    'username': 'demo_codexx',
    'password_hash': generate_password_hash('Demo_2026!'),
    'is_demo': True
}

# Telegram Bot Configuration helper functions
def load_telegram_config():
    """Load Telegram configuration from file"""
    try:
        if os.path.exists('telegram_config.json'):
            with open('telegram_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('bot_token', ''), config.get('chat_id', '')
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        app.logger.debug(f"Could not load Telegram config from file: {str(e)}")
    # Fallback to environment variables
    return os.environ.get('TELEGRAM_BOT_TOKEN', ''), os.environ.get('TELEGRAM_CHAT_ID', '')

def get_telegram_credentials():
    """Get Telegram credentials from config or env"""
    bot_token, chat_id = load_telegram_config()
    return bot_token, chat_id

# Telegram Bot Configuration - loaded at startup
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID = get_telegram_credentials()
TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


# SMTP Email Configuration helper functions
def load_smtp_config():
    """Load SMTP configuration from file"""
    try:
        if os.path.exists('smtp_config.json'):
            with open('smtp_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        app.logger.debug(f"Could not load SMTP config: {str(e)}")
    return {}


def save_smtp_config(config):
    """Save SMTP configuration to file"""
    try:
        with open('smtp_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        app.logger.error(f"Error saving SMTP config: {str(e)}")
        return False


def send_email(recipient, subject, body, html=False):
    """Send email using SMTP"""
    try:
        smtp_config = load_smtp_config()
        if not all([smtp_config.get('host'), smtp_config.get('port'), 
                    smtp_config.get('email'), smtp_config.get('password')]):
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_config.get('email')
        msg['To'] = recipient
        
        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(smtp_config.get('host'), int(smtp_config.get('port'))) as server:
            server.starttls()
            server.login(smtp_config.get('email'), smtp_config.get('password'))
            server.send_message(msg)
        
        return True
    except Exception as e:
        app.logger.error(f"Error sending email: {str(e)}")
        return False


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def load_data():
    """Load portfolio data from JSON file with error handling"""
    try:
        with open('data.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        # Initialize with default structure
        default_data = {
            'name': '',
            'title': '',
            'description': '',
            'photo': '',
            'about': '',
            'skills': [],
            'projects': [],
            'contact': {
                'email': '',
                'phone': '',
                'location': ''
            },
            'social': {},
            'messages': [],
            'visitors': {
                'total': 0,
                'today': [],
                'unique_ips': []
            },
            'settings': {
                'theme': 'luxury-gold'
            }
        }
        save_data(default_data)
        return default_data
    except json.JSONDecodeError:
        flash('Error reading data file. Please check data.json format.',
              'error')
        return {}


def save_data(data):
    """Save portfolio data to JSON file with automatic backup"""
    try:
        if os.path.exists('data.json'):
            create_backup(manual=False)

        with open('data.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.error(f"Error saving data: {str(e)}")
        flash('Error saving data. Please try again.', 'error')


def create_backup(manual=True):
    """Create a backup of data.json to backups folder"""
    try:
        if not os.path.exists('data.json'):
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f'backup_{timestamp}.json'
        backup_path = os.path.join('backups', backup_filename)
        
        with open('data.json', 'r', encoding='utf-8') as original:
            backup_content = original.read()
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(backup_content)
        
        file_size = os.path.getsize(backup_path) / 1024
        
        backup_info = {
            'filename': backup_filename,
            'timestamp': datetime.now().isoformat(),
            'size_kb': round(file_size, 2),
            'type': 'manual' if manual else 'automatic'
        }
        
        save_backup_metadata(backup_info)
        
        keep_recent_backups(max_backups=20)
        
        return backup_info
    except Exception as e:
        app.logger.error(f"Error creating backup: {str(e)}")
        return None


def save_backup_metadata(backup_info):
    """Save backup metadata to JSON file"""
    try:
        metadata_file = 'backups/backups.json'
        backups_list = []
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                backups_list = json.load(f)
        
        backups_list.append(backup_info)
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(backups_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.error(f"Error saving backup metadata: {str(e)}")


def get_backups_list():
    """Get list of all backups with metadata"""
    try:
        metadata_file = 'backups/backups.json'
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                backups = json.load(f)
                return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
        return []
    except Exception as e:
        app.logger.error(f"Error reading backups list: {str(e)}")
        return []


def keep_recent_backups(max_backups=20):
    """Keep only the most recent backups"""
    try:
        backups = get_backups_list()
        if len(backups) > max_backups:
            to_delete = backups[max_backups:]
            for backup in to_delete:
                backup_path = os.path.join('backups', backup['filename'])
                if os.path.exists(backup_path):
                    os.remove(backup_path)
            
            updated_backups = backups[:max_backups]
            with open('backups/backups.json', 'w', encoding='utf-8') as f:
                json.dump(updated_backups, f, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.error(f"Error cleaning old backups: {str(e)}")


def scheduled_backup():
    """Scheduled backup job"""
    try:
        with app.app_context():
            create_backup(manual=False)
            app.logger.info("Scheduled backup created successfully")
    except Exception as e:
        app.logger.error(f"Scheduled backup failed: {str(e)}")


def reset_demo_data():
    """Reset demo data to default state for Live Demo Edition"""
    try:
        with app.app_context():
            default_demo_data = {
                'name': 'Demo Portfolio - Codexx',
                'title': 'Web Developer & Designer',
                'description': 'Experience the power of Codexx Portfolio Platform with this interactive demo',
                'photo': 'static/assets/profile-placeholder.svg',
                'about': 'Welcome to the Codexx Portfolio Platform! This is a live demo showcasing all the features available in our professional portfolio management system. Feel free to explore and customize this demo to see how your portfolio would look.',
                'skills': [
                    {'name': 'Web Development', 'level': 90},
                    {'name': 'UI/UX Design', 'level': 85},
                    {'name': 'JavaScript', 'level': 88},
                    {'name': 'React.js', 'level': 85},
                    {'name': 'Python', 'level': 80}
                ],
                'projects': load_data().get('projects', []),
                'contact': {'email': 'demo@codexx.com', 'phone': '+1 234 567 8900', 'location': 'San Francisco, CA'},
                'social': {},
                'messages': [],
                'visitors': {'total': 0, 'today': [], 'unique_ips': []},
                'settings': {'theme': 'luxury-gold'},
                'clients': []
            }
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(default_demo_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.error(f"Demo data reset failed: {str(e)}")


scheduler.add_job(
    scheduled_backup,
    'cron',
    hour='*',
    minute=0,
    id='daily_backup',
    name='Hourly backup',
    replace_existing=True
)

scheduler.add_job(
    reset_demo_data,
    'cron',
    hour='*',
    minute=0,
    id='demo_reset',
    name='Demo data hourly reset',
    replace_existing=True
)


def login_required(f):
    """Decorator to require login"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('dashboard_login'))
        return f(*args, **kwargs)

    return decorated_function


def send_telegram_notification(message_text):
    """Send notification to Telegram"""
    # Get fresh credentials from config
    bot_token, chat_id = get_telegram_credentials()
    if not bot_token or not chat_id:
        return False
    
    try:
        # Check if message_text is already formatted (for contact forms) or needs formatting (for client updates)
        if isinstance(message_text, dict):
            # Old contact form format
            name = message_text.get('name', '')
            email = message_text.get('email', '')
            body = message_text.get('message', '')
            telegram_message = f"""
🔔 <b>New Contact Message</b>

📝 <b>Name:</b> {name}
📧 <b>Email:</b> {email}

💬 <b>Message:</b>
{body}

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            # New format (already formatted string for client updates)
            telegram_message = message_text
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': telegram_message,
            'parse_mode': 'HTML'
        }
        
        # Send in background thread to not block the request
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        app.logger.error(f"Error sending Telegram notification: {str(e)}")
        return False


def send_telegram_event_notification(event_type, details=None):
    """Send event-based notifications"""
    bot_token, chat_id = get_telegram_credentials()
    if not bot_token or not chat_id:
        return False
    
    try:
        event_messages = {
            'new_message': f"""📨 <b>New Contact Message</b>
{details}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}""",
            
            'new_project': f"""🚀 <b>New Project Added</b>
📌 {details}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}""",
            
            'project_updated': f"""✏️ <b>Project Updated</b>
📌 {details}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}""",
            
            'login_attempt': f"""🔐 <b>Dashboard Login</b>
👤 User: {details}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        }
        
        message_text = event_messages.get(event_type, f"{event_type}: {details}")
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message_text,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        app.logger.error(f"Error sending event notification: {str(e)}")
        return False


def send_event_notification_async(event_type, details=None):
    """Send event notification asynchronously"""
    thread = threading.Thread(target=send_telegram_event_notification, args=(event_type, details))
    thread.daemon = True
    thread.start()


def send_telegram_notification_async(name, email, message):
    """Send Telegram notification asynchronously"""
    bot_token, chat_id = get_telegram_credentials()
    if bot_token and chat_id:
        thread = threading.Thread(target=send_telegram_notification, args=(name, email, message))
        thread.daemon = True
        thread.start()


def save_message(name, email, message):
    """Save contact message and send notifications"""
    data = load_data()
    if 'messages' not in data:
        data['messages'] = []

    message_ids = [m.get('id', 0) for m in data.get('messages', [])]
    new_id = max(message_ids) + 1 if message_ids else 1

    client_ip = get_client_ip()
    new_message = {
        'id': new_id,
        'name': name,
        'email': email,
        'message': message,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'read': False,
        'ip': client_ip  # Log IP address
    }

    data['messages'].append(new_message)
    save_data(data)
    
    # Log the activity
    log_ip_activity('contact_message', f"From: {email}")
    
    # Send Telegram notifications
    send_telegram_notification_async(name, email, message)
    send_event_notification_async('new_message', f"📝 From: {name} ({email})\n💬 {message[:100]}...")
    
    return new_id


def get_unread_messages_count():
    """Get count of unread messages"""
    data = load_data()
    return len(
        [m for m in data.get('messages', []) if not m.get('read', False)])


def track_visitor():
    """Track visitor with improved logic"""
    data = load_data()
    if 'visitors' not in data:
        data['visitors'] = {'total': 0, 'today': [], 'unique_ips': []}

    visitor_ip = request.environ.get(
        'HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    today = datetime.now().strftime('%Y-%m-%d')

    data['visitors']['total'] = data['visitors'].get('total', 0) + 1
    data['visitors']['today'] = [
        v for v in data['visitors'].get('today', []) if v.get('date') == today
    ]
    data['visitors']['today'].append({
        'ip':
        visitor_ip,
        'timestamp':
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date':
        today
    })

    if isinstance(data['visitors'].get('unique_ips'), list):
        unique_ips_set = set(data['visitors']['unique_ips'])
    else:
        unique_ips_set = set()
    unique_ips_set.add(visitor_ip)
    data['visitors']['unique_ips'] = list(unique_ips_set)

    save_data(data)
    
    return data['visitors']['total']


def get_visitor_count():
    """Get total visitor count"""
    data = load_data()
    return data.get('visitors', {}).get('total', 0)


def mark_message_as_read(message_id):
    """Mark message as read"""
    data = load_data()
    for message in data.get('messages', []):
        if message.get('id') == message_id:
            message['read'] = True
            break
    save_data(data)


def get_clients_stats():
    """Get clients statistics"""
    data = load_data()
    clients = data.get('clients', [])

    total_clients = len(clients)
    active_clients = len([c for c in clients if c.get('status') == 'active'])
    completed_clients = len(
        [c for c in clients if c.get('status') == 'completed'])
    pending_clients = len([c for c in clients if c.get('status') == 'pending'])

    total_revenue = sum(
        float(c.get('price', 0)) for c in clients if c.get('price'))

    return {
        'total': total_clients,
        'active': active_clients,
        'completed': completed_clients,
        'pending': pending_clients,
        'revenue': total_revenue
    }


def get_current_theme():
    """Get current theme"""
    data = load_data()
    return data.get('settings', {}).get('theme', 'luxury-gold')


@app.context_processor
def inject_global_vars():
    """Make functions available in all templates"""
    return {
        'get_unread_messages_count': get_unread_messages_count,
        'get_visitor_count': get_visitor_count,
        'get_clients_stats': get_clients_stats,
        'current_year': datetime.now().year,
        'current_theme': get_current_theme(),
        'is_demo_mode': session.get('is_demo', False)
    }


# Error handlers
@app.errorhandler(400)
def bad_request(e):
    """Custom 400 error page"""
    return render_template('400.html'), 400


@app.errorhandler(403)
def forbidden(e):
    """Custom 403 error page"""
    return render_template('403.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Custom 500 error page"""
    app.logger.error(f"Server Error: {str(e)}")
    return render_template('500.html'), 500


@app.errorhandler(503)
def service_unavailable(e):
    """Custom 503 error page"""
    return render_template('503.html'), 503


@app.errorhandler(413)
def file_too_large(e):
    """File upload too large"""
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(request.url)


# Public routes
@app.route('/')
def index():
    """Main portfolio page"""
    data = load_data()
    track_visitor()
    return render_template('index.html', data=data)


@app.route('/catalog')
@login_required
def catalog():
    """Feature catalog page"""
    return render_template('catalog.html')


@app.route('/contact', methods=['POST'])
def contact():
    """Handle contact form submission with security"""
    # Check honeypot field
    honeypot = request.form.get('website', '').strip()
    if honeypot:
        # Bot detected - silently fail
        log_ip_activity('bot_detected', 'Contact form honeypot triggered')
        flash('Thank you for your message! I will get back to you soon.', 'success')
        return redirect(url_for('index') + '#contact')
    
    # Check rate limiting
    if not check_rate_limit('contact'):
        log_ip_activity('rate_limit_exceeded', 'Contact form submissions exceeded')
        flash('Too many messages. Please wait a moment before sending another message.', 'error')
        return redirect(url_for('index') + '#contact')
    
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()

    if name and email and message:
        try:
            save_message(name, email, message)
            
            # Send Telegram notification
            send_telegram_notification({
                'name': name,
                'email': email,
                'message': message
            })
            
            # Send email notification to admin
            smtp_config = load_smtp_config()
            if smtp_config.get('email'):
                email_subject = f'📬 New Contact Message from {name}'
                email_body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; color: #333;">
                        <h2 style="color: #D4AF37;">📬 New Contact Message</h2>
                        <p><strong>Name:</strong> {name}</p>
                        <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                        <p><strong>Message:</strong></p>
                        <p style="background: #f5f5f5; padding: 10px; border-left: 4px solid #D4AF37;">
                            {message.replace(chr(10), '<br>')}
                        </p>
                        <p style="margin-top: 20px; color: #666; font-size: 12px;">
                            Received at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </body>
                </html>
                """
                send_email(smtp_config.get('email'), email_subject, email_body, html=True)
            
            flash('Thank you for your message! I will get back to you soon.',
                  'success')
        except Exception as e:
            app.logger.error(f"Contact form error: {str(e)}")
            flash(
                'Sorry, there was an error sending your message. Please try again.',
                'error')
    else:
        flash('Please fill in all required fields.', 'error')

    return redirect(url_for('index') + '#contact')


@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Project detail page"""
    data = load_data()
    project = next(
        (p for p in data.get('projects', []) if p.get('id') == project_id),
        None)

    if not project:
        return render_template('404.html'), 404

    return render_template('project_detail.html', project=project, data=data)


@app.route('/sitemap.xml')
def sitemap():
    """Generate dynamic sitemap for SEO"""
    data = load_data()
    base_url = request.url_root.rstrip('/')
    
    sitemap_entries = []
    sitemap_entries.append({
        'loc': f'{base_url}/',
        'changefreq': 'weekly',
        'priority': '1.0',
        'lastmod': datetime.now().strftime('%Y-%m-%d')
    })
    
    for project in data.get('projects', []):
        sitemap_entries.append({
            'loc': f"{base_url}/project/{project['id']}",
            'changefreq': 'monthly',
            'priority': '0.8',
            'lastmod': project.get('created_at', datetime.now().strftime('%Y-%m-%d')).split()[0]
        })
    
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">')
    
    for entry in sitemap_entries:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>{entry["loc"]}</loc>')
        sitemap_xml.append(f'<lastmod>{entry["lastmod"]}</lastmod>')
        sitemap_xml.append(f'<changefreq>{entry["changefreq"]}</changefreq>')
        sitemap_xml.append(f'<priority>{entry["priority"]}</priority>')
        sitemap_xml.append('</url>')
    
    sitemap_xml.append('</urlset>')
    
    response = app.make_response('\n'.join(sitemap_xml))
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return response


@app.route('/robots.txt')
def robots():
    """Generate robots.txt for SEO"""
    robots_txt = """User-agent: *
Allow: /
Allow: /project/
Allow: /cv-preview
Allow: /sitemap.xml
Disallow: /dashboard/
Disallow: /static/
Disallow: /*.json$

Sitemap: """ + request.url_root.rstrip('/') + """/sitemap.xml
User-agent: GPTBot
Disallow: /

User-agent: CCBot
Disallow: /"""
    
    response = app.make_response(robots_txt)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response


@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_file('static/favicon.ico', mimetype='image/x-icon')


# Backup & Restore Routes
@app.route('/dashboard/backups')
@login_required
def view_backups():
    """View all available backups - redirect to settings"""
    return redirect(url_for('dashboard_settings') + '#backups')


@app.route('/backup/create', methods=['POST'])
@login_required
def create_manual_backup():
    """Create a manual backup"""
    try:
        backup_info = create_backup(manual=True)
        if backup_info:
            flash(f'✓ Backup created successfully: {backup_info["filename"]}', 'success')
            send_event_notification_async('backup_created', f'Manual backup: {backup_info["filename"]} ({backup_info["size_kb"]} KB)')
        else:
            flash('Error creating backup', 'error')
    except Exception as e:
        app.logger.error(f"Error creating manual backup: {str(e)}")
        flash('Error creating backup', 'error')
    return redirect(url_for('dashboard_settings') + '#backups')


@app.route('/backup/restore/<filename>', methods=['POST'])
@login_required
def restore_backup(filename):
    """Restore a backup"""
    # DEMO MODE: Block backup restoration in demo mode
    if session.get('is_demo'):
        flash('⚠️ Demo mode: Backup restoration is disabled.', 'warning')
        return redirect(url_for('dashboard_settings') + '#backups')
    
    try:
        filename = secure_filename(filename)
        backup_path = os.path.join('backups', filename)
        
        if not os.path.exists(backup_path):
            flash('Backup file not found', 'error')
            return redirect(url_for('dashboard_settings') + '#backups')
        
        if os.path.exists('data.json'):
            recovery_backup = f'backups/recovery_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            shutil.copy('data.json', recovery_backup)
        
        shutil.copy(backup_path, 'data.json')
        flash(f'✓ Portfolio restored from backup: {filename}', 'success')
        send_event_notification_async('backup_restored', f'Restored from: {filename}')
        return redirect(url_for('dashboard_settings') + '#backups')
    except Exception as e:
        app.logger.error(f"Error restoring backup: {str(e)}")
        flash('Error restoring backup', 'error')
        return redirect(url_for('dashboard_settings') + '#backups')


@app.route('/backup/download/<filename>')
@login_required
def download_backup(filename):
    """Download a backup file"""
    try:
        filename = secure_filename(filename)
        backup_path = os.path.join('backups', filename)
        
        if not os.path.exists(backup_path):
            flash('Backup file not found', 'error')
            return redirect(url_for('dashboard_settings') + '#backups')
        
        return send_file(backup_path, as_attachment=True, download_name=filename)
    except Exception as e:
        app.logger.error(f"Error downloading backup: {str(e)}")
        flash('Error downloading backup', 'error')
        return redirect(url_for('dashboard_settings') + '#backups')


@app.route('/backup/delete/<filename>', methods=['POST'])
@login_required
def delete_backup(filename):
    """Delete a backup file"""
    # DEMO MODE: Block backup deletion in demo mode
    if session.get('is_demo'):
        flash('⚠️ Demo mode: Backup deletion is disabled.', 'warning')
        return redirect(url_for('dashboard_settings') + '#backups')
    
    try:
        filename = secure_filename(filename)
        backup_path = os.path.join('backups', filename)
        
        if not os.path.exists(backup_path):
            flash('Backup file not found', 'error')
            return redirect(url_for('dashboard_settings') + '#backups')
        
        os.remove(backup_path)
        
        backups = get_backups_list()
        updated_backups = [b for b in backups if b['filename'] != filename]
        with open('backups/backups.json', 'w', encoding='utf-8') as f:
            json.dump(updated_backups, f, ensure_ascii=False, indent=2)
        
        flash(f'✓ Backup deleted: {filename}', 'success')
    except Exception as e:
        app.logger.error(f"Error deleting backup: {str(e)}")
        flash('Error deleting backup', 'error')
    
    return redirect(url_for('dashboard_settings') + '#backups')


@app.route('/api/backups')
@login_required
def api_backups():
    """API endpoint to get backups list"""
    try:
        backups = get_backups_list()
        return jsonify(backups)
    except Exception as e:
        app.logger.error(f"Error fetching backups: {str(e)}")
        return jsonify([]), 500


# Admin routes
@app.route('/dashboard/login', methods=['GET', 'POST'])
def dashboard_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        client_ip = get_client_ip()

        # Check admin credentials
        if (username == ADMIN_CREDENTIALS['username']
                and password and check_password_hash(
                    ADMIN_CREDENTIALS['password_hash'], password)):
            session['admin_logged_in'] = True
            session['username'] = username
            session['is_demo'] = False
            # Log successful login
            log_ip_activity('login_success', f"User: {username}")
            # Send login notification
            send_event_notification_async('login_attempt', f"{username} (IP: {client_ip})")
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        # Check demo user credentials (LIVE DEMO EDITION)
        elif (username == DEMO_USER_CREDENTIALS['username']
                and password and check_password_hash(
                    DEMO_USER_CREDENTIALS['password_hash'], password)):
            session['admin_logged_in'] = True
            session['username'] = username
            session['is_demo'] = True
            # Log demo login
            log_ip_activity('login_success', f"Demo User: {username}")
            flash('✓ Demo login successful - Some features are disabled', 'info')
            return redirect(url_for('dashboard'))
        else:
            # Log failed login attempt
            log_ip_activity('login_failed', f"Attempt with user: {username}")
            flash('Invalid username or password', 'error')

    return render_template('dashboard/login.html')


@app.route('/dashboard/logout')
def dashboard_logout():
    """Admin logout"""
    session.clear()
    flash('Logout successful', 'success')
    return redirect(url_for('dashboard_login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    data = load_data()
    stats = {
        'projects': len(data.get('projects', [])),
        'skills': len(data.get('skills', [])),
        'messages': len(data.get('messages', [])),
        'unread_messages': get_unread_messages_count(),
        'visitors': get_visitor_count(),
        'today_visitors': len(data.get('visitors', {}).get('today', []))
    }
    return render_template('dashboard/index.html', data=data, stats=stats)


@app.route('/documentation')
def documentation():
    """Serve documentation page"""
    import os
    doc_path = os.path.join('Documentation', 'English', 'documentation-english.html')
    if os.path.exists(doc_path):
        return send_file(doc_path)
    else:
        return render_template('404.html'), 404


@app.route('/dashboard/settings', methods=['GET', 'POST'])
@login_required
def dashboard_settings():
    """Dashboard settings page"""
    data = load_data()
    
    if request.method == 'POST':
        if 'settings' not in data:
            data['settings'] = {}
        
        selected_theme = request.form.get('theme', 'luxury-gold')
        valid_themes = ['luxury-gold', 'modern-dark', 'clean-light', 'terracotta-red', 'vibrant-green', 'silver-grey']
        if selected_theme in valid_themes:
            data['settings']['theme'] = selected_theme
            save_data(data)
            flash(f'Theme changed to {selected_theme.replace("-", " ").title()} successfully', 'success')
        else:
            flash('Invalid theme selected', 'error')
        
        return redirect(url_for('dashboard_settings'))
    
    themes = [
        {'id': 'luxury-gold', 'name': 'Luxury Gold', 'icon': 'fas fa-crown', 'description': 'Premium & Classic'},
        {'id': 'modern-dark', 'name': 'Modern Dark', 'icon': 'fas fa-zap', 'description': 'Tech & Trendy'},
        {'id': 'clean-light', 'name': 'Clean Light', 'icon': 'fas fa-sun', 'description': 'Minimal & Fresh'},
        {'id': 'terracotta-red', 'name': 'Terracotta Red', 'icon': 'fas fa-fire', 'description': 'Warm & Modern'},
        {'id': 'vibrant-green', 'name': 'Vibrant Green', 'icon': 'fas fa-leaf', 'description': 'Natural & Fresh'},
        {'id': 'silver-grey', 'name': 'Silver Grey', 'icon': 'fas fa-gem', 'description': 'Sophisticated & Modern'}
    ]
    
    current_theme = data.get('settings', {}).get('theme', 'luxury-gold')
    
    # Load Telegram credentials from file
    telegram_bot_token, telegram_chat_id = get_telegram_credentials()
    telegram_status = bool(telegram_bot_token and telegram_chat_id)
    
    # Mask bot token for display (show only first 10 chars)
    telegram_bot_token_display = telegram_bot_token[:10] + '...' if telegram_bot_token else ''
    
    # Load SMTP credentials
    smtp_config = load_smtp_config()
    smtp_host = smtp_config.get('host', '')
    smtp_port = smtp_config.get('port', '')
    smtp_email = smtp_config.get('email', '')
    smtp_status = bool(all([smtp_host, smtp_port, smtp_email, smtp_config.get('password')]))
    
    return render_template('dashboard/settings.html', themes=themes, current_theme=current_theme, data=data,
                         telegram_bot_token=telegram_bot_token_display,
                         telegram_chat_id=telegram_chat_id,
                         telegram_status=telegram_status,
                         smtp_host=smtp_host,
                         smtp_port=smtp_port,
                         smtp_email=smtp_email,
                         smtp_status=smtp_status)


@app.route('/dashboard/telegram', methods=['POST'])
@login_required
def dashboard_telegram():
    """Update Telegram settings"""
    # DEMO MODE: Block Telegram configuration changes
    if session.get('is_demo'):
        flash('⚠️ Demo mode: Telegram configuration changes are disabled.', 'warning')
        return redirect(url_for('dashboard_settings'))
    
    bot_token = request.form.get('bot_token', '').strip()
    chat_id = request.form.get('chat_id', '').strip()
    
    if not bot_token or not chat_id:
        flash('Please provide both Bot Token and Chat ID', 'error')
        return redirect(url_for('dashboard_settings'))
    
    try:
        # Test connection to Telegram API
        test_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(test_url, timeout=5)
        
        if response.status_code != 200:
            flash('Invalid Telegram Bot Token. Please check and try again.', 'error')
            return redirect(url_for('dashboard_settings'))
        
        # Send test message
        test_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        test_payload = {
            'chat_id': chat_id,
            'text': '✅ Telegram notifications configured successfully for Codexx Portfolio!',
            'parse_mode': 'HTML'
        }
        test_response = requests.post(test_message_url, json=test_payload, timeout=5)
        
        if test_response.status_code != 200:
            flash('Invalid Telegram Chat ID or permission denied. Please check and try again.', 'error')
            return redirect(url_for('dashboard_settings'))
        
        # Save to file since we can't modify env vars directly
        settings_file = 'telegram_config.json'
        telegram_config = {
            'bot_token': bot_token,
            'chat_id': chat_id,
            'configured_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(settings_file, 'w') as f:
            json.dump(telegram_config, f)
        
        flash('✅ Telegram notifications configured successfully! Check your Telegram for a test message.', 'success')
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Telegram configuration error: {str(e)}")
        flash('Connection error. Please check your internet connection and try again.', 'error')
    except Exception as e:
        app.logger.error(f"Telegram error: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('dashboard_settings'))


@app.route('/dashboard/smtp', methods=['POST'])
@login_required
def dashboard_smtp():
    """Update SMTP settings"""
    # DEMO MODE: Block SMTP configuration changes
    if session.get('is_demo'):
        flash('⚠️ Demo mode: SMTP configuration changes are disabled.', 'warning')
        return redirect(url_for('dashboard_settings'))
    
    smtp_host = request.form.get('smtp_host', '').strip()
    smtp_port = request.form.get('smtp_port', '').strip()
    smtp_email = request.form.get('smtp_email', '').strip()
    smtp_password = request.form.get('smtp_password', '').strip()
    
    if not all([smtp_host, smtp_port, smtp_email, smtp_password]):
        flash('Please provide all SMTP settings', 'error')
        return redirect(url_for('dashboard_settings'))
    
    try:
        smtp_config = {
            'host': smtp_host,
            'port': smtp_port,
            'email': smtp_email,
            'password': smtp_password,
            'configured_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if save_smtp_config(smtp_config):
            flash('✅ SMTP settings saved successfully!', 'success')
            send_event_notification_async('smtp_configured', f'Email configured: {smtp_email}')
        else:
            flash('Error saving SMTP settings', 'error')
    except Exception as e:
        app.logger.error(f"SMTP configuration error: {str(e)}")
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('dashboard_settings'))


@app.route('/dashboard/email-test', methods=['POST'])
@login_required
def email_test_connection():
    """Test SMTP connection"""
    # DEMO MODE: Simulate successful SMTP test without sending real emails
    if session.get('is_demo'):
        return jsonify({
            'success': True,
            'message': '✅ SMTP test simulated in demo mode - Configuration appears valid'
        })
    
    smtp_config = load_smtp_config()
    
    if not all([smtp_config.get('host'), smtp_config.get('email'), smtp_config.get('password')]):
        return jsonify({'success': False, 'error': 'SMTP not configured'})
    
    try:
        test_subject = '🧪 Codexx Portfolio - Email Test'
        test_body = """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #D4AF37;">✅ Email Connection Test Successful!</h2>
                <p>Your SMTP configuration is working perfectly.</p>
                <p><strong>Email Address:</strong> {}</p>
                <p><strong>Server:</strong> {}:{}</p>
                <p style="margin-top: 20px; color: #666; font-size: 12px;">
                    This is a test email from your Codexx Portfolio.
                </p>
            </body>
        </html>
        """.format(smtp_config.get('email'), smtp_config.get('host'), smtp_config.get('port'))
        
        if send_email(smtp_config.get('email'), test_subject, test_body, html=True):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to send email'})
    except Exception as e:
        app.logger.error(f"Email test error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/dashboard/telegram-test', methods=['POST'])
@login_required
def telegram_test_connection():
    """Test Telegram connection"""
    # DEMO MODE: Simulate successful Telegram test without sending real messages
    if session.get('is_demo'):
        return jsonify({
            'success': True,
            'message': '✅ Telegram test simulated in demo mode - Configuration appears valid'
        })
    
    bot_token, chat_id = get_telegram_credentials()
    
    if not bot_token or not chat_id:
        return jsonify({'success': False, 'error': 'Telegram not configured'})
    
    try:
        # Send test message
        test_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        test_payload = {
            'chat_id': chat_id,
            'text': '🧪 <b>Connection Test Successful!</b>\n✅ Your Portfolio Bot is working perfectly!',
            'parse_mode': 'HTML'
        }
        test_response = requests.post(test_url, json=test_payload, timeout=5)
        
        if test_response.status_code == 200:
            return jsonify({'success': True, 'message': 'Test message sent successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to send test message'})
    except Exception as e:
        app.logger.error(f"Test connection error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/dashboard/general', methods=['GET', 'POST'])
@login_required
def dashboard_general():
    """Edit general information"""
    data = load_data()

    if request.method == 'POST':
        data['name'] = request.form.get('name', '')
        data['title'] = request.form.get('title', '')
        data['description'] = request.form.get('description', '')

        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                data['photo'] = f"static/assets/uploads/{filename}"

        save_data(data)
        flash('General information saved successfully', 'success')
        return redirect(url_for('dashboard_general'))

    return render_template('dashboard/general.html', data=data)


@app.route('/dashboard/about', methods=['GET', 'POST'])
@login_required
def dashboard_about():
    """Edit about section"""
    data = load_data()

    if request.method == 'POST':
        data['about'] = request.form.get('about', '')
        save_data(data)
        flash('About section saved successfully', 'success')
        return redirect(url_for('dashboard_about'))

    return render_template('dashboard/about.html', data=data)


@app.route('/dashboard/skills', methods=['GET', 'POST'])
@login_required
def dashboard_skills():
    """Edit skills section"""
    data = load_data()

    if request.method == 'POST':
        skills = []
        skill_names = request.form.getlist('skill_name[]')
        skill_levels = request.form.getlist('skill_level[]')

        for name, level in zip(skill_names, skill_levels):
            if name.strip():
                skills.append({
                    'name':
                    name.strip(),
                    'level':
                    int(level)
                    if level.isdigit() and 0 <= int(level) <= 100 else 0
                })

        data['skills'] = skills
        save_data(data)
        flash('Skills saved successfully', 'success')
        return redirect(url_for('dashboard_skills'))

    return render_template('dashboard/skills.html', data=data)


@app.route('/dashboard/projects')
@login_required
def dashboard_projects():
    """List all projects"""
    data = load_data()
    return render_template('dashboard/projects.html', data=data)


@app.route('/dashboard/projects/add', methods=['GET', 'POST'])
@login_required
def dashboard_add_project():
    """Add new project"""
    if request.method == 'POST':
        data = load_data()

        project_ids = [p.get('id', 0) for p in data.get('projects', [])]
        new_id = max(project_ids) + 1 if project_ids else 1

        image_path = "static/assets/project-placeholder.svg"
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"project_{new_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f"static/assets/uploads/{filename}"

        technologies = [
            tech.strip() for tech in request.form.getlist('technologies[]')
            if tech.strip()
        ]
        short_desc = request.form.get('short_description', '').strip()
        full_content = request.form.get('content', '').strip()

        new_project = {
            'id': new_id,
            'title': request.form.get('title', '').strip(),
            'short_description': short_desc,
            'content': full_content,
            'description': short_desc,
            'image': image_path,
            'demo_url': request.form.get('demo_url', '').strip() or '#',
            'github_url': request.form.get('github_url', '').strip() or '#',
            'technologies': technologies
        }

        if 'projects' not in data:
            data['projects'] = []
        data['projects'].append(new_project)

        save_data(data)
        flash('Project added successfully', 'success')
        return redirect(url_for('dashboard_projects'))

    return render_template('dashboard/add_project.html')


@app.route('/dashboard/projects/edit/<int:project_id>',
           methods=['GET', 'POST'])
@login_required
def dashboard_edit_project(project_id):
    """Edit existing project"""
    data = load_data()
    project = next(
        (p for p in data.get('projects', []) if p.get('id') == project_id),
        None)

    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('dashboard_projects'))

    if request.method == 'POST':
        short_desc = request.form.get('short_description', '').strip()
        full_content = request.form.get('content', '').strip()

        project['title'] = request.form.get('title', '').strip()
        project['short_description'] = short_desc
        project['content'] = full_content
        project['description'] = short_desc
        project['demo_url'] = request.form.get('demo_url', '').strip() or '#'
        project['github_url'] = request.form.get('github_url',
                                                 '').strip() or '#'

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"project_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                project['image'] = f"static/assets/uploads/{filename}"

        project['technologies'] = [
            tech.strip() for tech in request.form.getlist('technologies[]')
            if tech.strip()
        ]

        save_data(data)
        flash('Project updated successfully', 'success')
        return redirect(url_for('dashboard_projects'))

    return render_template('dashboard/edit_project.html', project=project)


@app.route('/dashboard/projects/delete/<int:project_id>')
@login_required
def dashboard_delete_project(project_id):
    """Delete project"""
    data = load_data()
    data['projects'] = [
        p for p in data.get('projects', []) if p.get('id') != project_id
    ]
    save_data(data)
    flash('Project deleted successfully', 'success')
    return redirect(url_for('dashboard_projects'))


@app.route('/dashboard/contact', methods=['GET', 'POST'])
@login_required
def dashboard_contact():
    """Edit contact information"""
    data = load_data()

    if request.method == 'POST':
        if 'contact' not in data:
            data['contact'] = {}

        data['contact']['email'] = request.form.get('email', '')
        data['contact']['phone'] = request.form.get('phone', '')
        data['contact']['location'] = request.form.get('location', '')

        save_data(data)
        flash('Contact information saved successfully', 'success')
        return redirect(url_for('dashboard_contact'))

    return render_template('dashboard/contact.html', data=data)


@app.route('/dashboard/social', methods=['GET', 'POST'])
@login_required
def dashboard_social():
    """Edit social media links"""
    data = load_data()

    if request.method == 'POST':
        if 'social' not in data:
            data['social'] = {}

        data['social']['linkedin'] = request.form.get('linkedin', '')
        data['social']['github'] = request.form.get('github', '')
        data['social']['twitter'] = request.form.get('twitter', '')
        data['social']['instagram'] = request.form.get('instagram', '')
        data['social']['facebook'] = request.form.get('facebook', '')
        data['social']['youtube'] = request.form.get('youtube', '')
        data['social']['behance'] = request.form.get('behance', '')
        data['social']['dribbble'] = request.form.get('dribbble', '')

        save_data(data)
        flash('Social media links saved successfully', 'success')
        return redirect(url_for('dashboard_social'))

    return render_template('dashboard/social.html', data=data)




@app.route('/dashboard/messages')
@login_required
def dashboard_messages():
    """List all messages"""
    data = load_data()
    messages = sorted(data.get('messages', []),
                      key=lambda x: x.get('date', ''),
                      reverse=True)
    return render_template('dashboard/messages.html', messages=messages)


@app.route('/dashboard/messages/view/<int:message_id>')
@login_required
def dashboard_view_message(message_id):
    """View specific message"""
    data = load_data()
    message = next(
        (m for m in data.get('messages', []) if m.get('id') == message_id),
        None)

    if not message:
        flash('Message not found', 'error')
        return redirect(url_for('dashboard_messages'))

    if not message.get('read', False):
        mark_message_as_read(message_id)

    return render_template('dashboard/view_message.html', message=message)


@app.route('/dashboard/messages/delete/<int:message_id>')
@login_required
def dashboard_delete_message(message_id):
    """Delete message"""
    data = load_data()
    data['messages'] = [
        m for m in data.get('messages', []) if m.get('id') != message_id
    ]
    save_data(data)
    flash('Message deleted successfully', 'success')
    return redirect(url_for('dashboard_messages'))


@app.route('/dashboard/messages/convert/<int:message_id>')
@login_required
def dashboard_convert_message_to_client(message_id):
    """Convert message to client"""
    data = load_data()
    message = next(
        (m for m in data.get('messages', []) if m.get('id') == message_id),
        None)

    if not message:
        flash('Message not found', 'error')
        return redirect(url_for('dashboard_messages'))

    if 'clients' not in data:
        data['clients'] = []

    client_ids = [c.get('id', 0) for c in data.get('clients', [])]
    new_id = max(client_ids) + 1 if client_ids else 1

    new_client = {
        'id': new_id,
        'name': message.get('name', ''),
        'email': message.get('email', ''),
        'phone': '',
        'company': '',
        'project_title': '',
        'project_description': message.get('message', ''),
        'status': 'lead',
        'price': '',
        'deadline': '',
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'notes': '',
        'payment_status': 'pending',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    data['clients'].append(new_client)
    save_data(data)

    flash('Message converted to client successfully', 'success')
    return redirect(url_for('dashboard_edit_client', client_id=new_id))


@app.route('/dashboard/clients')
@login_required
def dashboard_clients():
    """List all clients"""
    data = load_data()
    if 'clients' not in data:
        data['clients'] = []
        save_data(data)

    clients = sorted(data.get('clients', []),
                     key=lambda x: x.get('created_at', ''),
                     reverse=True)
    stats = get_clients_stats()
    return render_template('dashboard/clients.html',
                           clients=clients,
                           stats=stats)


@app.route('/dashboard/clients/add', methods=['GET', 'POST'])
@login_required
def dashboard_add_client():
    """Add new client"""
    if request.method == 'POST':
        data = load_data()

        if 'clients' not in data:
            data['clients'] = []

        client_ids = [c.get('id', 0) for c in data.get('clients', [])]
        new_id = max(client_ids) + 1 if client_ids else 1

        new_client = {
            'id':
            new_id,
            'name':
            request.form.get('name', '').strip(),
            'email':
            request.form.get('email', '').strip(),
            'phone':
            request.form.get('phone', '').strip(),
            'company':
            request.form.get('company', '').strip(),
            'project_title':
            request.form.get('project_title', '').strip(),
            'project_description':
            request.form.get('project_description', '').strip(),
            'status':
            request.form.get('status', 'lead'),
            'price':
            request.form.get('price', '').strip(),
            'deadline':
            request.form.get('deadline', '').strip(),
            'start_date':
            request.form.get('start_date', '').strip()
            or datetime.now().strftime('%Y-%m-%d'),
            'notes':
            request.form.get('notes', '').strip(),
            'payment_status':
            request.form.get('payment_status', 'pending'),
            'created_at':
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status_updated_at':
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        data['clients'].append(new_client)
        save_data(data)
        
        # Send Telegram notification for new lead
        send_telegram_notification(
            f"📊 <b>New Lead Added</b>\n\n"
            f"👤 {new_client['name']}\n"
            f"📧 {new_client['email']}\n"
            f"📋 {new_client['project_title']}\n"
            f"💰 ${new_client['price'] if new_client['price'] else 'TBD'}"
        )
        
        flash('Client added successfully', 'success')
        return redirect(url_for('dashboard_clients'))

    return render_template('dashboard/add_client.html')


@app.route('/dashboard/clients/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
def dashboard_edit_client(client_id):
    """Edit existing client"""
    data = load_data()
    client = next(
        (c for c in data.get('clients', []) if c.get('id') == client_id), None)

    if not client:
        flash('Client not found', 'error')
        return redirect(url_for('dashboard_clients'))

    if request.method == 'POST':
        old_status = client.get('status', 'lead')
        new_status = request.form.get('status', 'lead')
        
        client['name'] = request.form.get('name', '').strip()
        client['email'] = request.form.get('email', '').strip()
        client['phone'] = request.form.get('phone', '').strip()
        client['company'] = request.form.get('company', '').strip()
        client['project_title'] = request.form.get('project_title', '').strip()
        client['project_description'] = request.form.get(
            'project_description', '').strip()
        client['status'] = new_status
        client['price'] = request.form.get('price', '').strip()
        client['deadline'] = request.form.get('deadline', '').strip()
        client['start_date'] = request.form.get('start_date', '').strip()
        client['notes'] = request.form.get('notes', '').strip()
        client['payment_status'] = request.form.get('payment_status', client.get('payment_status', 'pending'))
        
        if old_status != new_status:
            client['status_updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Send Telegram notification for status change
            status_emoji = {
                'lead': '🎯',
                'negotiation': '💬',
                'in-progress': '⚙️',
                'delivered': '✅'
            }
            send_telegram_notification(
                f"{status_emoji.get(new_status, '📊')} <b>Client Status Updated</b>\n\n"
                f"👤 {client['name']}\n"
                f"📋 {client['project_title']}\n"
                f"📍 {old_status.title()} → {new_status.replace('-', ' ').title()}\n"
                f"💰 ${client['price'] if client['price'] else 'TBD'}\n"
                f"📝 {client['notes'][:100] if client['notes'] else 'N/A'}"
            )

        save_data(data)
        flash('Client updated successfully', 'success')
        return redirect(url_for('dashboard_clients'))

    return render_template('dashboard/edit_client.html', client=client)


@app.route('/dashboard/clients/view/<int:client_id>')
@login_required
def dashboard_view_client(client_id):
    """View client details"""
    data = load_data()
    client = next(
        (c for c in data.get('clients', []) if c.get('id') == client_id), None)

    if not client:
        flash('Client not found', 'error')
        return redirect(url_for('dashboard_clients'))

    return render_template('dashboard/view_client.html', client=client)


@app.route('/dashboard/clients/delete/<int:client_id>')
@login_required
def dashboard_delete_client(client_id):
    """Delete client"""
    data = load_data()
    data['clients'] = [
        c for c in data.get('clients', []) if c.get('id') != client_id
    ]
    save_data(data)
    flash('Client deleted successfully', 'success')
    return redirect(url_for('dashboard_clients'))


@app.route('/dashboard/change-password', methods=['GET', 'POST'])
@login_required
def dashboard_change_password():
    """Change admin password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_password or not check_password_hash(
                ADMIN_CREDENTIALS['password_hash'], current_password):
            flash('Current password is incorrect', 'error')
        elif new_password != confirm_password:
            flash('New password and confirmation do not match', 'error')
        elif not new_password or len(new_password) < 8:
            flash('New password must be at least 8 characters long', 'error')
        else:
            ADMIN_CREDENTIALS['password_hash'] = generate_password_hash(
                new_password)
            flash('Password changed successfully. Please login again.',
                  'success')
            session.clear()
            return redirect(url_for('dashboard_login'))

    return render_template('dashboard/change_password.html')


@app.route('/cv-preview')
def cv_preview():
    """CV preview page"""
    data = load_data()
    return render_template('cv_preview.html', data=data)


@app.route('/download-cv')
def download_cv():
    """Download CV as PDF"""
    try:
        import weasyprint

        data = load_data()
        html_content = render_template('cv_preview.html',
                                       data=data,
                                       pdf_mode=True)

        pdf_buffer = io.BytesIO()
        html = weasyprint.HTML(string=html_content, base_url=request.url_root)
        html.write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        filename = data.get("name", "CV").replace(' ', '_')
        return send_file(pdf_buffer,
                         mimetype='application/pdf',
                         as_attachment=True,
                         download_name=f'{filename}_CV.pdf')

    except ImportError:
        flash(
            'PDF generation library not available. Please install weasyprint.',
            'error')
        return redirect(url_for('cv_preview'))
    except Exception as e:
        app.logger.error(f"PDF Generation Error: {str(e)}")
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('cv_preview'))


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
