# Quick Start: Diet Pi Deployment with nginx

This is a quick reference for deploying SolarApp on Raspberry Pi with Diet Pi OS. For complete details, see [DIETPI.md](DIETPI.md).

## ⚠️ Important Note

If you encounter "502 Bad Gateway" or API connection errors, see [TROUBLESHOOTING_502.md](TROUBLESHOOTING_502.md). The most common cause is building the frontend with a hardcoded IP address in `VITE_API_URL`.

## What You Get

- ✅ **Frontend**: Built React app served by nginx (port 80)
- ✅ **Backend API**: FastAPI service (port 8000, proxied through nginx at /api)
- ✅ **XML Parser**: Invoice processing service (port 5000)
- ✅ **All services**: Auto-start on boot via systemd
- ✅ **Optimized**: Uses ~130-250MB RAM total

## Installation (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/catar13274/SolarApp.git
cd SolarApp

# 2. Run automated installer
chmod +x dietpi-install.sh
sudo ./dietpi-install.sh

# 3. Access application
# Find your Pi's IP: hostname -I
# Open browser: http://YOUR_PI_IP/
```

That's it! The installer handles everything:
- Validates system requirements (disk space, ports, Python version)
- Installs Python 3.8+, nginx, and dependencies
- Builds the frontend
- Configures nginx as reverse proxy
- Sets up systemd services
- Starts all services

### Optional: Custom Port Configuration

If you need to use different ports (e.g., port 8000 already in use):

```bash
# Set custom ports before installation
export BACKEND_PORT=8080      # Default: 8000
export XML_PARSER_PORT=5001   # Default: 5000
export NGINX_PORT=8080        # Default: 80

# Run installer with environment variables preserved
sudo -E ./dietpi-install.sh
```

## What Gets Installed

### nginx Configuration
- **Location**: `/etc/nginx/sites-available/solarapp`
- **Frontend files**: `/home/dietpi/SolarApp/frontend/dist`
- **Proxy rules**: 
  - `/` → Frontend (React SPA)
  - `/api` → Backend (FastAPI on port 8000)
  - `/docs`, `/redoc` → API documentation

### Systemd Services
- **solarapp-backend.service**: FastAPI backend (1 worker, 50 concurrent connections)
- **solarapp-xml-parser.service**: XML invoice parser
- **nginx.service**: Web server (1 worker process)

### Directory Structure
```
/home/dietpi/SolarApp/
├── backend/
│   ├── .venv/              # Python virtual environment
│   ├── app/                # FastAPI application
│   ├── data/               # SQLite database
│   └── services/
│       └── xml_parser/     # XML parsing service
├── frontend/
│   ├── src/                # React source (not needed after build)
│   └── dist/               # Built frontend (served by nginx)
└── systemd/                # Service templates
```

## URLs and Ports

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| Frontend | http://YOUR_PI_IP/ | 80 | React web interface |
| API | http://YOUR_PI_IP/api | 80→8000 | Backend API (proxied) |
| API Docs | http://YOUR_PI_IP/docs | 80→8000 | Swagger UI (proxied) |
| Backend Direct | http://YOUR_PI_IP:8000 | 8000 | Direct backend access |
| XML Parser | http://localhost:5000 | 5000 | Internal only |

## Service Management

```bash
# Check status
sudo systemctl status solarapp-backend
sudo systemctl status solarapp-xml-parser
sudo systemctl status nginx

# View logs
sudo journalctl -u solarapp-backend -f
sudo journalctl -u solarapp-xml-parser -f
sudo journalctl -u nginx -f

# Restart services
sudo systemctl restart solarapp-backend
sudo systemctl restart solarapp-xml-parser
sudo systemctl restart nginx

# Stop services
sudo systemctl stop solarapp-backend
sudo systemctl stop solarapp-xml-parser
sudo systemctl stop nginx

# Enable/disable auto-start
sudo systemctl enable solarapp-backend
sudo systemctl disable solarapp-backend
```

## nginx Management

```bash
# Test configuration
sudo nginx -t

# Reload configuration (without downtime)
sudo nginx -s reload

# View nginx access log
sudo tail -f /var/log/nginx/access.log

# View nginx error log
sudo tail -f /var/log/nginx/error.log

# Edit site configuration
sudo nano /etc/nginx/sites-available/solarapp

# Edit main nginx config
sudo nano /etc/nginx/nginx.conf
```

## Updating the Application

### Automated Update (Recommended)

```bash
cd /home/dietpi/SolarApp
sudo ./dietpi-update.sh
```

The automated script handles everything:
- Stops services
- Backs up database automatically
- Pulls latest changes
- Updates all dependencies
- Rebuilds frontend
- Restarts services

### Manual Update

```bash
cd /home/dietpi/SolarApp

# Stop services
sudo systemctl stop solarapp-backend solarapp-xml-parser

# Backup database
cp backend/data/solarapp.db backend/data/solarapp.db.backup

# Update code
git pull

# Update backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Update XML parser
cd backend/services/xml_parser
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../../..

# Rebuild frontend (if changes)
cd frontend
npm install
npm run build
cd ..

