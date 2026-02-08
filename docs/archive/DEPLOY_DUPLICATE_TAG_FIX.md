# Deploy Duplicate Tag Fix - Instructions

## Issue

SEO tool is still showing old placeholder text with HTML tags in:
- `/pdf-tools/universal/`
- `/pdf-tools/html-to-pdf/`

The tool shows the OLD code because changes haven't been deployed yet.

## Fix Applied (Local)

✅ **Placeholder text changed to plain text:**
- Removed all HTML-like content from placeholders
- Changed to simple: `placeholder="Paste your HTML content here"`

**Files Changed:**
- `templates/pdf_tools/html_to_pdf.html` (line 28)
- `templates/pdf_tools/universal.html` (line 52)

## Deploy Steps

### 1. Commit and Push Changes

```bash
# On your local machine
git add templates/pdf_tools/html_to_pdf.html templates/pdf_tools/universal.html
git commit -m "Fix SEO: Remove HTML tags from textarea placeholders to prevent duplicate closing tag detection"
git push origin main
```

### 2. Deploy to VPS

```bash
# SSH to VPS
ssh ubuntu@217.146.78.140

# Pull latest changes
cd /opt/flipunit
git pull

# Restart web container
docker-compose restart web
```

### 3. Verify Fix

After deployment, verify the placeholder is updated:

```bash
# Check the rendered HTML
curl -s https://flipunit.eu/pdf-tools/html-to-pdf/ | grep -A 2 'textarea.*html_content'
# Should show: placeholder="Paste your HTML content here"

curl -s https://flipunit.eu/pdf-tools/universal/ | grep -A 2 'textarea.*html_content'
# Should show: placeholder="Paste your HTML content here"
```

### 4. Wait for Re-Crawl

- SEO tools need to re-crawl (24-48 hours)
- The tool is currently showing cached/old content
- After re-crawl, duplicate tag issues should be resolved

## Expected Result

After deployment and re-crawl:
- ✅ No duplicate `</head>` tags
- ✅ No duplicate `</body>` tags  
- ✅ No duplicate `</html>` tags
- ✅ Clean HTML structure

---

**Status:** ✅ Fix ready - Deploy to see changes
