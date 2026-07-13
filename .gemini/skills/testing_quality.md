# Testing & Quality Assurance - Matatucas LMS

## Pre-deployment Checklist

### 1. Server Startup
```bash
# Always kill zombie processes first
taskkill /F /IM python.exe /T
# Then start
python run.py
```

### 2. Critical Routes to Verify
After any code change, these routes must load without errors:

| Route | Expected | Who Can Access |
|-------|----------|----------------|
| `/` | Landing page with course cards | Everyone |
| `/auth/login` | Microsoft SSO button | Unauthenticated |
| `/docente/dashboard` | 6 metric cards + course list | Docente |
| `/admin/dashboard` | Admin metrics + audit log | Admin |
| `/cursos/<id>` | Course hero + lesson list + sidebar | Everyone |
| `/cursos/<id>/alumnos` | Student list with metrics | Docente owner |
| `/cursos/<id>/analytics` | Analytics dashboard | Docente owner |
| `/cursos/<id>/exportar-alumnos` | Downloads Excel file | Docente owner |
| `/fake-404-page` | Custom 404 page | Everyone |

### 3. Functional Tests

#### Course Management
- [ ] Create course → appears in dashboard
- [ ] Edit course → changes persist
- [ ] Publish course → visible to students
- [ ] Unpublish course → hidden from students
- [ ] Duplicate course → deep copy with new code
- [ ] Delete course (borrador) → fully removed
- [ ] Delete course (published with students) → blocked

#### Lesson Management
- [ ] Create lesson with all section types
- [ ] Edit lesson → sections update correctly
- [ ] Delete lesson → reorders remaining lessons
- [ ] Drag-and-drop reorder → persists order

#### Student Flow
- [ ] Enroll via code → inscripcion created
- [ ] Complete lesson → progress updates
- [ ] Complete exercises → attempts recorded
- [ ] 100% progress → certificate downloadable

### 4. Security Tests
- [ ] Student cannot access `/docente/dashboard`
- [ ] Student cannot edit/delete/publish courses
- [ ] Non-owner docente cannot manage another's course
- [ ] CSRF token required on all POST forms
- [ ] API endpoints require authentication

### 5. Performance Tests
- Course with 50+ students: `/alumnos` page loads in < 2s
- Dashboard with 10+ courses: loads in < 1s
- Excel export with 100+ students: generates in < 5s

## Debugging Workflow
1. Check Flask console for Python tracebacks
2. Check browser DevTools Console for JS errors
3. Check Network tab for failed requests (4xx/5xx)
4. If MySQL issues: check `C:\xampp\mysql\data\mysql_error.log`
5. If authentication issues: verify Azure AD redirect URIs

## Git Workflow
```bash
# Before committing
git status                    # Check what changed
git diff                      # Review changes
git add .
git commit -m "descripcion"   # Descriptive Spanish message
git push origin main
```

## Common Pitfalls
1. **Forgetting `_curso` parameter** when using `@curso_owner_required`
2. **Missing `csrf_token()`** in POST forms → 400 Bad Request
3. **Missing imports** (abort, func, or_) after adding optimized queries
4. **Template `{% if %}` blocks** not matching `{% endif %}`
5. **Flask-Login** `login_required` must come BEFORE role decorators
