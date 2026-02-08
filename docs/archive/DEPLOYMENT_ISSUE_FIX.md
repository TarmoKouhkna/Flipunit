# Deployment Issue - Template Files Not Updated

## Problem

The fix is committed and pushed to GitHub, but the live site still shows:
- Old placeholder: `placeholder="<html><head>..."`
- Duplicate closing tags: 2 `</body>` and 2 `</head>` tags

## Root Cause

**Templates are volume-mounted** in `docker-compose.yml`:
```yaml
volumes:
  - ./templates:/app/templates  # Mount templates so changes are immediate
```

This means:
- Container uses files directly from `/opt/flipunit/templates/` on VPS
- Git pull may not have updated the files properly
- Files on VPS may be out of sync with GitHub

## Solution

### Step 1: Force Update Files on VPS

SSH to VPS and run:

```bash
cd /opt/flipunit

# Check current state
git status
git log --oneline -5

# Force pull latest changes
git fetch origin
git reset --hard origin/main

# Verify files are updated
grep 'placeholder=' templates/pdf_tools/html_to_pdf.html | grep html_content
# Should show: placeholder="Paste your HTML content here"
```

### Step 2: Restart Container

Since templates are volume-mounted, just restart:

```bash
docker-compose restart web
```

### Step 3: Verify Fix

```bash
# Wait a few seconds for container to restart
sleep 5

# Check placeholder
curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -o 'textarea[^>]*placeholder="[^"]*"' | grep html_content
# Should show: placeholder="Paste your HTML content here"

# Check for duplicate tags (should be 1 each)
curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -o '</body>' | wc -l
# Should show: 1
```

## Expected Result

After fixing:
- ✅ Placeholder: `placeholder="Paste your HTML content here"` (no HTML tags)
- ✅ Closing tags: 1 `</body>`, 1 `</head>`, 1 `</html>`
- ✅ No duplicate tags

---

**Status:** ⚠️ Needs manual fix on VPS
