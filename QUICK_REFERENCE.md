# Quick Reference - Development Guide

## 🎯 Current Phase: 0 - ✅ COMPLETED (Dec 27)
**Next Phase**: Phase 1 - Workspace Architecture (Ready to begin)

### Login Credentials
- **Username**: admin
- **Password**: admin123
- **Status**: ✅ Working

### Key Endpoints
| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/` | Home page | ✅ |
| `/dashboard/login` | Admin login | ✅ |
| `/dashboard` | Main dashboard | ✅ |
| `/dashboard/general` | Edit profile | ✅ |
| `/dashboard/projects` | Manage projects | ✅ |
| `/dashboard/clients` | Manage clients | ✅ |
| `/dashboard/messages` | View messages | ✅ |
| `/cv-preview` | CV preview | ✅ |
| `/download-cv` | Download CV PDF | ✅ |

### Data Structure
```javascript
// Main object in data.json
{
  name: "",
  title: "",
  about: "",
  skills: [],
  projects: [],
  clients: [],
  messages: [],
  contact: {},
  social: {},
  visitors: {},
  settings: {}
}
```

### Routes Count: 28
- Public: 5
- Auth: 3
- Dashboard: 18
- Error: 5

### Tech Stack
- **Backend**: Flask 3.1.1
- **Frontend**: Bootstrap 5 + Custom CSS
- **Database**: JSON (Phase 1: PostgreSQL)
- **Server**: Gunicorn (4 workers)
- **Port**: 5000

### Dependencies (11 main)
1. Flask==3.1.1
2. Werkzeug==3.1.3
3. Gunicorn==23.0.0
4. WeasyPrint==65.1
5. APScheduler==3.10.4
6. email-validator
7. flask-login
8. flask-sqlalchemy
9. flask-dance
10. psycopg2-binary
11. PyJWT

### Themes (8 available)
1. luxury-gold (default)
2. modern-dark
3. clean-light
4. silver-grey
5. terracotta-red
6. vibrant-green
7. + 2 more

## 📊 Phase Roadmap

| Phase | Name | Status | Days | Key Feature | Completed |
|-------|------|--------|------|------------|-----------|
| 0 | Stabilization | ✅ COMPLETED | 1 | Documentation | ✅ Dec 27 |
| 1 | Workspace | 🔴 Pending | 3-4 | Multi-tenant | - |
| 2 | Auth | 🔴 Pending | 2-3 | Multi-user | - |
| 3 | Plans | 🔴 Pending | 3-4 | Subscriptions | - |
| 4 | Permissions | 🔴 Pending | 2-3 | RBAC | - |
| 5 | Super Admin | 🔴 Pending | 2-3 | Platform mgmt | - |
| 6 | Landing/Onboard | 🔴 Pending | 2-3 | New user flow | - |
| 7 | UI Adaptation | 🔴 Pending | 2-3 | Smart UI | - |
| 8 | Testing/Launch | 🔴 Pending | 3-5 | Production | - |

## 🔐 Security Checklist

- [x] Password hashing (Werkzeug)
- [x] Session security (secure cookies)
- [x] File validation (type & size)
- [x] CSRF protection (Flask sessions)
- [x] XSS protection (Jinja2)
- [ ] Rate limiting (in Phase 1)
- [ ] Audit logging (in Phase 1)
- [ ] 2FA support (in Phase 3+)

## 📝 Documentation Files

| File | Purpose | Priority |
|------|---------|----------|
| DEVELOPMENT.md | Master plan (8 phases) | HIGH |
| PHASE_0_CHECKLIST.md | Detailed Phase 0 tasks | HIGH |
| TECHNICAL_NOTES.md | Architecture decisions | MEDIUM |
| TESTS.md | Testing strategy | MEDIUM |
| SETUP.md | Installation guide | MEDIUM |
| QUICK_REFERENCE.md | This file | QUICK |

## ⚡ Fast Commands

```bash
# Start app
python app.py

# Check status
curl http://localhost:5000/

# View logs
tail -f /tmp/logs/flask-app*.log

# Create backup
cp data.json data.json.backup

# Restore backup
cp data.json.backup data.json
```

## 🐛 Common Issues

| Issue | Solution | Docs |
|-------|----------|------|
| Port in use | Kill process on :5000 | SETUP.md |
| Upload fails | Check static/assets/uploads/ | TECHNICAL_NOTES.md |
| PDF error | pip install weasyprint | SETUP.md |
| Login fails | Clear cache, try admin/admin123 | SETUP.md |

## 📅 Next 30 Days

```
Week 1: Phase 0 (Stabilization) - Documentation & Testing
Week 2: Phase 1 (Workspace) - Database & ORM setup
Week 3: Phase 2 (Auth) - Multi-user support
Week 4: Phase 3 (Plans) - Subscription system
+ Phases 4-8 follow the same pattern
```

## 💾 Backup Strategy

- **Hourly**: Automatic (APScheduler)
- **Manual**: Before any major change
- **Location**: `/backups/backup_*.json`
- **Retention**: Last 20 backups

## 🚀 Ready to Start?

1. Read: DEVELOPMENT.md
2. Review: PHASE_0_CHECKLIST.md
3. Execute: Test all features
4. Approve: Sign off on Phase 0
5. Begin: Phase 1 (Workspace)

---

**Last Updated**: Dec 27, 2025
**Status**: Phase 0 - Testing Phase ✅
