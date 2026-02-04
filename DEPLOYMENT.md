# Deployment Guide: Hetzner VPS with Docker

This guide will walk you through deploying your FlipUnit.eu Django application to a Hetzner Cloud VPS using Docker. No prior experience with Docker or server management is required - we'll cover everything step by step.

## What You'll Need

Before starting, make sure you have:

1. **Hetzner Cloud Account**
   - **Recommended: CX22** (or larger) - 2 vCPU, 4 GB RAM, 40 GB SSD (or choose a plan that fits your needs)
   - Create a server at [Hetzner Cloud Console](https://console.hetzner.cloud/) with Ubuntu 24.04 (or 22.04), and add your SSH public key during creation
   - Your VPS should be running and you should have SSH access (as `root` or `ubuntu` depending on image)

2. **Your Domain**
   - Domain: `flipunit.eu` (DNS can remain at Zone.ee or your current registrar; you will point A records to your Hetzner server IP)

3. **Your Code**
   - Your Flipunit code should be in a GitHub repository (or you can upload it manually)

4. **Basic Terminal/SSH Knowledge**
   - You'll need to connect to your server via SSH
   - We'll use simple commands that we'll explain as we go

## Overview: What We're Going to Do

1. Set up SSH key (for secure VPS access)
2. Connect to your VPS server
3. Install Docker and Docker Compose
4. Set up your application files
5. Create Docker configuration files
6. Set up the database
7. Configure Nginx (web server)
8. Set up SSL certificate (HTTPS)
9. Configure DNS
10. Test your deployment

**Estimated time**: 1-2 hours (depending on your experience level)

---

## Step 1: Set Up SSH Key (Before Creating Server)

**Important**: Hetzner Cloud will ask for your SSH public key when you create a server. Set this up first!

### 1.1 Check if You Already Have an SSH Key

**On Mac/Linux:**
Open Terminal and run:
```bash
ls -la ~/.ssh/id_*.pub
```

If you see files like `id_rsa.pub` or `id_ed25519.pub`, you already have a key! Skip to step 1.3.

**On Windows:**
Open PowerShell or Command Prompt and run:
```bash
dir %USERPROFILE%\.ssh\id_*.pub
```

### 1.2 Generate a New SSH Key (If You Don't Have One)

**On Mac/Linux:**
```bash
ssh-keygen -t ed25519 -C "flipunit-vps" -f ~/.ssh/id_ed25519
```

When prompted:
- **"Enter passphrase"**: Press Enter (no passphrase needed, or set one for extra security)
- **"Enter same passphrase again"**: Press Enter again

**On Windows:**
If you have Git Bash or WSL:
```bash
ssh-keygen -t ed25519 -C "flipunit-vps" -f ~/.ssh/id_ed25519
```

Or use PuTTYgen (download from https://www.putty.org/):
1. Open PuTTYgen
2. Click "Generate"
3. Move your mouse to generate randomness
4. Click "Save public key" and save it somewhere
5. Copy the text in the "Public key for pasting" box

### 1.3 Get Your Public Key

**On Mac/Linux:**
```bash
cat ~/.ssh/id_ed25519.pub
```

**On Windows (if using Git Bash/WSL):**
```bash
cat ~/.ssh/id_ed25519.pub
```

**On Windows (if using PuTTYgen):**
Copy the text from the "Public key for pasting" box

### 1.4 Copy Your Public Key

You'll see output like this:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGeb6G1zX68sBXpmabDmwxaMT/Aoor2AGGsD7AjK0B33 flipunit-vps
```

**Copy the entire line** (from `ssh-ed25519` to the end).

### 1.5 Add to Hetzner Cloud

When creating your server in the Hetzner Cloud Console:
1. Under "SSH Keys", add your public key (paste the entire line you copied), or choose an existing key
2. Complete the server creation

**Important Notes:**
- The **public key** is safe to share - that's what you add in Hetzner
- The **private key** stays on your computer - never share it!
- After adding your key, you can connect to the server without a password

---

## Step 2: Connect to Your VPS Server

### 2.1 Get Your VPS Information

After your server is created in Hetzner Cloud Console you will have:
- **Server IP Address** (e.g., `95.217.x.x`) - shown in the server list and details
- **SSH access**: Ubuntu images typically use user `root`; you can create an `ubuntu` user and use that if you prefer (see Step 3 for `sudo` usage)

### 2.2 Connect via SSH

**On Mac/Linux:**
Open Terminal and run (use your actual Hetzner server IP):
```bash
ssh root@your-server-ip
```
If you created an `ubuntu` user:
```bash
ssh ubuntu@your-server-ip
```

**On Windows:**
- Use **PuTTY** (download from https://www.putty.org/) or **Windows Terminal** with the same commands

**If you added your SSH key in Hetzner:** you should connect without a password.

**First time connecting?** You may see a message asking to confirm the server's identity. Type `yes` and press Enter.

✅ **Success check**: You should see a command prompt like `root@your-server:~$` or `ubuntu@your-server:~$`

---

## Step 3: Update Your Server

Before installing anything, let's update the server's software:

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

**Note**: Since you're logged in as `ubuntu` user (not `root`), you need to use `sudo` before admin commands.

This ensures you have the latest security updates. It may take a few minutes.

---

## Step 4: Install Docker

Docker is a tool that packages your application and all its dependencies into containers. This makes deployment much easier.

### 4.1 Install Docker

Run these commands one by one:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

This downloads and installs Docker. Wait for it to complete.

**Important**: After installing Docker, add your `ubuntu` user to the docker group so you don't need `sudo` for docker commands:

```bash
sudo usermod -aG docker ubuntu
```

**You'll need to log out and log back in** for this to take effect. For now, you can use `sudo docker` commands.

### 4.2 Install Docker Compose

Docker Compose helps manage multiple containers (your app + database):

```bash
sudo apt-get install -y docker-compose
```

### 4.3 Verify Installation

Check that Docker is installed correctly:

```bash
docker --version
docker-compose --version
```

You should see version numbers. If you see errors, let's troubleshoot in the Troubleshooting section.

✅ **Success check**: Both commands should show version numbers without errors.

---

## Step 5: Prepare Your Application Directory

### 5.1 Create Application Directory

We'll store your application in `/opt/flipunit`:

```bash
sudo mkdir -p /opt/flipunit
cd /opt/flipunit
```

**Note**: You may need to change ownership so the `ubuntu` user can write to this directory:
```bash
sudo chown -R ubuntu:ubuntu /opt/flipunit
```

### 5.2 Get Your Code

You have two options:

**Option A: Clone from GitHub (Recommended)**

First, install Git:
```bash
sudo apt-get install -y git
```

Then clone your repository:
```bash
git clone https://github.com/your-username/Flipunit.git .
```
*(Replace `your-username` with your actual GitHub username)*

**Option B: Upload Files Manually**

If your code isn't on GitHub, you can upload it using:
- **SCP** (from your local computer): `scp -r /path/to/your/code root@your-vps-ip:/opt/flipunit/`
- **SFTP client** like FileZilla
- Or use `nano` to create files directly on the server

✅ **Success check**: Run `ls` in `/opt/flipunit` - you should see your project files (like `manage.py`, `requirements.txt`, etc.)

---

## Step 6: Create Docker Configuration Files

We need to create two files that tell Docker how to run your application.

### 6.1 Create Dockerfile

The Dockerfile tells Docker how to build your application container:

```bash
cd /opt/flipunit
nano Dockerfile
```

This opens the `nano` text editor. Copy and paste this entire content:

```dockerfile
FROM python:3.11-slim

# Install system dependencies including FFmpeg, pandoc, and poppler
RUN apt-get update && apt-get install -y \
    ffmpeg \
    postgresql-client \
    pandoc \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directories for media and static files
RUN mkdir -p /app/media /app/staticfiles

# Expose port
EXPOSE 8000

# Start script
CMD python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    gunicorn flipunit.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

**To save in nano:**
- Press `Ctrl + O` (that's the letter O, not zero)
- Press `Enter` to confirm
- Press `Ctrl + X` to exit

### 6.2 Create docker-compose.yml

This file manages both your web application and database:

```bash
nano docker-compose.yml
```

Copy and paste this content:

```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: flipunit-web
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - ALLOWED_HOSTS=flipunit.eu,www.flipunit.eu
      - DB_NAME=flipunit
      - DB_USER=flipunit_user
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=postgres
      - DB_PORT=5432
    volumes:
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles
      - ./templates:/app/templates  # Mount templates so changes are immediate without rebuild
    depends_on:
      - postgres
    networks:
      - flipunit-network

  postgres:
    image: postgres:15
    container_name: flipunit-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=flipunit
      - POSTGRES_USER=flipunit_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - flipunit-network

volumes:
  postgres-data:

networks:
  flipunit-network:
```

Save the file (Ctrl+O, Enter, Ctrl+X).

✅ **Success check**: Run `ls` - you should see both `Dockerfile` and `docker-compose.yml`

---

## Step 7: Create Environment Variables File

We need to store sensitive information like passwords in a `.env` file.

### 7.1 Generate a Secret Key

First, let's generate a secure secret key for Django. Run this command:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Copy the long string that appears** - you'll need it in the next step.

### 7.2 Create .env File

```bash
nano .env
```

Add these lines (replace the values with your own):

```env
SECRET_KEY=your-generated-secret-key-from-step-6.1
DEBUG=False
DB_PASSWORD=choose-a-strong-password-here
ALLOWED_HOSTS=flipunit.eu,www.flipunit.eu,YOUR_SERVER_IP
```

**Important:**
- Replace `your-generated-secret-key-from-step-6.1` with the secret key you copied
- Replace `choose-a-strong-password-here` with a strong password (at least 16 characters, mix of letters, numbers, and symbols)
- Replace `YOUR_SERVER_IP` with your Hetzner server's public IP (from `curl ifconfig.me` on the server). This allows direct IP access and health checks.
- **Never share this file or commit it to GitHub!**

Save the file (Ctrl+O, Enter, Ctrl+X).

✅ **Success check**: Run `cat .env` - you should see your environment variables (don't worry, you're the only one who can see this on your server)

---

## Step 8: Build and Start Your Application

Now let's build and start everything:

### 8.1 Build Docker Images

This downloads dependencies and prepares your application:

```bash
cd /opt/flipunit
docker-compose build
```

**This will take 5-10 minutes** the first time as it downloads Python, PostgreSQL, and all dependencies. You'll see lots of output - that's normal!

### 8.2 Start the Containers

Once building is complete:

```bash
docker-compose up -d
```

The `-d` flag runs containers in the background (detached mode).

### 8.3 Check Status

Verify everything is running:

```bash
docker-compose ps
```

You should see both `flipunit-web` and `flipunit-postgres` with status "Up".

### 8.4 Check Logs

If something went wrong, check the logs:

```bash
docker-compose logs web
```

Look for any error messages. Common issues:
- **Database connection errors**: Check your `.env` file has the correct `DB_PASSWORD`
- **Port already in use**: Something else might be using port 8000

✅ **Success check**: Both containers should show "Up" status, and logs should show Django starting successfully.

---

## Step 9: Create Admin User

Create a superuser account to access Django admin:

```bash
docker-compose exec web python manage.py createsuperuser
```

Follow the prompts:
- Username: (choose a username)
- Email: (your email)
- Password: (choose a strong password)

✅ **Success check**: You should see "Superuser created successfully."

---

## Step 10: Test Your Application Locally

Before setting up the domain, let's test that it works:

### 10.1 Check if Application is Running

```bash
curl http://localhost:8000
```

You should see HTML output (your website's content).

### 10.2 Test from Your Computer

**Important**: You need to allow port 8000 through the firewall first (we'll do this properly in Step 11). For now, if you want to test:

1. Note your VPS IP address
2. In your browser, try: `http://your-vps-ip:8000`

You should see your website! (It won't have HTTPS yet - we'll add that next)

---

## Step 11: Install and Configure Nginx

Nginx is a web server that will:
- Serve your application to the internet
- Handle SSL/HTTPS
- Serve static files efficiently

### 11.1 Install Nginx

```bash
sudo apt-get install -y nginx
```

### 11.2 Create Nginx Configuration

```bash
nano /etc/nginx/sites-available/flipunit.eu
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name flipunit.eu www.flipunit.eu;
    
    # Allow file uploads up to 700MB
    client_max_body_size 700M;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for large file uploads
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
    
    location /static/ {
        alias /opt/flipunit/staticfiles/;
    }
    
    location /media/ {
        alias /opt/flipunit/media/;
    }
}
```

Save the file (Ctrl+O, Enter, Ctrl+X).

### 11.3 Enable the Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/flipunit.eu /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t
```

You should see "syntax is ok" and "test is successful".

### 11.4 Restart Nginx

```bash
sudo systemctl restart nginx
```

✅ **Success check**: Run `sudo systemctl status nginx` - it should show "active (running)"

---

## Step 12: Set Up SSL Certificate (HTTPS)

We'll use Let's Encrypt to get a free SSL certificate for HTTPS.

### 12.1 Install Certbot

```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

### 12.2 Get SSL Certificate

```bash
sudo certbot --nginx -d flipunit.eu -d www.flipunit.eu
```

**Follow the prompts:**
- Email address: Enter your email (for renewal notifications)
- Agree to terms: Type `A` and press Enter
- Share email: Your choice (Y or N)
- Redirect HTTP to HTTPS: Choose `2` (recommended)

Certbot will automatically configure Nginx for HTTPS!

✅ **Success check**: Visit `https://flipunit.eu` - you should see a padlock icon in your browser!

---

## Step 13: Configure Firewall

Protect your server by only allowing necessary ports:

### 13.1 Install and Configure UFW (Firewall)

```bash
# Install UFW if not already installed
sudo apt-get install -y ufw

# Allow SSH (important - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

When asked "Command may disrupt existing ssh connections. Proceed?", type `y` and press Enter.

✅ **Success check**: Run `ufw status` - you should see the allowed ports listed.

---

## Step 14: Configure DNS

Now we need to point your domain to your Hetzner server.

### 14.1 Get Your Server IP Address

On your Hetzner server (or from the Hetzner Cloud Console), get the public IP:

```bash
curl ifconfig.me
```

Copy this IP address - you'll need it for DNS and for `.env` (ALLOWED_HOSTS).

### 14.2 Configure DNS (e.g. at Zone.ee)

If your domain is managed at Zone.ee (or another registrar):

1. Log into your DNS control panel (e.g. Zone.ee)
2. Go to DNS management for `flipunit.eu`
3. Add or edit these DNS records (use your **Hetzner server IP** from step 14.1):

   **A Record:**
   - Name: `@` (or leave blank, depending on the interface)
   - Value: `your-hetzner-server-ip`
   - TTL: 3600 (or 300 for faster propagation before go-live)

   **A Record:**
   - Name: `www`
   - Value: `your-hetzner-server-ip` (same IP)
   - TTL: 3600 (or 300)

4. Save the changes

### 14.3 Wait for DNS Propagation

DNS changes can take anywhere from a few minutes to 48 hours to propagate. Usually it's 15-30 minutes.

**Check if DNS is working:**
```bash
# From your local computer, run:
ping flipunit.eu
```

Or use an online tool like https://dnschecker.org/

✅ **Success check**: After DNS propagates, `https://flipunit.eu` should work!

---

## Step 15: Set Up Auto-Restart (Optional but Recommended)

This ensures your application automatically starts if the server reboots:

### 15.1 Create Systemd Service

```bash
sudo nano /etc/systemd/system/flipunit.service
```

Add this content:

```ini
[Unit]
Description=FlipUnit Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/flipunit
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Save the file (Ctrl+O, Enter, Ctrl+X).

### 15.2 Enable the Service

```bash
sudo systemctl enable flipunit.service
```

Now your application will automatically start on server reboot!

---

## Step 16: Final Testing

Test everything is working:

1. ✅ Visit `https://flipunit.eu` - should load with HTTPS padlock
2. ✅ Visit `https://www.flipunit.eu` - should also work
3. ✅ Test a converter (upload an image, try a unit conversion)
4. ✅ Check static files load (CSS, images should work)
5. ✅ Test admin panel: `https://flipunit.eu/admin/` (use your superuser credentials)

---

## Maintenance Commands

Here are useful commands for managing your deployment.

**Deploy from your laptop:** Use `./deploy_to_vps.sh` or `./deploy.sh`. Default target is Hetzner: `root@46.225.75.195`. Override with the first argument (e.g. `./deploy_to_vps.sh root@46.225.75.195`) or `export VPS_HOST=root@46.225.75.195`.

### View Application Logs

```bash
cd /opt/flipunit
docker-compose logs -f web
```
(Press `Ctrl+C` to exit)

### Restart Application

```bash
cd /opt/flipunit
docker-compose restart
```

### Update Application (After Code Changes)

**IMPORTANT**: Templates are mounted as a volume, so template changes are immediate without rebuild!

```bash
cd /opt/flipunit
git pull                    # Get latest code

# For template changes: Just restart (no rebuild needed!)
docker-compose restart web

# For Python code changes: Rebuild required
docker-compose build web
docker-compose restart web
```

**Why this works**: The `docker-compose.yml` mounts `./templates:/app/templates` as a volume, so template files on the VPS are immediately available in the container without rebuilding.

### Backup Database

```bash
cd /opt/flipunit
docker-compose exec postgres pg_dump -U flipunit_user flipunit > backup_$(date +%Y%m%d).sql
```

### Stop Application

```bash
cd /opt/flipunit
docker-compose down
```

### Start Application

```bash
cd /opt/flipunit
docker-compose up -d
```

### Check Container Status

```bash
docker-compose ps
```

---

## Troubleshooting

### Containers Won't Start

**Check logs:**
```bash
cd /opt/flipunit
docker-compose logs web
docker-compose logs postgres
```

**Common issues:**
- **Port 8000 already in use**: Something else is using the port
  ```bash
  netstat -tulpn | grep 8000
  ```
- **Database connection errors**: Check your `.env` file has correct `DB_PASSWORD`
- **Permission errors**: Check file permissions
  ```bash
  ls -la /opt/flipunit
  ```

### Database Connection Issues

**Check if PostgreSQL is running:**
```bash
docker-compose ps postgres
```

**Test database connection:**
```bash
docker-compose exec web python manage.py dbshell
```

**Reset database (⚠️ WARNING: This deletes all data!):**
```bash
docker-compose down -v
docker-compose up -d
```

### Static Files Not Loading

**Re-collect static files:**
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

**Check Nginx configuration:**
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

**Fix permissions:**
```bash
sudo chown -R www-data:www-data /opt/flipunit/staticfiles
sudo chown -R www-data:www-data /opt/flipunit/media
```

### SSL Certificate Issues

**Check certificate status:**
```bash
certbot certificates
```

**Renew certificate manually:**
```bash
sudo certbot renew
```

**Test auto-renewal:**
```bash
sudo certbot renew --dry-run
```

### Nginx Not Serving Site

**Check Nginx status:**
```bash
sudo systemctl status nginx
```

**Check Nginx configuration:**
```bash
sudo nginx -t
```

**View Nginx error logs:**
```bash
sudo tail -f /var/log/nginx/error.log
```

**Test if application is accessible:**
```bash
curl http://localhost:8000
```

### Can't Access Website

1. **Check DNS is pointing correctly:**
   ```bash
   # From your local computer
   ping flipunit.eu
   nslookup flipunit.eu
   ```

2. **Check firewall:**
   ```bash
   ufw status
   ```

3. **Check if containers are running:**
   ```bash
   docker-compose ps
   ```

4. **Check Nginx is running:**
   ```bash
   sudo systemctl status nginx
   ```

### Container Keeps Restarting

**Check logs for errors:**
```bash
docker-compose logs web
```

**Common causes:**
- Missing environment variables in `.env` file
- Database connection issues
- Port conflicts
- Application errors (check Django logs)

---

## Security Best Practices

1. **Keep your server updated:**
   ```bash
   apt-get update && apt-get upgrade -y
   ```

2. **Use strong passwords** for:
   - Your VPS root/user account
   - Database password (in `.env`)
   - Django secret key

3. **Never commit `.env` file** to Git

4. **Regular backups:**
   - Set up automated database backups
   - Backup your `/opt/flipunit` directory

5. **Monitor logs** regularly for suspicious activity

6. **Keep Docker images updated:**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

---

## Next Steps

Congratulations! Your application should now be live at `https://flipunit.eu`.

**Recommended next steps:**
1. Set up automated backups (database + files)
2. Monitor server resources (CPU, RAM, disk space)
3. Set up monitoring/alerting (optional)
4. Configure email notifications for errors (optional)
5. Review and optimize performance as needed

**Need help?** Check the logs first, then consult Hetzner or Django/Docker documentation.

---

## Migration from Zone.ee: Phase 2 Backup

When moving to a new server (e.g. Hetzner), run backups on the **current** VPS first. (Production is now on Hetzner 46.225.75.195; the commands below use the **previous** Zone.ee server 217.146.78.140 only when pulling backups from it.)

**Option A – Run the backup script on the source VPS**

1. From your Mac, push the repo (so the source server can pull), then SSH to that server and run (use Zone.ee `ubuntu@217.146.78.140` only if backing up from the old server):
   ```bash
   ssh ubuntu@217.146.78.140
   cd /opt/flipunit && git pull origin main
   bash backup_zoneee_for_migration.sh
   ```
2. Note the backup filenames printed (e.g. `backup_db_20260204_1234.sql`, `backup_media_20260204.tar.gz`).
3. From your Mac, copy the files and secrets (replace filenames with what was printed):
   ```bash
   scp ubuntu@217.146.78.140:/opt/flipunit/backup_db_*.sql .
   scp ubuntu@217.146.78.140:/opt/flipunit/backup_media_*.tar.gz .
   scp ubuntu@217.146.78.140:/opt/flipunit/.env ./env.backup
   scp ubuntu@217.146.78.140:/etc/nginx/sites-available/flipunit.eu ./nginx_flipunit.eu.conf
   ```
   Do not commit `.env` or `env.backup`.

**Option B – Run commands manually on Zone.ee**

1. SSH: `ssh ubuntu@217.146.78.140`, then `cd /opt/flipunit`.
2. Database: `docker-compose exec -T postgres pg_dump -U flipunit_user flipunit > backup_db_$(date +%Y%m%d_%H%M).sql`
3. Media: `tar -czvf backup_media_$(date +%Y%m%d).tar.gz -C /opt/flipunit media staticfiles`
4. From your Mac, copy the backup files, `.env`, and nginx config as in Option A step 3.

Use the backup SQL and `.env` (with `ALLOWED_HOSTS` updated to include the new server IP) when deploying on the new server (Phase 3).

---

## Migration from Zone.ee: Phase 3 Deploy on Hetzner

Do this after Phase 2 backups are on your Mac and the Hetzner server has Docker, Nginx, and Certbot installed (see main guide).

**Hetzner server IP used below:** `46.225.75.195` — replace with yours if different.

### Step 1: On the Hetzner server – create directory and clone repo

```bash
ssh root@46.225.75.195
mkdir -p /opt/flipunit && cd /opt/flipunit
git clone https://github.com/TarmoKouhkna/Flipunit.git .
```

### Step 2: From your Mac – copy backup files and .env to Hetzner

From `~/Documents/Flipunit` (where you have the backup files):

```bash
scp backup_db_20260204_0850.sql root@46.225.75.195:/opt/flipunit/
scp backup_media_20260204.tar.gz root@46.225.75.195:/opt/flipunit/
scp env.backup root@46.225.75.195:/opt/flipunit/.env
scp nginx_flipunit.eu.conf root@46.225.75.195:/tmp/flipunit.eu
```

(Use your actual backup filenames if different.)

### Step 3: On the Hetzner server – add Hetzner IP to ALLOWED_HOSTS

```bash
ssh root@46.225.75.195
nano /opt/flipunit/.env
```

Ensure a line like this exists (add or edit; use your Hetzner IP):

```env
ALLOWED_HOSTS=flipunit.eu,www.flipunit.eu,46.225.75.195
```

Save (Ctrl+O, Enter, Ctrl+X).

### Step 4: On the Hetzner server – restore DB, media, and start app

```bash
cd /opt/flipunit
bash deploy_phase3_hetzner.sh backup_db_20260204_0850.sql
```

(Use your actual backup SQL filename if different.) This starts Postgres, restores the database, extracts media/static, and runs `docker compose build && docker compose up -d`.

### Step 5: On the Hetzner server – configure Nginx

```bash
sudo mv /tmp/flipunit.eu /etc/nginx/sites-available/flipunit.eu
sudo ln -sf /etc/nginx/sites-available/flipunit.eu /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Step 6: Verify

- From the server: `curl -H "Host: flipunit.eu" http://localhost:8000/` should return 200.
- From your Mac (before DNS switch): `curl -H "Host: flipunit.eu" http://46.225.75.195/` should return 200.

### Step 7: SSL (after Phase 4 DNS switch)

Once DNS for flipunit.eu points to the Hetzner IP:

```bash
ssh root@46.225.75.195
sudo certbot --nginx -d flipunit.eu -d www.flipunit.eu
```

Phase 4 is to point the domain’s A records at the Hetzner IP in your DNS panel (e.g. Zone.ee).

---

## Quick Reference: Important Paths

- Application directory: `/opt/flipunit`
- Docker compose file: `/opt/flipunit/docker-compose.yml`
- Environment variables: `/opt/flipunit/.env`
- Nginx config: `/etc/nginx/sites-available/flipunit.eu`
- Nginx logs: `/var/log/nginx/error.log`
- Application logs: `docker-compose logs web` (from `/opt/flipunit`)
