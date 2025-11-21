# Codexx Dev Portfolio Platform

## Overview
A professional portfolio website with an integrated admin dashboard for managing content. Built with Flask (Python), featuring modern design, comprehensive content management capabilities, and ready for deployment on Render.

**Created**: November 6, 2025  
**Last Updated**: November 21, 2025  
**Status**: Production-ready, optimized for Render deployment

## Project Structure
```
portfolio-platform/
├── app.py                      # Main Flask application
├── data.json                   # Portfolio data storage (default: Codexx Dev)
├── requirements.txt            # Python dependencies for production
├── pyproject.toml             # Python dependencies for Replit
├── build.sh                   # Render build script
├── render.yaml                # Render deployment configuration
├── Procfile                   # Process file for deployment
├── .gitignore                 # Git ignore rules
├── static/                    # Static assets
│   ├── css/style.css         # Main stylesheet
│   ├── js/script.js          # Frontend JavaScript
│   └── assets/
│       ├── uploads/           # User-uploaded images
│       ├── profile-placeholder.svg
│       └── project-placeholder.svg
├── templates/                 # HTML templates
│   ├── index.html            # Main portfolio page
│   ├── dashboard/            # Admin dashboard templates
│   ├── 404.html              # Error pages
│   ├── 500.html
│   ├── cv_preview.html       # CV templates
│   └── project_detail.html
└── README.md                  # Complete documentation
```

## Features
- **Portfolio Display**: Hero section, about, skills, projects showcase, contact form
- **Admin Dashboard**: Secure login, content management, file uploads, analytics
- **Client Management**: Full CRUD operations for client tracking with project status, pricing, and conversion from messages
- **CV Generation**: Professional CV preview and PDF download
- **Visitor Tracking**: Real-time analytics and visitor counter
- **Message Management**: Contact form submissions with read/unread status, convert to client
- **Security**: Password hashing, session management, file upload validation

## Technology Stack
- **Backend**: Flask 3.1.1 (Python 3.11)
- **Templating**: Jinja2
- **Styling**: Bootstrap 5, Custom CSS
- **PDF Generation**: WeasyPrint
- **Authentication**: Flask sessions with Werkzeug password hashing
- **Data Storage**: JSON file-based storage
- **Production Server**: Gunicorn with 4 workers

## Setup & Configuration

### Workflow (Replit)
- **Name**: flask-app
- **Command**: `python app.py`
- **Port**: 5000 (webview)
- **Type**: Web application with frontend

### Dependencies
All dependencies are available in both formats:
- **Production** (`requirements.txt`): For Render deployment
- **Replit** (`pyproject.toml`): Managed via `uv`

Main dependencies:
- Flask 3.1.1
- Werkzeug 3.1.3
- Gunicorn 23.0.0
- WeasyPrint 65.1
- email-validator, flask-login, flask-sqlalchemy, psycopg2-binary, flask-dance, oauthlib, pyjwt

### Environment Variables
- `SESSION_SECRET`: Flask session secret key (auto-generated on Render)
- `ADMIN_USERNAME`: Admin username (default: admin)
- `ADMIN_PASSWORD`: Admin password (auto-generated on Render)
- `FLASK_ENV`: Set to 'production' for production mode
- `PYTHON_VERSION`: 3.11.0 (Render)

### Admin Access
- **Login URL**: `/dashboard/login`
- **Default Username**: admin
- **Default Password**: admin123 (Replit) / auto-generated (Render)
- **Important**: Change the default password immediately after first login!

## Key Routes
- `/` - Main portfolio page
- `/dashboard` - Admin dashboard (requires login)
- `/dashboard/general` - Edit profile information
- `/dashboard/about` - Edit about section
- `/dashboard/skills` - Manage skills
- `/dashboard/projects` - Manage projects
- `/dashboard/contact` - Edit contact information
- `/dashboard/social` - Edit social media links
- `/dashboard/clients` - Manage clients and projects
- `/dashboard/messages` - View contact messages
- `/dashboard/change-password` - Change admin password
- `/cv-preview` - Preview CV
- `/download-cv` - Download CV as PDF
- `/sitemap.xml` - SEO sitemap

## Data Management
- **Storage**: `data.json` file in root directory
- **Default Data**: Codexx Dev profile with sample projects
- **Backups**: Automatic backups created on each save (keeps last 5)
- **Upload Directory**: `static/assets/uploads/`
- **Allowed File Types**: png, jpg, jpeg, gif, webp (max 16MB)

