# VPS Deployment Instructions - PDF to EPUB Feature

**Status:** Ready for deployment  
**Commits to deploy:**
- `8ece331` - Add PDF to EPUB conversion tool
- `9adfd48` - Fix EPUB TOC structure and improve navigation
- `86fa078` - Update deployment script and add deployment guide

---

## 🚀 Quick Deployment (Automated)

### Option 1: Use the automated deployment script

```bash
# Make sure you're in the project directory
cd /Users/tarmokouhkna/Documents/Flipunit

# Run the deployment script
./deploy_to_vps.sh ubuntu@217.146.78.140
```

This script will:
1. Push code to GitHub
2. SSH to VPS and pull latest code
3. Install ebooklib if needed
4. Collect static files
5. Restart the container
6. Verify deployment

---

## 📋 Manual Deployment Steps

If you prefer to deploy manually or the script doesn't work:

### Step 1: Push to GitHub

```bash
cd /Users/tarmokouhkna/Documents/Flipunit
git push origin main
```

### Step 2: Connect to VPS

```bash
ssh ubuntu@217.146.78.140
```

### Step 3: Deploy on VPS

Once connected to the VPS, run:

```bash
cd /opt/flipunit

# Pull latest code
git pull origin main

# Install ebooklib if not already installed
docker-compose exec -T web pip install ebooklib>=0.18

# Verify ebooklib is installed
docker-compose exec -T web python -c "import ebooklib; print('ebooklib version:', ebooklib.__version__)"

# Collect static files
docker-compose exec -T web python manage.py collectstatic --noinput

# Restart the web container
docker-compose restart web

# Check container status
docker-compose ps

# Check logs
docker-compose logs -f web
```

---

## ✅ Verification Steps

After deployment, verify everything works:

### 1. Check URL Accessibility

```bash
# From your local machine or VPS
curl -I https://flipunit.eu/pdf-tools/to-epub/
```

Should return: `200 OK` or `301/302 Redirect`

### 2. Test in Browser

1. Visit: `https://flipunit.eu/pdf-tools/to-epub/`
2. The page should load without errors
3. You should see the PDF to EPUB conversion form

### 3. Test Functionality

1. Upload a test PDF file (< 1MB)
2. Optionally add a cover image
3. Enter a custom title
4. Click "Convert to EPUB"
5. Verify EPUB file downloads
6. Open EPUB in an e-reader app to verify it works

### 4. Check Logs

```bash
# On VPS
cd /opt/flipunit
docker-compose logs -f web
```

Look for:
- No import errors for `ebooklib`
- No errors when accessing `/pdf-tools/to-epub/`
- Successful EPUB generation (if you test conversion)

---

## 🔧 Troubleshooting

### Issue: "ebooklib not found" error

**Solution:**
```bash
docker-compose exec -T web pip install ebooklib>=0.18
docker-compose restart web
```

### Issue: Page returns 404

**Check:**
1. URL routing is correct: `path('to-epub/', views.pdf_to_epub, name='pdf_to_epub')`
2. Container restarted: `docker-compose restart web`
3. Check logs: `docker-compose logs web | grep -i error`

### Issue: Container won't start

**Check logs:**
```bash
docker-compose logs web
```

**Common fixes:**
- Check if port 8000 is available
- Verify environment variables in `.env` file
- Check database connection

### Issue: EPUB generation fails

**Check:**
1. ebooklib is installed: `docker-compose exec -T web python -c "import ebooklib"`
2. PyMuPDF is installed: `docker-compose exec -T web python -c "import fitz"`
3. Check application logs for specific error messages

### Issue: Static files not loading

**Solution:**
```bash
docker-compose exec -T web python manage.py collectstatic --noinput
docker-compose restart web
```

---

## 📊 Post-Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Code pulled on VPS
- [ ] ebooklib installed in container
- [ ] Static files collected
- [ ] Container restarted
- [ ] URL accessible: `/pdf-tools/to-epub/`
- [ ] Page loads without errors
- [ ] Form displays correctly
- [ ] Test PDF upload works
- [ ] EPUB generation succeeds
- [ ] EPUB downloads correctly
- [ ] No errors in logs

---

## 🔄 Rollback (If Needed)

If something goes wrong, you can rollback:

```bash
# On VPS
cd /opt/flipunit

# Check recent commits
git log --oneline -5

# Rollback to previous commit (replace with actual commit hash)
git checkout <previous-commit-hash>

# Restart container
docker-compose restart web
```

Or revert the last commit:
```bash
git revert HEAD
git push origin main
# Then redeploy
```

---

## 📝 Notes

- The docker-compose.yml mounts source code, so Python changes are immediate after restart
- Template changes are also immediate (mounted as volume)
- Only need to rebuild if Dockerfile changes
- ebooklib needs to be installed in the container (not just in requirements.txt)

---

## ✅ Success Criteria

Deployment is successful when:

1. ✅ URL `https://flipunit.eu/pdf-tools/to-epub/` loads
2. ✅ No errors in browser console
3. ✅ Form displays correctly
4. ✅ Can upload PDF files
5. ✅ EPUB generation works
6. ✅ EPUB downloads successfully
7. ✅ No errors in container logs

---

**Ready to deploy!** Run `./deploy_to_vps.sh` or follow the manual steps above.

