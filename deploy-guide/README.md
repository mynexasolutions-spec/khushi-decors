# Deploy Flask App to AWS EC2 — Git-Based Deployment

> **Server**: `ec2-13-200-255-139.ap-south-1.compute.amazonaws.com`  
> **SSH User**: `ec2-user`  
> **PEM Key**: `nexa-solutions.pem` (included in this folder)

---

## Port Allocation (existing apps)

| Port | App |
|------|-----|
| 8000 | luvtaleofficial.com |
| 8001 | curvesportsnutrition.com |
| 8002 | evnationsre.com |
| 8003 | twoindia.in |
| 8004 | talbeenaa.com / htwoindia.in / htwo.store |
| **8005** | **← Use this for new app** |

---

## Step 1 — Push Your Code to GitHub First

Create a **private GitHub repo** and push your Flask project:

```bash
cd your-project
git init
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:your-username/your-repo.git
git push -u origin main
```

Your repo should have:

```
your-project/
├── app/              # (optional) Flask package folder
├── static/           # CSS, JS, images
├── templates/        # Jinja2 templates
├── wsgi.py           # Entry point: `app = Flask(__name__)`
├── requirements.txt  # Python dependencies
├── .gitignore        # Must include .env, venv/, __pycache__
└── deploy-guide/     # (optional — can delete after reading)
```

> **IMPORTANT**: Do NOT commit `.env` or `venv/` — add them to `.gitignore`.

---

## Step 2 — Generate & Add an SSH Deploy Key

This lets the server pull code from GitHub without a password.

### On your laptop, generate a new deploy key:

```bash
ssh-keygen -t ed25519 -C "deploy-<your-project-name>" -f ~/.ssh/deploy-<your-project-name>
cat ~/.ssh/deploy-<your-project-name>.pub
```

Copy the output (starts with `ssh-ed25519 AAA...`).

### Add the public key to GitHub:

1. Go to your repo on GitHub → **Settings** → **Deploy Keys** → **Add deploy key**
2. Paste the public key, check **Allow write access**, save

---

## Step 3 — One-Time Server Setup

SSH into the server:

```bash
ssh -i deploy-guide/nexa-solutions.pem ec2-user@ec2-13-200-255-139.ap-south-1.compute.amazonaws.com
```

### 3a — Add the private deploy key to the server

Create the SSH key file on the server:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
nano ~/.ssh/deploy-<your-project-name>
```

Paste the **private key** content (from `~/.ssh/deploy-<your-project-name>` on your laptop), save, then:

```bash
chmod 600 ~/.ssh/deploy-<your-project-name>
```

Create `~/.ssh/config` (or edit it):

```
nano ~/.ssh/config
```

Add this entry:

```
Host github.com
    HostName github.com
    IdentityFile ~/.ssh/deploy-<your-project-name>
```

Then:

```bash
# Test the connection
ssh -T git@github.com
# Should say: "Hi username/your-repo! You've successfully authenticated..."
```

### 3b — Clone the repo & set up venv

```bash
cd /home/ec2-user
git clone git@github.com:your-username/your-repo.git <your-project-name>
cd <your-project-name>

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
nano .env
```

Paste your environment variables:

```
DATABASE_URL=postgresql://...
CLOUDINARY_URL=cloudinary://...
SECRET_KEY=your-secret-key
FLASK_ENV=production
```

Save and exit.

---

## Step 4 — systemd Service File

On the server, create `/etc/systemd/system/<your-project-name>.service`:

```bash
sudo nano /etc/systemd/system/<your-project-name>.service
```

Paste:

```ini
[Unit]
Description=Your Flask App
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/<your-project-name>
Environment="PATH=/home/ec2-user/<your-project-name>/venv/bin"
EnvironmentFile=/home/ec2-user/<your-project-name>/.env
ExecStart=/home/ec2-user/<your-project-name>/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8005 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable <your-project-name>
sudo systemctl start <your-project-name>
sudo systemctl status <your-project-name>
```

---

## Step 5 — Nginx Config File

On the server, create `/etc/nginx/conf.d/<your-project-name>.conf`:

```bash
sudo nano /etc/nginx/conf.d/<your-project-name>.conf
```

Paste:

```nginx
server {
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 20M;

    location /static/ {
        alias /home/ec2-user/<your-project-name>/static/;
        expires 30d;
        access_log off;
    }

    location / {
        proxy_pass http://127.0.0.1:8005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

# HTTP → HTTPS redirect
server {
    if ($host = www.yourdomain.com) { return 301 https://$host$request_uri; }
    if ($host = yourdomain.com) { return 301 https://$host$request_uri; }
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 404;
}
```

Test and reload:

```bash
sudo nginx -t
sudo nginx -s reload
```

---

## Step 6 — SSL Certificate (Certbot)

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## Step 7 — DNS

Point your domain's **A record** to the EC2 IP: **`13.200.255.139`**

---

## Step 8 — Daily Deploy (Updating Code)

Whenever you push new code to GitHub, deploy with one command:

```bash
# SSH into server and run:
ssh -i deploy-guide/nexa-solutions.pem ec2-user@ec2-13-200-255-139.ap-south-1.compute.amazonaws.com

cd /home/ec2-user/<your-project-name>
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # only needed if deps changed
sudo systemctl restart <your-project-name>
```

### Or use this deploy script (`deploy.sh`):

```bash
#!/bin/bash
set -e

SERVER="ec2-user@ec2-13-200-255-139.ap-south-1.compute.amazonaws.com"
PEM="deploy-guide/nexa-solutions.pem"
REMOTE_DIR="/home/ec2-user/<your-project-name>"
SERVICE="<your-project-name>"

echo "==> Pulling latest code on server..."
ssh -i "$PEM" "$SERVER" \
  "cd $REMOTE_DIR && \
   git pull origin main && \
   source venv/bin/activate && \
   pip install -r requirements.txt && \
   sudo systemctl restart $SERVICE && \
   sleep 3 && \
   sudo systemctl is-active $SERVICE"

echo "✅ Deployed!"
```

Make it executable: `chmod +x deploy.sh`, then run: `./deploy.sh`

---

## Deploy Checklist

- [ ] Project pushed to GitHub
- [ ] Deploy key added to GitHub repo settings
- [ ] Server can authenticate with GitHub (`ssh -T git@github.com` works)
- [ ] `wsgi.py` exports `app` Flask instance
- [ ] `requirements.txt` includes `flask`, `gunicorn`, `psycopg2-binary`, `python-dotenv`, `cloudinary`
- [ ] `.env` created on server (NOT committed to git)
- [ ] `.gitignore` has `.env`, `venv/`, `__pycache__/`, `*.pyc`
- [ ] Domain A record pointed to `13.200.255.139`
- [ ] Port `8005` is free (`sudo ss -tlnp | grep 8005`)
- [ ] systemd service is running (`sudo systemctl status <project-name>`)
- [ ] Nginx config is valid (`sudo nginx -t`)

---

## Useful Server Commands

```bash
# View live app logs
sudo journalctl -u <your-project-name> -f

# Restart app
sudo systemctl restart <your-project-name>

# Check status
sudo systemctl status <your-project-name>

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo nginx -s reload

# Check which ports are in use
sudo ss -tlnp

# Test GitHub auth
ssh -T git@github.com
```
