# Deployment Readiness Checklist - tk_dev → main

**Date:** December 5, 2025  
**Branch:** tk_dev → main  
**Status:** ✅ **READY FOR DEPLOYMENT**

---

## 📋 Commits Ready to Merge

1. **efccdcb** - Clean up: remove static robots.txt, add documentation, minor formatting
2. **cbee5ea** - Complete margin unification: standardize spacing across all templates
3. **f91b41f** - Unify horizontal margins across all pages
4. **59fc30b** - Add live preview and loading state to Rotate & Flip Image tool

**Total changes:** 63 code files modified (Python, HTML, CSS, JS)

---

## ✅ Pre-Deployment Checklist

### 1. Code Status
- ✅ All changes committed to tk_dev
- ✅ All changes pushed to origin/tk_dev
- ✅ Working tree clean (no uncommitted changes)
- ✅ No merge conflicts with main branch

### 2. Dependencies
- ✅ `pillow-heif==0.13.0` in requirements.txt (for HEIC/HEIF support)
- ✅ All Python dependencies listed in requirements.txt
- ✅ Python version: 3.12 (matches runtime.txt)
- ✅ Django version: 5.2.8 (in requirements.txt)

### 3. Configuration Files
- ✅ Dockerfile configured correctly
  - Runs migrations automatically
  - Collects static files automatically
  - Installs all system dependencies (FFmpeg, pandoc, poppler, tesseract)
- ✅ docker-compose.yml configured
- ✅ deploy.sh script ready
- ✅ Static files configuration (WhiteNoise)

### 4. Database
- ✅ No new migrations in this deployment (only template/CSS changes)
- ✅ Existing migrations will run automatically via Dockerfile entrypoint

### 5. Static Files
- ✅ Static files configuration in settings.py
- ✅ WhiteNoise middleware configured
- ✅ collectstatic runs automatically in Dockerfile
- ✅ static/robots.txt removed (using template version)

### 6. New Features
- ✅ Live preview for Rotate & Flip Image tool
- ✅ Loading state on form submission buttons
- ✅ Unified horizontal margins across all pages
- ✅ Standardized spacing system (container variants, gap utilities)

### 7. Breaking Changes
- ⚠️ **None** - All changes are backward compatible
- ⚠️ CSS changes are additive (new classes, existing classes still work)
- ⚠️ Template changes maintain existing functionality

### 8. Environment Variables Required
The following must be set in production `.env` file:
- ✅ `SECRET_KEY` (required)
- ✅ `DEBUG=False` (for production)
- ✅ `ALLOWED_HOSTS=flipunit.eu,www.flipunit.eu,217.146.78.140`
- ✅ `CSRF_TRUSTED_ORIGINS=https://flipunit.eu,https://www.flipunit.eu`
- ✅ `SITE_URL=https://flipunit.eu`
- ✅ Database variables: `DB_NAME`, `DB_USER`, `DB_PASSWORD`

---

## 🚀 Deployment Steps

### Step 1: Merge to Main
```bash
git checkout main
git pull origin main
git merge tk_dev
git push origin main
```

### Step 2: Deploy to Production
On the production server:
```bash
cd /opt/flipunit
./deploy.sh
```

The deploy script will:
1. Check for uncommitted changes
2. Pull latest code from main
3. Check environment variables
4. Check Docker
5. Build Docker images (if needed)
6. Run migrations
7. Collect static files
8. Restart containers
9. Verify deployment

---

## 🔍 Post-Deployment Verification

After deployment, verify:

1. **Homepage loads correctly**
   - Check: https://flipunit.eu
   - Verify: Margins are consistent

2. **Rotate & Flip Image tool**
   - Check: https://flipunit.eu/image-converter/rotate-flip/
   - Verify: Live preview works when selecting actions
   - Verify: Button shows "Processing..." during submission

3. **All pages have consistent margins**
   - Check: Various tool pages
   - Verify: All use container-medium (1000px max-width)

4. **HEIC/HEIF support**
   - Check: Image converter accepts HEIC files
   - Verify: No errors about pillow-heif

5. **Static files**
   - Check: CSS loads correctly
   - Verify: No 404 errors for static assets

---

## 📝 Notes

- All template changes maintain backward compatibility
- CSS changes are additive (new utility classes)
- No database schema changes required
- No breaking API changes
- All dependencies are in requirements.txt

---

## ⚠️ Potential Issues & Solutions

### Issue: Static files not loading
**Solution:** Run `python manage.py collectstatic --noinput` manually if needed

### Issue: HEIC files not working
**Solution:** Verify `pillow-heif==0.13.0` is installed: `pip list | grep pillow-heif`

### Issue: CSS not applying
**Solution:** Clear browser cache, verify static files are collected

### Issue: Margins look different
**Solution:** Verify base.html uses `container-medium` class

---

## ✅ Final Status

**READY TO DEPLOY** - All checks passed, no blocking issues identified.
