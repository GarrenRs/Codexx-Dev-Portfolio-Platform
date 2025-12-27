# Codexx Dev Portfolio Platform

## Overview
A professional portfolio website with an integrated admin dashboard for managing content. Built with Flask (Python), featuring modern design, comprehensive content management capabilities, and ready for production deployment.

**Created**: November 6, 2025  
**Last Updated**: December 27, 2025 (Phase 0 Complete ✅)  
**Status**: Production-ready, Phase 0 stabilization complete, ready for Phase 1

## Project Structure
```
portfolio-platform/
├── app.py                      # Main Flask application
├── data.json                   # Portfolio data storage (initialized empty)
├── requirements.txt            # Python dependencies for production
├── pyproject.toml             # Python dependencies for Replit
├── build.sh                   # Build script
├── Procfile                   # Process file for deployment
├── .gitignore                 # Git ignore rules
├── static/                    # Static assets
│   ├── css/style.css         # Main stylesheet
│   ├── js/script.js          # Frontend JavaScript
│   ├── themes/               # Multiple theme CSS files
│   └── assets/
│       ├── uploads/          # User-uploaded images (empty)
│       ├── profile-placeholder.svg
│       └── project-placeholder.svg
├── templates/                # HTML templates
│   ├── index.html            # Main portfolio page
│   ├── dashboard/            # Admin dashboard templates
│   ├── error pages (404, 500, etc)
│   ├── cv_preview.html       # CV templates
│   └── project_detail.html
└── README.md                 # Complete documentation
```

## Features
- **Portfolio Display**: Hero section, about, skills, projects showcase, contact form
- **Admin Dashboard**: Secure login (admin/admin123), content management, file uploads, analytics
- **Client Management**: Full CRUD operations for client tracking with status and pricing
- **CV Generation**: Professional CV preview and PDF download
- **Visitor Tracking**: Real-time analytics and visitor counter
- **Message Management**: Contact form submissions with read/unread status
- **Theme Support**: Multiple professional themes (luxury-gold, modern-dark, etc.)
- **Security**: Password hashing, session management, file upload validation, rate limiting

## Technology Stack
- **Backend**: Flask 3.1.1 (Python 3.11)
- **Templating**: Jinja2
- **Styling**: Bootstrap 5, Custom CSS with multiple themes
- **PDF Generation**: WeasyPrint 65.1
- **Authentication**: Flask sessions with Werkzeug password hashing
- **Data Storage**: JSON file-based storage (data.json)
- **Scheduler**: APScheduler for automated tasks (backups, demo reset)
- **Production Server**: Gunicorn with 4 workers
- **Email**: SMTP integration for notifications
- **Notifications**: Telegram bot integration (optional)

## Installation & Setup

### 1. Install Dependencies
All dependencies are already installed:
```bash
pip install -r requirements.txt
```

### 2. Workflow Setup (Replit)
- **Name**: flask-app
- **Command**: `python app.py`
- **Port**: 5000 (webview)
- **Status**: Running and configured

### 3. Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`
- **⚠️ IMPORTANT**: Change the password immediately after first login via Dashboard > Settings > Change Password

## Environment Variables
The application supports these environment variables:
- `SESSION_SECRET`: Flask session secret key (auto-generated on deployment)
- `ADMIN_USERNAME`: Admin username (default: admin)
- `ADMIN_PASSWORD`: Admin password (default: admin123)
- `FLASK_ENV`: Set to 'production' for production mode (optional)
- `TELEGRAM_BOT_TOKEN`: Telegram bot token (optional)
- `TELEGRAM_CHAT_ID`: Telegram chat ID (optional)

## Key Routes
- `/` - Main portfolio page
- `/dashboard` - Admin dashboard (requires login)
- `/dashboard/general` - Edit profile information
- `/dashboard/about` - Edit about section
- `/dashboard/skills` - Manage skills
- `/dashboard/projects` - Manage projects
- `/dashboard/contact` - Edit contact information
- `/dashboard/social` - Edit social media links
- `/dashboard/clients` - Manage clients
- `/dashboard/messages` - View contact messages
- `/dashboard/settings` - Theme and preferences
- `/dashboard/change-password` - Change admin password
- `/cv-preview` - Preview CV
- `/download-cv` - Download CV as PDF
- `/catalog` - Public project catalog

