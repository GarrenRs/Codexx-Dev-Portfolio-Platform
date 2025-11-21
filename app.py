
import os
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from datetime import datetime
from functools import wraps
import io

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "CHANGE-THIS-SECRET-KEY-IN-PRODUCTION")

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

# Admin credentials (should be environment variables in production)
ADMIN_CREDENTIALS = {
    'username': os.environ.get('ADMIN_USERNAME', 'admin'),
    'password_hash': generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
            'contact': {'email': '', 'phone': '', 'location': ''},
            'social': {},
            'messages': [],
            'visitors': {'total': 0, 'today': [], 'unique_ips': []}
        }
        save_data(default_data)
        return default_data
    except json.JSONDecodeError:
        flash('Error reading data file. Please check data.json format.', 'error')
        return {}

def save_data(data):
    """Save portfolio data to JSON file with backup"""
    try:
        # Create backup before saving
        if os.path.exists('data.json'):
            backup_path = f'data_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open('data.json', 'r', encoding='utf-8') as original:
                with open(backup_path, 'w', encoding='utf-8') as backup:
                    backup.write(original.read())
            
            # Keep only last 5 backups
            backups = sorted([f for f in os.listdir('.') if f.startswith('data_backup_')])
            for old_backup in backups[:-5]:
                try:
                    os.remove(old_backup)
                except:
                    pass
        
        with open('data.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.error(f"Error saving data: {str(e)}")
        flash('Error saving data. Please try again.', 'error')

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('dashboard_login'))
        return f(*args, **kwargs)
    return decorated_function

def save_message(name, email, message):
    """Save contact message"""
    data = load_data()
    if 'messages' not in data:
        data['messages'] = []
    
    message_ids = [m.get('id', 0) for m in data.get('messages', [])]
    new_id = max(message_ids) + 1 if message_ids else 1
    
    new_message = {
        'id': new_id,
        'name': name,
        'email': email,
        'message': message,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'read': False
    }
    
    data['messages'].append(new_message)
    save_data(data)
    return new_id

def get_unread_messages_count():
    """Get count of unread messages"""
    data = load_data()
    return len([m for m in data.get('messages', []) if not m.get('read', False)])

