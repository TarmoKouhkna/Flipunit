#!/bin/bash
# Script to fix HTTP to HTTPS redirect issue
# Run this on the server: bash fix_http_redirect.sh

set -e

echo "🔧 Fixing HTTP to HTTPS redirect..."

# Backup current config
echo "📦 Creating backup..."
sudo cp /etc/nginx/sites-available/flipunit.eu /etc/nginx/sites-available/flipunit.eu.backup.$(date +%Y%m%d_%H%M%S)

# Create the fixed nginx config
echo "✏️  Creating fixed nginx configuration..."
sudo tee /etc/nginx/sites-available/flipunit.eu > /dev/null <<'EOF'
# Redirect HTTP to HTTPS (301 permanent redirect)
server {
    listen 80;
    server_name flipunit.eu www.flipunit.eu;
    return 301 https://flipunit.eu$request_uri;
}

# Redirect www to non-www HTTPS (301 permanent redirect)
server {
    listen 443 ssl;
    server_name www.flipunit.eu;
    ssl_certificate /etc/letsencrypt/live/flipunit.eu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/flipunit.eu/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    return 301 https://flipunit.eu$request_uri;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=100r/m;

# Main server block
server {
    server_name flipunit.eu;

    # Allow file uploads up to 5GB (matches Django's max_total_size limit)
    client_max_body_size 5G;

    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;

    # Remove security headers from sitemap.xml for Google Search Console compatibility
    # This MUST come BEFORE "location /" so it matches first
    location = /sitemap.xml {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Remove security headers that interfere with Google Search Console
        proxy_hide_header X-Frame-Options;
        proxy_hide_header X-Content-Type-Options;
        proxy_hide_header Referrer-Policy;
        proxy_hide_header Cross-Origin-Opener-Policy;
        proxy_hide_header X-Robots-Tag;
        
        # Ensure correct content type
        proxy_set_header Accept "application/xml";
        
        # Increase timeouts
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
    }

    location / {
        limit_req zone=general_limit burst=20 nodelay;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeouts for large file uploads and async jobs
        proxy_read_timeout 600s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 600s;
        
        # Disable buffering for large uploads
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # Rate limit converter endpoints
    location ~ ^/(text-converter/audio-transcription|media-converter|pdf-tools|image-converter|archive-converter)/ {
        limit_req zone=api_limit burst=2 nodelay;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 600s;
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # Health check endpoint (no rate limiting)
    location /health/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        access_log off;
    }

    location /static/ {
        alias /opt/flipunit/staticfiles/;
    }

    location /media/ {
        alias /opt/flipunit/media/;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/flipunit.eu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/flipunit.eu/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}
EOF

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration test passed!"
    
    # Reload nginx
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    
    echo ""
    echo "✅ SUCCESS! HTTP to HTTPS redirect has been fixed."
    echo ""
    echo "📋 Verifying the fix..."
    echo "Testing HTTP redirect:"
    curl -I http://flipunit.eu 2>/dev/null | head -n 5 || echo "Could not test (curl may not be available)"
    echo ""
    echo "✅ Fix applied successfully!"
else
    echo "❌ ERROR: Nginx configuration test failed!"
    echo "Restoring backup..."
    sudo cp /etc/nginx/sites-available/flipunit.eu.backup.* /etc/nginx/sites-available/flipunit.eu 2>/dev/null || true
    exit 1
fi
