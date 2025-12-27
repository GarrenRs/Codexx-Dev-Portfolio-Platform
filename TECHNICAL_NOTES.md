# Technical Notes & Architecture

## System Architecture

### Current Stack
```
Frontend
├── HTML Templates (Jinja2)
├── Bootstrap 5 CSS
├── Custom CSS Themes (8 variants)
└── Vanilla JavaScript

Backend
├── Flask 3.1.1
├── Werkzeug 3.1.3 (Security)
├── APScheduler 3.10.4 (Jobs)
└── WeasyPrint 65.1 (PDF)

Storage
├── data.json (JSON file)
├── static/assets/uploads/ (File uploads)
└── backups/ (Automatic backups)

Server
├── Flask dev: 0.0.0.0:5000
└── Gunicorn prod: 4 workers, 120s timeout
```

### Current Data Flow
```
User Request
    ↓
Flask Route
    ↓
Load data.json
    ↓
Process data
    ↓
Save data.json (with backup)
    ↓
Response
```

## Phase 0 Specific Notes

### Routes That Will NOT Change
- `/` - Home page (cosmetic updates only)
- `/catalog` - Project catalog (cosmetic updates only)
- `/cv-preview` - CV preview (cosmetic updates only)
- `/download-cv` - PDF download (system stays same)
- Error pages (400, 403, 404, 500, 503)

### Routes That WILL Change in Phase 1+
- `/dashboard/*` - Will be multi-user aware
- `/submit-message` - May have rate limiting per user

### Critical Functions to Preserve
- `load_data()` - Will change to database query
- `save_data()` - Will change to database commit
- `send_telegram_notification()` - Keep as is
- `send_email()` - Keep as is
- Password hashing functions - Replace with bcrypt in Phase 2

## Database Migration Strategy (Phase 1)

### Step 1: Create Tables
```sql
-- In parallel with JSON system
CREATE TABLE workspaces (...)
CREATE TABLE users (...)
CREATE TABLE projects (...)
...
```

### Step 2: Migrate Data
```python
# Read from JSON
# Write to database
# Verify counts match
```

### Step 3: Switch Over
```python
# Update load_data() to query database
# Update save_data() to commit database
# Remove JSON file (keep backup)
```

### Step 4: Rollback Plan
```
If issues:
1. Switch load_data() back to JSON
2. Keep both systems running for 24h
3. Identify issues
4. Fix and retry
```

## Performance Considerations

### Current Bottlenecks
1. **JSON File I/O**: ~5-10ms per load
2. **No Indexing**: All data scanned
3. **No Caching**: Regenerates every request
4. **Single File**: All data in one place

### Post-Phase 1 Improvements
1. Database indexing
2. Query optimization
3. Redis caching
4. Pagination for large datasets

## Security Notes

### Current Security
- ✅ Password hashing (Werkzeug)
- ✅ Session security (secure cookies)
- ✅ File validation (type & size)
- ⚠️ No rate limiting per user
- ⚠️ Single admin only
- ⚠️ No audit trail

### Post-Phase 4 Security
- JWT tokens
- Fine-grained permissions
- Audit logging
- Rate limiting per user
- API key management
- 2FA support (future)

## File Structure After Phase 1

```
app.py                      # Main application (refactored)
│
├── config.py              # Configuration
├── models.py              # Database models
├── auth.py                # Authentication logic
├── permissions.py         # Permission checking
│
├── routes/
│   ├── __init__.py
│   ├── public.py          # Public pages
│   ├── auth.py            # Login/logout
│   ├── dashboard.py       # Dashboard pages
│   ├── api.py             # API endpoints
│   └── admin.py           # Admin pages
│
├── templates/
│   ├── base.html
│   ├── public/
│   ├── dashboard/
│   ├── admin/
│   └── errors/
│
├── static/
│   ├── css/
│   ├── js/
│   ├── assets/
│   └── themes/
│
├── migrations/            # Alembic migrations
│
└── tests/
    ├── test_auth.py
    ├── test_routes.py
    └── test_permissions.py
```

## Important Variables & Constants

### In app.py
```python
ADMIN_CREDENTIALS = {
    'username': os.environ.get('ADMIN_USERNAME', 'admin'),
    'password_hash': generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))
}

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = 'static/assets/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

RATE_LIMIT_REQUESTS = 10  # per 60 seconds
RATE_LIMIT_WINDOW = 60    # seconds
```

### Theme List
- luxury-gold
- modern-dark
- clean-light
- silver-grey
- terracotta-red
- vibrant-green
- (+ 2 more)

## Testing Strategy

### Phase 0 Tests (Manual)
1. Login with admin/admin123 ✅
2. Create project ⏳
3. Create client ⏳
4. Send message ⏳
5. Download CV ⏳
6. Upload profile photo ⏳
7. Change theme ⏳
8. Change password ⏳

### Phase 1+ Tests (Automated)
- Unit tests for models
- Integration tests for routes
- Permission tests
- Plan limit tests

## Logging Strategy

### Current Logging
- IP logs (ip_log.json)
- Backup logs
- Error logs (Flask logger)

### Phase 1+ Logging
- Database audit logs
- User action logs
- API request logs
- Permission check logs

## Monitoring & Alerts (Future)

### Metrics to Track
- Login attempts
- Failed operations
- Backup success
- API errors
- Storage usage
- Plan limit usage

## Notes for Future Phases

1. **Phase 1**: Will introduce breaking changes - plan rollback strategy
2. **Phase 2**: Email system needed for invitations
3. **Phase 3**: Payment integration (Stripe/Paddle)
4. **Phase 4**: Consider adding webhook system
5. **Phase 5**: Admin API needed
6. **Phase 6**: Consider analytics integration
7. **Phase 7**: A/B testing framework
8. **Phase 8**: Monitor production closely

## Known Issues to Fix

1. APScheduler version mismatch (will fix in refactor)
2. No CORS support (needed for Phase 1 API)
3. No request validation (add in Phase 1)
4. Limited error messages (improve in Phase 1)