def track_visitor():
    """Track visitor with improved logic"""
    data = load_data()
    if 'visitors' not in data:
        data['visitors'] = {'total': 0, 'today': [], 'unique_ips': []}
    
    visitor_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    today = datetime.now().strftime('%Y-%m-%d')
    
    data['visitors']['total'] = data['visitors'].get('total', 0) + 1
    data['visitors']['today'] = [v for v in data['visitors'].get('today', []) if v.get('date') == today]
    data['visitors']['today'].append({
        'ip': visitor_ip,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date': today
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
    completed_clients = len([c for c in clients if c.get('status') == 'completed'])
    pending_clients = len([c for c in clients if c.get('status') == 'pending'])
    
    total_revenue = sum(float(c.get('price', 0)) for c in clients if c.get('price'))
    
    return {
        'total': total_clients,
        'active': active_clients,
        'completed': completed_clients,
        'pending': pending_clients,
        'revenue': total_revenue
    }

@app.context_processor
def inject_global_vars():
    """Make functions available in all templates"""
    return {
        'get_unread_messages_count': get_unread_messages_count,
        'get_visitor_count': get_visitor_count,
        'get_clients_stats': get_clients_stats,
        'current_year': datetime.now().year
    }

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Custom 500 error page"""
    app.logger.error(f"Server Error: {str(e)}")
    return render_template('500.html') if os.path.exists('templates/500.html') else ('Internal Server Error', 500)

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

@app.route('/contact', methods=['POST'])
def contact():
    """Handle contact form submission"""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()
    
    if name and email and message:
        try:
            save_message(name, email, message)
            flash('Thank you for your message! I will get back to you soon.', 'success')
        except Exception as e:
            app.logger.error(f"Contact form error: {str(e)}")
            flash('Sorry, there was an error sending your message. Please try again.', 'error')
    else:
        flash('Please fill in all required fields.', 'error')
    
    return redirect(url_for('index') + '#contact')

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Project detail page"""
    data = load_data()
    project = next((p for p in data.get('projects', []) if p.get('id') == project_id), None)
    
    if not project:
        return render_template('404.html'), 404
    
    return render_template('project_detail.html', project=project, data=data)

@app.route('/sitemap.xml')
def sitemap():
    """Generate sitemap for SEO"""
    data = load_data()
    pages = ['index']
    projects = [f"project/{p['id']}" for p in data.get('projects', [])]
    
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    base_url = request.url_root.rstrip('/')
    for page in pages + projects:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>{base_url}/{page}</loc>')
        sitemap_xml.append('<changefreq>weekly</changefreq>')
        sitemap_xml.append('<priority>0.8</priority>')
        sitemap_xml.append('</url>')
    
    sitemap_xml.append('</urlset>')
    
    response = app.make_response('\n'.join(sitemap_xml))
    response.headers['Content-Type'] = 'application/xml'
    return response

# Admin routes
@app.route('/dashboard/login', methods=['GET', 'POST'])
def dashboard_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if (username == ADMIN_CREDENTIALS['username'] and 
            password and 
            check_password_hash(ADMIN_CREDENTIALS['password_hash'], password)):
            session['admin_logged_in'] = True
            session['username'] = username
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        else:
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
    return send_file('documentation.html')

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
                    'name': name.strip(),
                    'level': int(level) if level.isdigit() and 0 <= int(level) <= 100 else 0
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
        
        technologies = [tech.strip() for tech in request.form.getlist('technologies[]') if tech.strip()]
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

@app.route('/dashboard/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def dashboard_edit_project(project_id):
    """Edit existing project"""
    data = load_data()
    project = next((p for p in data.get('projects', []) if p.get('id') == project_id), None)
    
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
        project['github_url'] = request.form.get('github_url', '').strip() or '#'
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"project_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                project['image'] = f"static/assets/uploads/{filename}"
        
        project['technologies'] = [tech.strip() for tech in request.form.getlist('technologies[]') if tech.strip()]
        
        save_data(data)
        flash('Project updated successfully', 'success')
        return redirect(url_for('dashboard_projects'))
    
    return render_template('dashboard/edit_project.html', project=project)

@app.route('/dashboard/projects/delete/<int:project_id>')
@login_required
def dashboard_delete_project(project_id):
    """Delete project"""
    data = load_data()
    data['projects'] = [p for p in data.get('projects', []) if p.get('id') != project_id]
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
    messages = sorted(data.get('messages', []), key=lambda x: x.get('date', ''), reverse=True)
    return render_template('dashboard/messages.html', messages=messages)

@app.route('/dashboard/messages/view/<int:message_id>')
@login_required
def dashboard_view_message(message_id):
    """View specific message"""
    data = load_data()
    message = next((m for m in data.get('messages', []) if m.get('id') == message_id), None)
    
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
    data['messages'] = [m for m in data.get('messages', []) if m.get('id') != message_id]
    save_data(data)
    flash('Message deleted successfully', 'success')
    return redirect(url_for('dashboard_messages'))

@app.route('/dashboard/messages/convert/<int:message_id>')
@login_required
def dashboard_convert_message_to_client(message_id):
    """Convert message to client"""
    data = load_data()
    message = next((m for m in data.get('messages', []) if m.get('id') == message_id), None)
    
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
        'status': 'pending',
        'price': '',
        'deadline': '',
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'notes': '',
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
    
    clients = sorted(data.get('clients', []), key=lambda x: x.get('created_at', ''), reverse=True)
    stats = get_clients_stats()
    return render_template('dashboard/clients.html', clients=clients, stats=stats)

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
            'id': new_id,
            'name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'company': request.form.get('company', '').strip(),
            'project_title': request.form.get('project_title', '').strip(),
            'project_description': request.form.get('project_description', '').strip(),
            'status': request.form.get('status', 'pending'),
            'price': request.form.get('price', '').strip(),
            'deadline': request.form.get('deadline', '').strip(),
            'start_date': request.form.get('start_date', '').strip() or datetime.now().strftime('%Y-%m-%d'),
            'notes': request.form.get('notes', '').strip(),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        data['clients'].append(new_client)
        save_data(data)
        flash('Client added successfully', 'success')
        return redirect(url_for('dashboard_clients'))
    
    return render_template('dashboard/add_client.html')

@app.route('/dashboard/clients/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
def dashboard_edit_client(client_id):
    """Edit existing client"""
    data = load_data()
    client = next((c for c in data.get('clients', []) if c.get('id') == client_id), None)
    
    if not client:
        flash('Client not found', 'error')
        return redirect(url_for('dashboard_clients'))
    
    if request.method == 'POST':
        client['name'] = request.form.get('name', '').strip()
        client['email'] = request.form.get('email', '').strip()
        client['phone'] = request.form.get('phone', '').strip()
        client['company'] = request.form.get('company', '').strip()
        client['project_title'] = request.form.get('project_title', '').strip()
        client['project_description'] = request.form.get('project_description', '').strip()
        client['status'] = request.form.get('status', 'pending')
        client['price'] = request.form.get('price', '').strip()
        client['deadline'] = request.form.get('deadline', '').strip()
        client['start_date'] = request.form.get('start_date', '').strip()
        client['notes'] = request.form.get('notes', '').strip()
        
        save_data(data)
        flash('Client updated successfully', 'success')
        return redirect(url_for('dashboard_clients'))
    
    return render_template('dashboard/edit_client.html', client=client)

@app.route('/dashboard/clients/view/<int:client_id>')
@login_required
def dashboard_view_client(client_id):
    """View client details"""
    data = load_data()
    client = next((c for c in data.get('clients', []) if c.get('id') == client_id), None)
    
    if not client:
        flash('Client not found', 'error')
        return redirect(url_for('dashboard_clients'))
    
    return render_template('dashboard/view_client.html', client=client)

@app.route('/dashboard/clients/delete/<int:client_id>')
@login_required
def dashboard_delete_client(client_id):
    """Delete client"""
    data = load_data()
    data['clients'] = [c for c in data.get('clients', []) if c.get('id') != client_id]
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
        
        if not current_password or not check_password_hash(ADMIN_CREDENTIALS['password_hash'], current_password):
            flash('Current password is incorrect', 'error')
        elif new_password != confirm_password:
            flash('New password and confirmation do not match', 'error')
        elif not new_password or len(new_password) < 8:
            flash('New password must be at least 8 characters long', 'error')
        else:
            ADMIN_CREDENTIALS['password_hash'] = generate_password_hash(new_password)
            flash('Password changed successfully. Please login again.', 'success')
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
        html_content = render_template('cv_preview.html', data=data, pdf_mode=True)
        
        pdf_buffer = io.BytesIO()
        html = weasyprint.HTML(string=html_content, base_url=request.url_root)
        html.write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        filename = data.get("name", "CV").replace(' ', '_')
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{filename}_CV.pdf'
        )
        
    except ImportError:
        flash('PDF generation library not available. Please install weasyprint.', 'error')
        return redirect(url_for('cv_preview'))
    except Exception as e:
        app.logger.error(f"PDF Generation Error: {str(e)}")
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('cv_preview'))

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
