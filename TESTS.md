# Testing Plan

## Phase 0: Manual Testing Checklist

### Portfolio Display
- [ ] Home page loads
- [ ] All theme CSS files load
- [ ] Logo displays
- [ ] Layout responsive on mobile/tablet/desktop
- [ ] Links work (to dashboard, cv, etc)

### Authentication
- [ ] Login with correct credentials works
- [ ] Login with wrong credentials fails
- [ ] Session persists across pages
- [ ] Logout clears session

### Portfolio Management
- [ ] Can edit name and title
- [ ] Can edit about section
- [ ] Can add/edit/delete skills
- [ ] Can add/edit/delete projects
- [ ] Project images upload correctly
- [ ] Can set project demo and github URLs

### Client Management
- [ ] Can add clients
- [ ] Can edit clients
- [ ] Can delete clients
- [ ] Client status options work
- [ ] Price field accepts numbers
- [ ] Deadline field accepts dates

### Contact & Messages
- [ ] Contact form submits
- [ ] Message appears in dashboard
- [ ] Can mark message as read/unread
- [ ] Messages don't reappear after delete

### Settings
- [ ] Can change theme
- [ ] Theme persists after reload
- [ ] Can edit contact info
- [ ] Can edit social links
- [ ] Can change password

### File Operations
- [ ] Profile photo uploads
- [ ] Only allowed types accepted
- [ ] File size limit enforced
- [ ] Uploaded files display
- [ ] CV preview generates
- [ ] CV PDF downloads

### Performance
- [ ] Page loads in < 2 seconds
- [ ] Dashboard loads in < 1 second
- [ ] Bulk operations complete quickly

### Security
- [ ] Can't access dashboard without login
- [ ] Can't access other user data (single user)
- [ ] File upload validation works
- [ ] SQL injection not possible (uses ORM in future)

## Phase 1+ Testing (Automated)

### Unit Tests
```python
# test_models.py
def test_workspace_creation()
def test_user_creation()
def test_project_creation()
def test_user_workspace_assignment()
```

### Integration Tests
```python
# test_routes.py
def test_login_flow()
def test_create_and_view_project()
def test_project_isolation_between_workspaces()
def test_message_submission()
```

### Permission Tests
```python
# test_permissions.py
def test_user_cannot_access_other_workspace()
def test_manager_can_edit()
def test_viewer_cannot_edit()
```

### Load Tests
```
# Test 100 concurrent users
# Test 1000 projects per workspace
# Test response times under load
```

## Test Execution Schedule

- Phase 0: Manual testing before Phase 1
- Phase 1: Automated tests for core features
- Phase 2: Tests for multi-user auth
- Phase 3: Tests for subscription limits
- Phase 4: Tests for permissions
- Phase 5: Admin dashboard tests
- Phase 6-8: Comprehensive test coverage

