# Diet Pi Installation Guide

This guide provides step-by-step instructions for running SolarApp on Raspberry Pi with Diet Pi OS, using nginx to serve the frontend.

## ⚠️ Important: API Configuration

**Before building the frontend**, ensure you do not set `VITE_API_URL` to a hardcoded IP address. 

- ✅ **Correct**: Leave `VITE_API_URL` empty (default) - nginx will proxy `/api` requests
- ❌ **Wrong**: Setting `VITE_API_URL=http://192.168.x.x` - causes 502 errors when IP changes

See [TROUBLESHOOTING_502.md](TROUBLESHOOTING_502.md) if you encounter API connection errors.

For detailed build configuration, see [frontend/BUILD.md](frontend/BUILD.md).

## What is Diet Pi?

Diet Pi is an extremely lightweight Debian-based operating system optimized for Raspberry Pi and other single-board computers. It's perfect for SolarApp because:
- **Minimal footprint**: Uses ~50MB less RAM than standard Raspberry Pi OS
- **Optimized for headless operation**: No GUI overhead
- **Simple software installation**: Built-in software manager (`dietpi-software`)
- **Performance focused**: Optimized defaults for resource-constrained devices

## Prerequisites

- Raspberry Pi (Pi 3 B+, Pi 4, or Pi Zero 2 W)
- MicroSD card (8GB minimum, 16GB+ recommended, Class 10 or better)
- Diet Pi OS installed (download from https://dietpi.com/)
- Network connection (Ethernet recommended for initial setup)
- SSH access to your Raspberry Pi

## Installation Methods

Diet Pi supports two installation methods for SolarApp:

1. **Docker Installation** - Easiest, recommended for Pi 4
2. **Native Installation with nginx** - Best performance, recommended for Diet Pi

---

## Method 1: Docker Installation on Diet Pi

### Step 1: Install Docker using dietpi-software

```bash
# Launch Diet Pi software installer
sudo dietpi-software

# In the menu:
# - Go to "Search Software"
# - Search for "Docker"
# - Select: Docker (ID 162) and Docker Compose (ID 134)
# - Choose "Install"
```

Or install directly from command line:

```bash
# Install Docker and Docker Compose
sudo dietpi-software install 162 134

# Verify installation
docker --version
docker-compose --version
```

### Step 2: Clone and Deploy SolarApp

```bash
# Navigate to home directory
cd /home/dietpi

# Clone the repository
git clone https://github.com/catar13274/SolarApp.git
cd SolarApp

# Use the Raspberry Pi optimized Docker Compose configuration
docker-compose -f docker-compose.rpi.yml up -d

# View logs
docker-compose -f docker-compose.rpi.yml logs -f
```

### Step 3: Access the Application

```bash
# Find your Pi's IP address
hostname -I

# Access from browser on another device:
# Frontend: http://YOUR_PI_IP:3000
# API Docs: http://YOUR_PI_IP:8000/docs
```

**Resource Usage (Docker on Diet Pi):**
- Backend: ~128-256MB RAM
- XML Parser: ~64-128MB RAM
- Frontend (nginx): ~32-64MB RAM
- **Total: ~250-450MB RAM**

---

## Method 2: Native Installation with nginx (Recommended)

This method provides the best performance on Diet Pi and uses the least resources.

**Note**: For fully automated installation, see the [Quick Setup Script](#quick-setup-script) section below which uses `dietpi-install.sh`. The steps below are for manual installation if you want more control over the process.

### Step 1: Install Prerequisites

```bash
# Update Diet Pi
sudo dietpi-update

# Install required software using dietpi-software
sudo dietpi-software install 130  # Python 3
sudo dietpi-software install 83   # Node.js (if building frontend locally)
sudo dietpi-software install 85   # nginx
sudo dietpi-software install 17   # Git

# Or install directly with apt
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx git
```

### Step 2: Install SolarApp

```bash
# Clone the repository
cd /home/dietpi
git clone https://github.com/catar13274/SolarApp.git
cd SolarApp

# Run the installation script
chmod +x install.sh
sudo ./install.sh
```

The install script will:
- Set up Python virtual environments
- Install backend and XML parser dependencies
- Build the frontend (if Node.js is available)
- Create systemd services

### Step 3: Configure nginx for Frontend

Create a Diet Pi-optimized nginx configuration:

```bash
# Create nginx site configuration
sudo nano /etc/nginx/sites-available/solarapp
```

Add the following configuration:

```nginx
# SolarApp Frontend - Optimized for Diet Pi
server {
    listen 80;
    server_name _;
    
    root /home/dietpi/SolarApp/frontend/dist;
    index index.html;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Main location - serve React app
    location / {
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Proxy API requests to backend
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # API docs
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

Enable the site:

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/solarapp /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### Step 4: Optimize nginx for Diet Pi

Edit the main nginx configuration:

```bash
sudo nano /etc/nginx/nginx.conf
```

Optimize these settings for Diet Pi:

```nginx
# Reduce worker processes for single-core or low-resource systems
worker_processes 1;

# Lower worker connections for limited resources
events {
    worker_connections 256;
    use epoll;
}

http {
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/atom+xml image/svg+xml;
    
    # Reduce buffer sizes for lower memory usage
    client_body_buffer_size 10K;
    client_header_buffer_size 1k;
    client_max_body_size 8m;
    large_client_header_buffers 2 1k;
    
    # Timeouts
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # Cache
    open_file_cache max=1000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
    
    # Disable access log for better performance (enable for debugging)
    # access_log off;
    access_log /var/log/nginx/access.log combined buffer=32k;
    error_log /var/log/nginx/error.log warn;
}
```

Restart nginx:

```bash
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Step 5: Set up Systemd Services

Use the Diet Pi/Raspberry Pi optimized services:

```bash
# Copy optimized service files
sudo cp /home/dietpi/SolarApp/systemd/solarapp-backend-rpi.service /etc/systemd/system/
sudo cp /home/dietpi/SolarApp/systemd/solarapp-xml-parser-rpi.service /etc/systemd/system/

# Edit the service files to set correct user
sudo sed -i 's/User=pi/User=dietpi/g' /etc/systemd/system/solarapp-backend-rpi.service
sudo sed -i 's/User=pi/User=dietpi/g' /etc/systemd/system/solarapp-xml-parser-rpi.service

# Update paths if needed (if installed in different location)
# sudo nano /etc/systemd/system/solarapp-backend-rpi.service
# sudo nano /etc/systemd/system/solarapp-xml-parser-rpi.service

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable solarapp-backend-rpi solarapp-xml-parser-rpi nginx
sudo systemctl start solarapp-backend-rpi solarapp-xml-parser-rpi

# Check status
systemctl status solarapp-backend-rpi
systemctl status solarapp-xml-parser-rpi
systemctl status nginx
```

### Step 6: Build Frontend (If Node.js Available)

If you installed Node.js:

```bash
cd /home/dietpi/SolarApp/frontend

# Install dependencies
npm install

# Build for production
npm run build

# The build output will be in frontend/dist/
# nginx is already configured to serve from this directory
```

If Node.js is not available, you can build on another machine and copy the dist folder:

```bash
# On development machine:
cd frontend
npm install
npm run build

# Copy dist folder to Raspberry Pi:
scp -r dist/ dietpi@YOUR_PI_IP:/home/dietpi/SolarApp/frontend/
```

### Step 7: Validate Installation

After installation completes, verify everything is configured correctly:

```bash
cd /home/dietpi/SolarApp

# Run the validation script
chmod +x validate-dietpi.sh
./validate-dietpi.sh
```

The validation script will check:
- ✓ Python and nginx installation
- ✓ Virtual environments
- ✓ nginx configuration validity
- ✓ Systemd services
- ✓ Port availability
- ✓ Frontend build
- ✓ File permissions

If all checks pass, you'll see:
```
✓ All checks passed!
Access your application:
  Frontend:  http://YOUR_PI_IP/
  API Docs:  http://YOUR_PI_IP/docs
```

### Step 8: Access the Application

```bash
# Find your Pi's IP address
hostname -I

# Access from browser:
# Frontend: http://YOUR_PI_IP/
# API Docs: http://YOUR_PI_IP/docs
# API: http://YOUR_PI_IP/api
```

**Resource Usage (Native on Diet Pi):**
- nginx: ~10-20MB RAM
- Backend: ~80-150MB RAM
- XML Parser: ~40-80MB RAM
- **Total: ~130-250MB RAM**

---

## Diet Pi Optimizations

### 1. Diet Pi Configuration Tool

Optimize your Diet Pi installation:

```bash
sudo dietpi-config
```

Recommended settings:
- **Performance Options** → CPU Governor: `performance` or `ondemand`
- **Advanced Options** → Memory Split: Allocate minimal to GPU (16MB for headless)
- **Advanced Options** → Reduce serial console logging

### 2. Reduce Memory Usage

Edit Diet Pi configuration:

```bash
sudo nano /boot/dietpi.txt
```

Optimize these settings:

```
# Reduce memory logging
AUTO_SETUP_LOGGING_CLEAR=1

# Disable unnecessary services
AUTO_SETUP_AUTOMATED=1
AUTO_SETUP_GLOBAL_PASSWORD=your-password
```

### 3. Enable Log Rotation for nginx

```bash
# nginx logs are already rotated by default on Diet Pi
# Verify configuration:
cat /etc/logrotate.d/nginx
```

### 4. Monitor Resources

```bash
# Use Diet Pi's built-in tools
sudo dietpi-services
sudo dietpi-services status

# Or standard Linux tools
htop
free -h
df -h

# Check service logs
journalctl -u solarapp-backend-rpi -f
journalctl -u nginx -f
```

### 5. Automate Database Backups

Create a backup script:

```bash
nano /home/dietpi/backup-solarapp.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/dietpi/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
cp /home/dietpi/SolarApp/backend/data/solarapp.db "$BACKUP_DIR/solarapp_$DATE.db"

# Keep only last 7 days
find $BACKUP_DIR -name "solarapp_*.db" -mtime +7 -delete
```

Make it executable and add to cron:

```bash
chmod +x /home/dietpi/backup-solarapp.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/dietpi/backup-solarapp.sh
```

---

## Quick Setup Script

For fully automated installation on Diet Pi, use the provided `dietpi-install.sh` script:

```bash
# Clone repository
cd /home/dietpi
git clone https://github.com/catar13274/SolarApp.git
cd SolarApp

# Run the automated Diet Pi installer
chmod +x dietpi-install.sh
sudo ./dietpi-install.sh
```

The `dietpi-install.sh` script will:
- Install prerequisites (Python, nginx, Git)
- Set up backend and XML parser with virtual environments
- Build the frontend (if Node.js available)
- Configure nginx with reverse proxy
- Create and start systemd services
- Validate the installation

Access your application at `http://YOUR_PI_IP/` after installation completes.

**Note**: This is the recommended installation method for Diet Pi as it handles all configuration automatically.

---

---

## Troubleshooting

### nginx Won't Start

```bash
# Check configuration
sudo nginx -t

# Check logs
sudo journalctl -u nginx -n 50

# Verify port 80 is not in use
sudo netstat -tlnp | grep :80
```

### Frontend Not Loading

```bash
# Check if dist folder exists
ls -la /home/dietpi/SolarApp/frontend/dist/

# Check nginx configuration
cat /etc/nginx/sites-enabled/solarapp

# Check nginx error log
sudo tail -f /var/log/nginx/error.log
```

### Backend Not Responding

```bash
# Check backend service
systemctl status solarapp-backend-rpi

# Check logs
journalctl -u solarapp-backend-rpi -n 50

# Verify backend is listening
sudo netstat -tlnp | grep :8000
```

### High Memory Usage

```bash
# Check memory usage
free -h

# Check top processes
htop

# Restart services to clear memory
sudo systemctl restart solarapp-backend-rpi solarapp-xml-parser-rpi nginx
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R dietpi:dietpi /home/dietpi/SolarApp

# Fix permissions for scripts
chmod +x /home/dietpi/SolarApp/install.sh
chmod +x /home/dietpi/SolarApp/dietpi-install.sh
```

---

## Performance Benchmarks on Diet Pi

### Raspberry Pi 4 (4GB) with Diet Pi
- **Boot time**: ~20-30 seconds (vs 40-60s on standard Raspberry Pi OS)
- **Idle RAM usage**: ~80-100MB (vs 150-200MB on standard Raspberry Pi OS)
- **SolarApp RAM usage**: ~130-250MB
- **Total RAM usage**: ~210-350MB
- **Available for apps**: ~3.6GB+ on 4GB model
- **API response time**: 15-40ms (local)
- **Dashboard load time**: 1-2 seconds

### Raspberry Pi 3 B+ (1GB) with Diet Pi
- **Boot time**: ~25-35 seconds
- **Idle RAM usage**: ~70-90MB
- **SolarApp RAM usage**: ~150-250MB
- **Total RAM usage**: ~220-340MB
- **Available for apps**: ~600-700MB
- **API response time**: 30-80ms (local)
- **Dashboard load time**: 2-3 seconds

---

## Updating SolarApp

### Automated Update (Recommended)

For quick and safe updates, use the automated update script:

```bash
cd /home/dietpi/SolarApp

# Run the automated update script
sudo ./dietpi-update.sh
```

The `dietpi-update.sh` script will:
- Stop services before updating
- Create automatic database backup
- Pull latest changes from git
- Update backend and XML parser dependencies
- Rebuild frontend (if Node.js available)
- Run database migrations (if any)
- Restart all services

### Manual Update

To update SolarApp manually:

```bash
cd /home/dietpi/SolarApp

# Stop services
sudo systemctl stop solarapp-backend-rpi solarapp-xml-parser-rpi

# Backup database
cp backend/data/solarapp.db backend/data/solarapp.db.backup

# Pull latest changes
git pull

# Update backend dependencies
cd backend
source .venv/bin/activate
pip install -r requirements.txt
deactivate

# Update XML parser dependencies
cd services/xml_parser
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../../..

# Rebuild frontend (if Node.js available)
cd frontend
npm install
npm run build
cd ..

# Restart services
sudo systemctl start solarapp-backend-rpi solarapp-xml-parser-rpi
```

---

## Uninstalling

### Automated Uninstallation (Recommended)

For safe and complete removal, use the automated uninstall script:

```bash
cd /home/dietpi/SolarApp

# Run the automated uninstall script
sudo ./dietpi-uninstall.sh
```

The `dietpi-uninstall.sh` script will:
- Stop and disable all SolarApp services
- Remove systemd service files
- Remove nginx configuration
- Optionally create a database backup
- Remove application files (with confirmation)
- Provide guidance on removing system packages

The script will ask for confirmation before removing components and offers options to keep backups.

### Manual Uninstallation

To completely remove SolarApp manually:

```bash
# Stop and disable services
sudo systemctl stop solarapp-backend-rpi solarapp-xml-parser-rpi
sudo systemctl disable solarapp-backend-rpi solarapp-xml-parser-rpi

# Remove service files
sudo rm /etc/systemd/system/solarapp-backend-rpi.service
sudo rm /etc/systemd/system/solarapp-xml-parser-rpi.service
sudo systemctl daemon-reload

# Remove nginx configuration
sudo rm /etc/nginx/sites-enabled/solarapp
sudo rm /etc/nginx/sites-available/solarapp
sudo systemctl restart nginx

# Remove application files
rm -rf /home/dietpi/SolarApp

# Remove backups (optional)
rm -rf /home/dietpi/backups
```

---

## Additional Resources

- [Diet Pi Official Documentation](https://dietpi.com/docs/)
- [Diet Pi Software List](https://dietpi.com/docs/software/)
- [nginx Optimization Guide](https://nginx.org/en/docs/)
- [SolarApp Raspberry Pi Guide](RASPBERRY_PI.md)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

## Support

For Diet Pi specific issues:
1. Check Diet Pi logs: `sudo dietpi-services logs`
2. Review this guide's troubleshooting section
3. Check SolarApp logs: `journalctl -u solarapp-backend-rpi -f`
4. Visit [Diet Pi Forums](https://dietpi.com/forum/)
5. Open an issue on GitHub with:
   - Diet Pi version: `dietpi-software list`
   - Error logs
   - Output of `free -h` and `df -h`

---

**Optimized for Diet Pi with ❤️**
