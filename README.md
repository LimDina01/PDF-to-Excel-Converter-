# Ubuntu Server Deployment Guide

This guide covers everything your IT administrator needs to deploy the Bank Statement Converter application to a production Ubuntu Server.

## 1. Prepare the Server
Update the server and install the required system packages, including Python 3, Nginx (web server), and Supervisor (process manager).

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev nginx supervisor
```

## 2. Transfer the Code
Copy the entire `web-converter` project folder to the server. The standard location for web applications is `/var/www/`.

```bash
# Example showing ownership setup
sudo cp -r /path/to/your/web-converter /var/www/web-converter
sudo chown -R $USER:$USER /var/www/web-converter
cd /var/www/web-converter
```

## 3. Set up the Python Environment
Create an isolated virtual environment and install all required dependencies (Django, Pandas, PDF tools, LDAP, and Gunicorn).

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

## 4. Configure Django for Production
Before starting the server, you need to adjust a few Django settings:

1. Open `core/settings.py`.
2. Change `DEBUG = True` to `DEBUG = False`.
3. Update `ALLOWED_HOSTS = []` to include your server's IP or Domain Name (e.g., `ALLOWED_HOSTS = ['192.168.1.100', 'converter.yourdomain.local']`).
4. **Enable LDAP:** Scroll to the bottom and uncomment line 140: `"django_python3_ldap.auth.LDAPBackend"`.
5. Run the production prep commands:

```bash
# Create the database tables
python manage.py migrate

# Collect all CSS/JS files into the staticfiles folder
python manage.py collectstatic --noinput
```

## 5. Configure Supervisor (Gunicorn)
We use Supervisor to ensure Gunicorn (the Python app server) runs automatically on startup and restarts if it crashes.

1. Create a configuration file: `sudo nano /etc/supervisor/conf.d/web-converter.conf`
2. Paste the following (adjust paths if you put the folder elsewhere):

```ini
[program:web-converter]
command=/var/www/web-converter/venv/bin/gunicorn core.wsgi:application --bind 127.0.0.1:8000 --workers 3
directory=/var/www/web-converter
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/web-converter.err.log
stdout_logfile=/var/log/web-converter.out.log
```

3. Start the Supervisor task:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start web-converter
```

## 6. Configure Nginx (Web Server)
Nginx will accept traffic on Port 80 and forward it to Gunicorn. It will also serve your static CSS/JS files quickly.

1. Create a new Nginx config: `sudo nano /etc/nginx/sites-available/web-converter`
2. Paste the following configuration (replace `YOUR_SERVER_IP`):

```nginx
server {
    listen 80;
    server_name YOUR_SERVER_IP; # e.g. 192.168.1.100 or a local domain

    location = /favicon.ico { access_log off; log_not_found off; }
    
    # Serve CSS and JS
    location /static/ {
        root /var/www/web-converter;
    }

    # Serve the main app by proxying to Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

3. Enable the configuration and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/web-converter /etc/nginx/sites-enabled
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

## 7. You're Done!
Open your web browser and navigate to the Ubuntu Server's IP address. You should see the sleek Active Directory login page!