## Security Features
- Password hashing with Werkzeug
- Session-based authentication with secure cookies
- File upload validation and sanitization
- Secure filename handling
- XSS protection through Jinja2 auto-escaping
- CSRF protection via Flask sessions
- Environment-based secret management

## Recent Changes

### Nov 21, 2025: Production Deployment Preparation
- **Data Reset**: Cleaned all data and created fresh default profile for "Codexx Dev"
- **Render Optimization**:
  - Created `requirements.txt` from pyproject.toml
  - Created `build.sh` with proper permissions
  - Updated `render.yaml` with production configuration
  - Updated `Procfile` with Gunicorn settings (4 workers, 120s timeout)
- **Cleanup**:
  - Removed all backup files (data_backup_*.json)
  - Removed screenshot folder
  - Removed documentation HTML files (arabic/english variants)
  - Removed attached_assets folder
  - Updated `.gitignore` for cleaner repository
- **Documentation**:
  - Updated README.md with Render deployment instructions
  - Added comprehensive deployment guide
  - Documented all environment variables
- **Project State**: Production-ready, optimized for Render deployment

### Nov 7, 2025: Client Management System Added
- Added comprehensive client management with full CRUD operations
- Implemented client statistics dashboard (total, active, completed, revenue)
- Created client tracking with status management (Pending, Active, On Hold, Completed)
- Added project price and deadline tracking
- Implemented "Convert to Client" feature from messages
- Updated navigation with Clients section and active project badge
- All client templates follow luxury gold theme design
- Full integration with existing dashboard architecture

### Nov 6, 2025: GitHub Import Setup Completed
- Installed all Python dependencies (Flask, Werkzeug, WeasyPrint, Gunicorn, etc.)
- Configured workflow 'flask-app' for port 5000 webview
- Created .gitignore for Python project
- Configured deployment with Gunicorn for autoscale
- Verified application runs successfully on port 5000
- All features operational (portfolio, dashboard, CV generation, file uploads)
- Application ready for use and deployment

## Deployment on Render

### Quick Start
1. Push code to GitHub/GitLab
2. Connect repository to Render
3. Render auto-detects `render.yaml` and deploys
4. Access admin at: `https://your-app.onrender.com/dashboard/login`
5. Change default password immediately!

### Configuration
The project includes `render.yaml` with:
- Python 3.11 environment
- Automated build via `build.sh`
- Gunicorn server with 4 workers
- Auto-generated SESSION_SECRET and ADMIN_PASSWORD
- Environment variables pre-configured

## Development Notes
- Uses JSON file storage (no database required)
- Flask development server runs on 0.0.0.0:5000 (Replit)
- Gunicorn production server with 4 workers (Render)
- WeasyPrint handles PDF generation for CV downloads
- Bootstrap 5 provides responsive design framework
- Custom JavaScript handles theme toggling and animations
- All uploads stored in `static/assets/uploads/`

## Default Data (Codexx Dev)
The portfolio comes pre-configured with professional sample data for "Codexx Dev":
- **Name**: Codexx Dev
- **Title**: Full-Stack Developer & Software Engineer
- **Skills**: 8 professional skills (JavaScript, React, Python, Node.js, etc.)
- **Projects**: 7 sample projects with descriptions and images
- **Contact**: Placeholder contact information
- **Social**: Placeholder social media links
- All data can be easily modified via the admin dashboard

## Troubleshooting

### Replit Environment
- **Images not displaying**: Check upload directory permissions and file paths
- **Can't login**: Use default credentials admin/admin123, clear browser cache
- **PDF generation fails**: Ensure WeasyPrint is installed (already in dependencies)
- **Port conflicts**: Application is configured for port 5000 only

### Render Deployment
- **Build fails**: Check `build.sh` permissions and dependencies in `requirements.txt`
- **App crashes**: Verify environment variables are set correctly
- **Static files not loading**: Ensure `static/` directory structure is correct
- **Database errors**: This app uses JSON storage, no database needed

## User Preferences
- Clean, professional setup ready for immediate deployment
- All unnecessary files removed for production
- Optimized for both Replit development and Render production

## Production Checklist
✅ requirements.txt created  
✅ build.sh configured with execute permissions  
✅ render.yaml configured for production  
✅ Procfile updated with Gunicorn settings  
✅ .gitignore configured for clean repository  
✅ Default data cleaned and reset  
✅ All backup and temporary files removed  
✅ README.md updated with deployment instructions  
✅ Application tested and running successfully  

**Status**: Ready for deployment to Render! 🚀
