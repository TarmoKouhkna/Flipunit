# Deployment Guide - PDF to EPUB Conversion Tool

**Status:** ✅ Code Committed Locally  
**Commit:** `9adfd48` - Fix EPUB TOC structure and improve navigation

---

## 📦 Deployment Steps

### 1. Push to Remote Repository

The changes have been committed locally. Push to remote:

```bash
git push origin main
```

If you encounter SSL certificate issues, you can temporarily disable verification:
```bash
git config --global http.sslVerify false
git push origin main
git config --global http.sslVerify true  # Re-enable after push
```

### 2. Server Deployment

#### Option A: If using Git-based deployment (recommended)
```bash
# On your production server
cd /path/to/your/project
git pull origin main
```

#### Option B: Manual deployment
1. Ensure all files are synced to production server
2. Verify `pdf_tools/views.py` has the latest changes
3. Verify `requirements.txt` includes `ebooklib>=0.18`

### 3. Install/Update Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate  # or your venv path

# Install/update dependencies
pip install -r requirements.txt

# Verify ebooklib is installed
python -c "import ebooklib; print('ebooklib version:', ebooklib.__version__)"
```

### 4. Django Management Commands

```bash
# Collect static files (if needed)
python manage.py collectstatic --noinput

# Run migrations (if any)
python manage.py migrate

# Check for errors
python manage.py check
```

### 5. Restart Application Server

#### If using Gunicorn:
```bash
# Find the process
ps aux | grep gunicorn

# Restart (method depends on your setup)
sudo systemctl restart gunicorn
# OR
sudo supervisorctl restart gunicorn
# OR kill and restart manually
```

#### If using Django development server:
```bash
# Stop current server (Ctrl+C)
# Start again
python manage.py runserver
```

#### If using Docker:
```bash
docker-compose restart
# OR
docker-compose up -d --build
```

### 6. Verify Deployment

1. **Check URL accessibility:**
   - Visit: `https://yourdomain.com/pdf-tools/to-epub/`
   - Should load without errors

2. **Test functionality:**
   - Upload a test PDF file
   - Try converting to EPUB
   - Verify EPUB downloads correctly

3. **Check logs:**
   ```bash
   # Django logs
   tail -f /path/to/logs/django.log
   
   # Gunicorn logs
   tail -f /path/to/logs/gunicorn.log
   
   # System logs
   journalctl -u gunicorn -f
   ```

---

## 🔍 Post-Deployment Verification

### Quick Tests

1. **URL Test:**
   ```bash
   curl -I https://yourdomain.com/pdf-tools/to-epub/
   # Should return 200 OK
   ```

2. **Dependency Check:**
   ```bash
   python manage.py shell
   >>> import ebooklib
   >>> from ebooklib import epub
   >>> print("✓ ebooklib available")
   ```

3. **View Test:**
   ```bash
   python manage.py shell
   >>> from pdf_tools.views import pdf_to_epub, EBOOKLIB_AVAILABLE
   >>> print(f"ebooklib available: {EBOOKLIB_AVAILABLE}")
   ```

### Functional Tests

1. **Test PDF Upload:**
   - Upload a small PDF (< 1MB)
   - Verify file validation works
   - Check error messages for invalid files

2. **Test EPUB Generation:**
   - Convert a simple PDF
   - Verify EPUB file downloads
   - Check EPUB opens in e-reader

3. **Test Options:**
   - Test with cover image
   - Test page break options
   - Test skip images option
   - Test tables as text option

4. **Test Multiple PDFs:**
   - Upload 2-3 PDFs
   - Verify they combine into one EPUB
   - Check TOC is clickable

---

## 🐛 Troubleshooting

### Issue: "ebooklib not available"
**Solution:**
```bash
pip install ebooklib>=0.18
# Restart server
```

### Issue: "Module not found: ebooklib"
**Solution:**
- Verify virtual environment is activated
- Check `requirements.txt` includes `ebooklib>=0.18`
- Reinstall: `pip install -r requirements.txt`

### Issue: EPUB generation fails
**Solution:**
- Check server logs for error details
- Verify PyMuPDF is installed: `pip install pymupdf`
- Check file permissions for temporary files

### Issue: Cover image not working
**Solution:**
- Verify PIL/Pillow is installed: `pip install pillow`
- Check image file size (max 5MB)
- Verify image format (PNG, JPG, JPEG, WebP)

### Issue: TOC not clickable
**Solution:**
- Verify latest code is deployed (commit `9adfd48`)
- Check EPUB structure with EPUB validator
- Test with different e-readers

---

## 📋 Deployment Checklist

- [ ] Code pushed to remote repository
- [ ] Dependencies installed (`ebooklib>=0.18`)
- [ ] Static files collected (if needed)
- [ ] Migrations run (if any)
- [ ] Server restarted
- [ ] URL accessible (`/pdf-tools/to-epub/`)
- [ ] Test PDF conversion works
- [ ] EPUB downloads correctly
- [ ] Cover image works
- [ ] TOC is clickable
- [ ] Error handling works
- [ ] Logs checked for errors

---

## 📊 Monitoring

After deployment, monitor:

1. **Error Logs:**
   - Check for any conversion errors
   - Monitor file size issues
   - Watch for memory problems

2. **Performance:**
   - Large PDF processing time
   - Memory usage during conversion
   - Server response times

3. **User Feedback:**
   - Monitor user reports
   - Check for common issues
   - Track conversion success rate

---

## 🔄 Rollback Plan

If issues occur, rollback to previous commit:

```bash
# On server
git log --oneline -5  # Find previous working commit
git checkout <previous-commit-hash>
# Restart server
```

Or revert the last commit:
```bash
git revert HEAD
git push origin main
```

---

## ✅ Success Criteria

Deployment is successful when:

1. ✅ URL loads without errors
2. ✅ PDF upload works
3. ✅ EPUB generation succeeds
4. ✅ EPUB downloads correctly
5. ✅ EPUB opens in e-readers
6. ✅ TOC is clickable
7. ✅ Cover image works
8. ✅ All options work correctly
9. ✅ Error handling works
10. ✅ No errors in logs

---

**Deployment Date:** December 22, 2025  
**Commit:** `9adfd48`  
**Status:** Ready for deployment

