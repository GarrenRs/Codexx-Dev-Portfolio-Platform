# Portfolio Platform - Codexx Dev

A professional, feature-rich portfolio website with an integrated admin dashboard for easy content management. Built with Flask and modern web technologies.

## 🚀 Features

### 🎨 Modern Design
- **Responsive Design**: Perfect display on all devices (desktop, tablet, mobile)
- **Modern UI/UX**: Clean, professional interface with smooth animations
- **Bootstrap 5**: Latest Bootstrap framework for consistent styling

### 🛡️ Admin Dashboard
- **Secure Authentication**: Password-protected admin panel with session management
- **Content Management**: Easy-to-use interface for all portfolio sections
- **File Upload**: Secure image upload system with validation
- **Real-time Analytics**: Visitor tracking and message management
- **Client Management**: Track and manage client projects and inquiries

### 📊 Portfolio Sections
- **Hero Section**: Professional introduction with profile photo
- **About Section**: Detailed personal/professional information
- **Skills Section**: Animated progress bars showing technical proficiencies
- **Projects Portfolio**: Showcase projects with images, descriptions, and links
- **Contact Section**: Professional contact form with message management
- **CV Generation**: Professional CV preview and PDF download functionality
- **Social Media Integration**: Links to all major social platforms

### 📈 Analytics & Tracking
- **Visitor Counter**: Real-time visitor tracking and analytics
- **Message Management**: Contact form submissions with read/unread status
- **Client Management**: Track projects, deadlines, and revenue
- **Dashboard Statistics**: Overview of projects, skills, visitors, and messages

### 🔧 Technical Features
- **Flask Backend**: Python-based web framework
- **JSON Database**: Lightweight data storage solution
- **File Management**: Organized upload system for images
- **Security**: Input validation, secure file uploads, XSS protection
- **SEO Optimized**: Meta tags, sitemap, and performance optimization

## 📋 Requirements

- Python 3.11+
- See `requirements.txt` for all dependencies

## 🚀 Quick Start

### Local Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd portfolio-platform

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Access at: http://localhost:5000

### Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

> ⚠️ **Important**: Change the default password immediately after first login via Dashboard > Change Password!

## 🌐 Deployment on Render

### Prerequisites
1. Create a [Render](https://render.com) account
2. Connect your GitHub/GitLab repository

### Deployment Steps

#### Option 1: Using render.yaml (Recommended)

1. Push your code to GitHub/GitLab
2. In Render Dashboard, click "New +" → "Blueprint"
3. Connect your repository
4. Render will automatically detect `render.yaml` and deploy

The `render.yaml` file is already configured with:
- Python 3.11 environment
- Build command running `build.sh`
- Gunicorn server with 4 workers
- Auto-generated secrets for security

#### Option 2: Manual Setup

1. In Render Dashboard, click "New +" → "Web Service"
2. Connect your repository
3. Configure:
   - **Name**: portfolio-app (or your choice)
   - **Environment**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 app:app`
   - **Plan**: Free (or your choice)

4. Add Environment Variables:
   - `PYTHON_VERSION`: `3.11.0`
   - `SESSION_SECRET`: (Auto-generate a secret)
   - `ADMIN_USERNAME`: `admin`
   - `ADMIN_PASSWORD`: (Set a strong password)

5. Click "Create Web Service"

### Post-Deployment

1. Wait for the build to complete (2-3 minutes)
2. Access your portfolio at the provided Render URL
3. Login to dashboard at: `https://your-app.onrender.com/dashboard/login`
4. **Immediately change the admin password!**

## 📁 Project Structure

```
portfolio-platform/
├── static/
│   ├── assets/
│   │   └── uploads/          # Uploaded images
│   ├── css/
│   │   └── style.css         # Main stylesheet
│   └── js/
│       └── script.js         # JavaScript functionality
├── templates/
│   ├── dashboard/            # Admin dashboard templates
│   ├── index.html           # Main portfolio template
│   └── 404.html             # Error page
├── app.py                   # Main Flask application
├── data.json               # Data storage
├── requirements.txt        # Python dependencies
├── build.sh               # Render build script
├── render.yaml            # Render deployment config
├── Procfile              # Process file
└── README.md             # This file
```

## 🎯 Dashboard Sections

| Section | Purpose | Features |
|---------|---------|----------|
| **Home** | Dashboard overview | Statistics, quick actions, recent activity |
| **General** | Basic profile information | Name, title, description, profile photo |
| **About** | Detailed about section | Rich text editor |
| **Skills** | Technical skills management | Add/remove skills, proficiency levels |
| **Projects** | Portfolio management | CRUD operations, image uploads, technology tags |
| **Contact** | Contact information | Email, phone, location management |
| **Social** | Social media links | LinkedIn, GitHub, Twitter, Instagram, etc. |
| **Messages** | Contact form messages | View, mark as read, delete messages |
| **Clients** | Client management | Track projects, deadlines, revenue |
| **CV Preview** | CV generation and download | Professional CV preview, PDF download |

## 🔒 Security Features

- **Password Hashing**: Secure password storage with Werkzeug
- **Session Management**: Secure session handling with HTTP-only cookies
- **File Upload Validation**: Strict file type checking (16MB limit)
- **XSS Protection**: Input sanitization
- **Secure Filenames**: Safe file naming conventions
- **Automatic Backups**: Data preservation (keeps last 5 backups)
- **Environment Variables**: Sensitive data stored securely

## 🛠️ Configuration

### Environment Variables

Set these in Render Dashboard or `.env` file for local development:

```env
SESSION_SECRET=your-secure-random-secret-key-min-32-chars
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
FLASK_ENV=production
```

### File Uploads
- **Allowed formats**: PNG, JPG, JPEG, GIF, WebP
- **Upload directory**: `static/assets/uploads/`
- **Max file size**: 16MB
- **Recommended sizes**:
  - Profile images: 400x400px
  - Project images: 600x400px

## 🐛 Troubleshooting

### Common Issues

**Build fails on Render:**
- Check that `build.sh` has execute permissions: `chmod +x build.sh`
- Verify all dependencies are in `requirements.txt`
- Check Render build logs for specific errors

**Images not displaying:**
- Ensure uploads directory exists: `static/assets/uploads/`
- Check file permissions
- Verify file extensions are allowed

**Can't login to dashboard:**
- Check environment variables are set correctly
- Clear browser cookies and cache
- Verify SESSION_SECRET is set

**Application crashes:**
- Check Render logs for errors
- Ensure all environment variables are set
- Verify data.json format is valid

## 📊 Performance Tips

- Use Render's free tier for testing
- Upgrade to paid plans for better performance
- Enable CDN for static assets
- Optimize images before uploading
- Monitor Render logs regularly

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Render deployment logs
3. Check browser console for error messages

---

**Built with Flask, Bootstrap 5, and modern web technologies**

**Developer**: Codexx Dev  
**Portfolio**: https://your-app.onrender.com