# Restart services
sudo systemctl start solarapp-backend solarapp-xml-parser
sudo systemctl restart nginx
```

## Uninstalling SolarApp

### Automated Uninstall (Recommended)

```bash
cd /home/dietpi/SolarApp
sudo ./dietpi-uninstall.sh
```

The script will:
- Stop and remove all services
- Remove nginx configuration
- Optionally backup database
- Clean up application files
- Ask for confirmation before each step

## Troubleshooting

### 500 Internal Server Error after fresh install

```bash
# This happens when the backend data directory doesn't exist
# The latest version (since Feb 2026) creates it automatically.
# You might encounter this if:
# - You upgraded from an older version
# - The automatic creation somehow failed
# - You manually deleted the data directory

cd /home/dietpi/SolarApp/backend
source .venv/bin/activate
python3 init_db.py --non-interactive
deactivate

# Restart backend
sudo systemctl restart solarapp-backend

# Check if it's running
systemctl status solarapp-backend
curl http://localhost:8000/health
```

### Frontend shows 404 or blank page

```bash
# Check if frontend is built
ls -la /home/dietpi/SolarApp/frontend/dist/

# If missing, build it:
cd /home/dietpi/SolarApp/frontend
npm install
npm run build

# Restart nginx
sudo systemctl restart nginx
```

### API calls fail (network errors)

```bash
# Check backend is running
systemctl status solarapp-backend

# Check backend logs
sudo journalctl -u solarapp-backend -n 50

# Test backend directly
curl http://localhost:8000/docs
```

### nginx fails to start

```bash
# Test configuration
sudo nginx -t

# Check error log
sudo tail -f /var/log/nginx/error.log

# Check if port 80 is available
sudo netstat -tlnp | grep :80

# If another service is using port 80, stop it:
sudo systemctl stop apache2  # if Apache is installed
```

### High memory usage

```bash
# Check memory
free -h

# Check processes
htop

# Restart services to free memory
sudo systemctl restart solarapp-backend solarapp-xml-parser nginx
```

## Resource Usage

| Component | RAM Usage | Notes |
|-----------|-----------|-------|
| nginx | 10-20 MB | Single worker, static files |
| Backend | 80-150 MB | Single worker, optimized for Raspberry Pi |
| XML Parser | 40-80 MB | On-demand processing |
| **Total** | **130-250 MB** | Plenty of room for other services |

## Manual Installation (Alternative)

If you prefer manual installation or the script fails:

1. **Install prerequisites**:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv nginx git nodejs npm
   ```

2. **Follow steps in DIETPI.md** for detailed manual installation

## Docker Alternative

If you prefer Docker (uses more RAM but easier updates):

```bash
# Install Docker on Diet Pi
sudo dietpi-software install 162 134  # Docker + Docker Compose

# Run with Docker
cd /home/dietpi/SolarApp
docker-compose -f docker-compose.rpi.yml up -d
```

## Key Files

| File | Purpose |
|------|---------|
| `/etc/nginx/sites-available/solarapp` | nginx site config |
| `/etc/systemd/system/solarapp-backend.service` | Backend service |
| `/etc/systemd/system/solarapp-xml-parser.service` | XML parser service |
| `/home/dietpi/SolarApp/backend/.env` | Backend configuration |
| `/home/dietpi/SolarApp/backend/data/solarapp.db` | Database file |

## Configuration

### Backend Configuration

Edit `/home/dietpi/SolarApp/backend/.env`:

```env
# Database
SOLARAPP_DB_URL=sqlite:////home/dietpi/SolarApp/backend/data/solarapp.db

# XML Parser
XML_PARSER_URL=http://localhost:5000
XML_PARSER_TOKEN=dev-token-12345  # Use default token (change for production)

# CORS (adjust for your network)
CORS_ORIGINS=http://localhost,http://192.168.1.*
```

After changing, restart backend:
```bash
sudo systemctl restart solarapp-backend
```

### nginx Configuration

Key settings in `/etc/nginx/nginx.conf`:
- `worker_processes 1;` - Single worker for low RAM usage
- `worker_connections 256;` - Limit concurrent connections
- `gzip on;` - Enable compression

After changing, test and reload:
```bash
sudo nginx -t
sudo nginx -s reload
```

## Performance Tips

1. **SD Card**: Use Class 10 or better, A1/A2 rated
2. **Memory Split**: Allocate minimal RAM to GPU (16MB for headless)
3. **CPU Governor**: Set to `ondemand` or `performance` in `dietpi-config`
4. **Swap**: Disable if you have 1GB+ RAM to reduce SD card wear
5. **Monitoring**: Use `htop` or `dietpi-services` to watch resources

## Getting Help

- **Diet Pi docs**: https://dietpi.com/docs/
- **Full SolarApp guide**: [DIETPI.md](DIETPI.md)
- **Raspberry Pi optimizations**: [RASPBERRY_PI.md](RASPBERRY_PI.md)
- **GitHub issues**: https://github.com/catar13274/SolarApp/issues

## Security Notes

For production use:
1. Change default passwords in `.env` files
2. Configure firewall: `sudo ufw allow 80/tcp`
3. Consider HTTPS with Let's Encrypt
4. Restrict CORS_ORIGINS in backend `.env`
5. Keep system updated: `sudo apt update && sudo apt upgrade`

---

**Quick, lightweight, and optimized for Diet Pi! 🚀**
