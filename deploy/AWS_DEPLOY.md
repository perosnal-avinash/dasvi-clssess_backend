# AWS Ubuntu Server Deployment Guide
## Stack: Django + Gunicorn + Nginx + PostgreSQL

---

## STEP 1 — Launch EC2 Instance (AWS Console)

1. Go to **EC2 → Launch Instance**
2. Choose **Ubuntu Server 22.04 LTS**
3. Instance type: **t2.micro** (free tier) or **t3.small** for production
4. Create or select a **Key Pair** (.pem file) — save it safely
5. Security Group — open these ports:
   - **22** (SSH)
   - **80** (HTTP)
   - **443** (HTTPS)
6. Launch the instance
7. Note the **Public IP** from the EC2 dashboard

---

## STEP 2 — Connect to Server

```bash
# On your local machine
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_PUBLIC_IP
```

---

## STEP 3 — Server Setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv python3-dev \
    nginx postgresql postgresql-contrib \
    libpq-dev git curl
```

---

## STEP 4 — PostgreSQL Setup

```bash
sudo -u postgres psql

# Inside psql:
CREATE DATABASE dasvi_classes;
CREATE USER dasvi_user WITH PASSWORD 'your_strong_password';
ALTER ROLE dasvi_user SET client_encoding TO 'utf8';
ALTER ROLE dasvi_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE dasvi_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE dasvi_classes TO dasvi_user;
\q
```

---

## STEP 5 — Clone Project

```bash
cd /home/ubuntu
git clone https://github.com/perosnal-avinash/dasvi-clssess_backend.git backend
cd backend
```

---

## STEP 6 — Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## STEP 7 — Create .env File

```bash
nano /home/ubuntu/backend/.env
```

Paste this (replace all values):

```env
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=YOUR_PUBLIC_IP,yourdomain.com

# Database
DB_NAME=dasvi_classes
DB_USER=dasvi_user
DB_PASSWORD=your_strong_password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
ADMIN_EMAIL=admin@dasviclasses.com

# CORS — add your frontend domain
CORS_ALLOWED_ORIGINS=http://YOUR_PUBLIC_IP,https://yourdomain.com

# Referral
REFERRAL_ENABLED=true
REFERRAL_REWARD_AMOUNT=25
```

> Generate a secret key:
> ```bash
> python3 -c "import secrets; print(secrets.token_urlsafe(50))"
> ```

---

## STEP 8 — Django Setup

```bash
source venv/bin/activate

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

---

## STEP 9 — Gunicorn Setup

```bash
# Create log directory
sudo mkdir -p /var/log/gunicorn
sudo chown ubuntu:ubuntu /var/log/gunicorn

# Copy service file
sudo cp /home/ubuntu/backend/deploy/gunicorn.service /etc/systemd/system/gunicorn.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# Check status
sudo systemctl status gunicorn
```

---

## STEP 10 — Nginx Setup

```bash
# Copy nginx config
sudo cp /home/ubuntu/backend/deploy/nginx.conf /etc/nginx/sites-available/dasvi

# Edit and replace YOUR_DOMAIN_OR_IP with your actual IP or domain
sudo nano /etc/nginx/sites-available/dasvi

# Enable the site
sudo ln -s /etc/nginx/sites-available/dasvi /etc/nginx/sites-enabled/

# Remove default nginx site
sudo rm /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## STEP 11 — Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

---

## STEP 12 — Test

Open browser: `http://YOUR_PUBLIC_IP/swagger/`

---

## STEP 13 — Free SSL with Let's Encrypt (if you have a domain)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
sudo systemctl reload nginx
```

---

## Useful Commands

```bash
# Restart after code changes
cd /home/ubuntu/backend
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn

# View logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/gunicorn/error.log
sudo tail -f /var/log/nginx/error.log

# Check service status
sudo systemctl status gunicorn
sudo systemctl status nginx
```

---

## API Endpoints (after deploy)

| URL | Description |
|-----|-------------|
| `http://IP/swagger/` | Swagger API docs |
| `http://IP/api/v1/auth/register/` | Register |
| `http://IP/api/v1/auth/login/` | Login |
| `http://IP/api/v1/referral/details/` | Referral details |
| `http://IP/admin/` | Django admin |