## Data Management
- **Storage**: `data.json` file in root directory
- **Default Data**: Empty (clean slate for production)
- **Backups**: Automatic backups created hourly (keeps last 20)
- **Upload Directory**: `static/assets/uploads/`
- **Allowed File Types**: PNG, JPG, JPEG, GIF, WebP (max 16MB)

## Security Features
- ✅ Password hashing with Werkzeug
- ✅ Session-based authentication with secure cookies
- ✅ File upload validation and sanitization
- ✅ Rate limiting on contact form (10 requests per 60 seconds)
- ✅ IP logging for security tracking
- ✅ XSS protection through Jinja2 auto-escaping
- ✅ CSRF protection via Flask sessions
- ✅ Secure filename handling with werkzeug.utils

## Development & Deployment

### Running Locally (Replit Development)
```bash
# Already configured via workflow
python app.py
# Runs on http://0.0.0.0:5000
```

### Production Deployment
The project includes configuration files for easy deployment:
- `requirements.txt` - Production dependencies
- `Procfile` - Gunicorn configuration
- `render.yaml` - Render.com deployment config

**Deployment Steps**:
1. Push code to GitHub
2. Connect repository to Render
3. Set environment variables if needed
4. Deploy automatically

## Recent Changes (December 27, 2025)

### Fresh Initialization
- ✅ Cleared all default portfolio data
- ✅ Reset data.json to empty/clean state
- ✅ Added .gitignore for Python project
- ✅ Removed old backup files (17 backups cleaned)
- ✅ Configured admin credentials: `admin` / `admin123`
- ✅ Verified all features and tools are functional
- ✅ Updated deployment configuration to autoscale with Gunicorn
- ✅ Project ready for real production use

### Previous Updates
- **Nov 21, 2025**: Production Deployment Preparation
  - Created `requirements.txt` and `build.sh`
  - Updated deployment configuration
  - Cleaned and optimized project structure

- **Nov 7, 2025**: Client Management System
  - Added comprehensive client management with CRUD operations
  - Implemented client statistics dashboard
  - Added project price and deadline tracking

- **Nov 6, 2025**: GitHub Import Setup
  - Installed all Python dependencies
  - Configured Flask development server
  - Verified all features operational

## Troubleshooting

### Login Issues
- Default credentials: `admin` / `admin123`
- Clear browser cache and cookies if login fails
- Check that SESSION_SECRET environment variable is set (if deployed)

### File Upload Issues
- Verify `static/assets/uploads/` directory exists and is writable
- Check file type is in allowed list (png, jpg, jpeg, gif, webp)
- Maximum file size is 16MB

### PDF Generation
- Ensure WeasyPrint is installed: `pip install weasyprint==65.1`
- If PDF fails, check that all required system fonts are available

### Port Conflicts
- Application is configured for port 5000 only
- Flask development server uses 0.0.0.0:5000
- Gunicorn production server also uses 0.0.0.0:5000

## Production Checklist
✅ Dependencies installed and verified  
✅ Admin credentials set (admin/admin123)  
✅ Data cleared and initialized  
✅ .gitignore configured  
✅ Workflow running on port 5000  
✅ Deployment configuration (autoscale with Gunicorn)  
✅ All features tested and working  
✅ Ready for deployment  

## User Preferences
- Clean, professional setup
- All necessary tools fully functional
- Production-ready configuration
- Security best practices implemented

**Status**: ✅ Ready for production use! 🚀

---

## Next Steps for Users
1. Login with `admin` / `admin123`
2. Change password immediately via Dashboard > Settings > Change Password
3. Update profile information via Dashboard > General
4. Add your projects, skills, and contact information
5. Deploy to production when ready
