# Raspberry Pi Optimization Guide

This guide provides detailed instructions for running SolarApp on Raspberry Pi devices with optimal performance and minimal resource usage.

## Supported Raspberry Pi Models

SolarApp has been optimized for:
- **Raspberry Pi 4 (2GB+ RAM)** - Recommended
- **Raspberry Pi 3 B+ (1GB RAM)** - Supported
- **Raspberry Pi Zero 2 W** - Backend only, limited features

## Performance Optimizations

### 1. Memory Optimization
- Single Uvicorn worker process (reduces memory footprint by ~60%)
- Reduced connection pool and concurrency limits
- SQLite WAL mode to minimize memory usage
- Optimized Python bytecode compilation
- Removed unnecessary .pyc files in Docker images

### 2. CPU Optimization
- Reduced worker processes for ARM CPUs
- Gzip compression for API responses
- Code splitting in frontend for faster loading
- Terser minification with console removal

### 3. SD Card Optimization
- SQLite Write-Ahead Logging (WAL) mode reduces write cycles
- Docker log rotation (10MB max, 3 files)
- Memory-based temp storage for SQLite
- Optimized Docker layer caching

### 4. Network Optimization
- Gzip compression on both backend and frontend
- Code splitting for smaller initial bundles
- Optimized chunk sizes for slower connections

## Installation Options

### Option 1: Docker Installation (Recommended for Raspberry Pi 4)

Use the optimized Docker Compose configuration:

```bash
# Clone the repository
git clone https://github.com/catar13274/SolarApp.git
cd SolarApp

# Use the Raspberry Pi optimized configuration
docker-compose -f docker-compose.rpi.yml up -d

# View logs
docker-compose -f docker-compose.rpi.yml logs -f

# Stop services
docker-compose -f docker-compose.rpi.yml down
```

**Resource Usage:**
- Backend: ~128-256MB RAM, 25-50% CPU
- XML Parser: ~64-128MB RAM, 10-25% CPU
- Frontend (nginx): ~32-64MB RAM, 10-25% CPU
- **Total: ~300-500MB RAM**

### Option 2: Native Installation (Best for Raspberry Pi 3/Zero)

For lower-resource devices, run services natively without Docker:

```bash
# Clone the repository
git clone https://github.com/catar13274/SolarApp.git
cd SolarApp

# Run the installation script
chmod +x install.sh
sudo ./install.sh

# Install Raspberry Pi optimized systemd services
sudo cp systemd/solarapp-backend-rpi.service /etc/systemd/system/
sudo cp systemd/solarapp-xml-parser-rpi.service /etc/systemd/system/

# IMPORTANT: Edit the service files to match your installation:
# 1. Change "User=pi" to your actual username
# 2. Update all paths to match where you installed SolarApp
#    (e.g., if you installed to /opt/SolarApp instead of /home/pi/SolarApp)
sudo nano /etc/systemd/system/solarapp-backend-rpi.service
sudo nano /etc/systemd/system/solarapp-xml-parser-rpi.service

# Example: If you installed to /opt/SolarApp, replace all instances of:
#   /home/pi/SolarApp -> /opt/SolarApp
# in both service files

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable solarapp-backend-rpi solarapp-xml-parser-rpi
sudo systemctl start solarapp-backend-rpi solarapp-xml-parser-rpi

# Check status
systemctl status solarapp-backend-rpi
systemctl status solarapp-xml-parser-rpi
```

**Resource Usage (Native):**
- Backend: ~80-150MB RAM
- XML Parser: ~40-80MB RAM
- Frontend (if built): Static files served by backend or separate nginx
- **Total: ~150-250MB RAM**

### Option 3: Backend-Only Mode (Raspberry Pi Zero 2 W)

For extremely resource-constrained devices, run only the backend:

```bash
cd SolarApp/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Run with optimized settings
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --limit-concurrency 25 --timeout-keep-alive 5
```

Access the API at `http://raspberry-pi-ip:8000/docs`

**Resource Usage:**
- Backend only: ~60-120MB RAM
- Suitable for API-only deployments or headless operation

## Configuration Optimizations

### Environment Variables

Create or edit `<your-install-dir>/backend/.env` (replace `<your-install-dir>` with your actual installation path):

```env
# Database (update path to match your installation directory)
SOLARAPP_DB_URL=sqlite:////home/pi/SolarApp/backend/data/solarapp.db

# If you installed to /opt/SolarApp, use:
# SOLARAPP_DB_URL=sqlite:////opt/SolarApp/backend/data/solarapp.db

# XML Parser
XML_PARSER_URL=http://localhost:5000
XML_PARSER_TOKEN=your-secure-token-here

# CORS (adjust for your network)
CORS_ORIGINS=http://raspberrypi.local:3000,http://raspberrypi.local:5173

# Python optimizations
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### SQLite Optimizations

The database is automatically configured with:
- **WAL mode**: Reduces write operations, better for SD cards
- **Normal synchronous**: Faster writes with minimal risk
- **32MB cache**: Optimal for Raspberry Pi memory
- **Memory temp storage**: Reduces SD card wear
- **Memory-mapped I/O**: Faster reads

These settings are automatically applied via `backend/app/database.py`.

### Uvicorn Optimizations

Optimized startup parameters for Raspberry Pi:
- `--workers 1`: Single worker process (sufficient for most use cases)
- `--limit-concurrency 50`: Limit concurrent connections (25 for Pi Zero)
- `--timeout-keep-alive 5`: Shorter keep-alive for better resource recycling

## Performance Tuning

### For Raspberry Pi 4 (4GB+ RAM)

You can increase resources in `docker-compose.rpi.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

Or for native installation:
```bash
# Increase to 2 workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --limit-concurrency 100
```

### For Raspberry Pi 3 B+ (1GB RAM)

Keep default settings or reduce further:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --limit-concurrency 30
```

### For Raspberry Pi Zero 2 W (512MB RAM)

Minimal configuration:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --limit-concurrency 10
```

## Monitoring

### Check Service Status

```bash
# Systemd services
systemctl status solarapp-backend-rpi
systemctl status solarapp-xml-parser-rpi

# Docker services
docker-compose -f docker-compose.rpi.yml ps
docker stats
```

### Monitor Resource Usage

```bash
# Overall system
htop

# Memory usage
free -h

# SD card I/O
sudo iotop

# Service logs
journalctl -u solarapp-backend-rpi -f
docker-compose -f docker-compose.rpi.yml logs -f
```

## Network Access

### Local Network Access

Access SolarApp from other devices on your network:

```bash
# Find your Raspberry Pi IP
hostname -I

# Access from browser on another device
http://YOUR_PI_IP:3000        # Frontend (if running)
http://YOUR_PI_IP:8000/docs   # API Documentation
```

### Setup mDNS (Optional)

Enable accessing via hostname instead of IP:

```bash
# Install avahi-daemon
sudo apt-get update
sudo apt-get install avahi-daemon

# Access via
http://raspberrypi.local:3000
http://raspberrypi.local:8000/docs
```

## Troubleshooting

### High Memory Usage

1. Check running processes:
   ```bash
   ps aux --sort=-%mem | head -10
   ```

2. Reduce worker count or concurrency limits

3. Consider backend-only mode

### Slow Performance

1. Verify SD card speed (Class 10 or better recommended)

2. Check for thermal throttling:
   ```bash
   vcgencmd measure_temp
   vcgencmd get_throttled
   ```

3. Ensure adequate cooling

4. Check system load:
   ```bash
   uptime
   ```

### Database Issues

If database becomes corrupted:

```bash
# Backup current database
cp backend/data/solarapp.db backend/data/solarapp.db.backup

# Rebuild database
cd backend
source .venv/bin/activate
python3 -c "from app.database import create_db_and_tables; create_db_and_tables()"
python3 sample_data.py  # Optional: reload sample data
```

### Service Won't Start

1. Check logs:
   ```bash
   journalctl -u solarapp-backend-rpi -n 50
   journalctl -u solarapp-xml-parser-rpi -n 50
   ```

2. Verify Python environment:
   ```bash
   source backend/.venv/bin/activate
   python3 --version  # Should be 3.9+
   ```

3. Check port availability:
   ```bash
   sudo netstat -tlnp | grep :8000
   sudo netstat -tlnp | grep :5000
   ```

## SD Card Longevity

To extend SD card life on Raspberry Pi:

### 1. Use WAL Mode (Already Enabled)
The SQLite database uses WAL mode to reduce write operations.

### 2. Log to RAM (Optional)

Edit `/etc/fstab`:
```
tmpfs /var/log tmpfs defaults,noatime,mode=0755 0 0
```

**Warning:** Logs will be lost on reboot.

### 3. Reduce Swap Usage

```bash
sudo dphys-swapfile swapoff
sudo dphys-swapfile uninstall
sudo systemctl disable dphys-swapfile
```

### 4. Use Quality SD Card

- **Minimum:** Class 10, A1 rating
- **Recommended:** UHS-I U3, A2 rating
- **Best:** Industrial-grade SD cards

## Backup Strategy

### Automated Backup Script

Create `/home/pi/backup-solarapp.sh` (adjust paths to match your installation):

```bash
#!/bin/bash
# Update INSTALL_DIR to match where you installed SolarApp
INSTALL_DIR="/home/pi/SolarApp"
BACKUP_DIR="/home/pi/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
cp "$INSTALL_DIR/backend/data/solarapp.db" "$BACKUP_DIR/solarapp_$DATE.db"

# Keep only last 7 days
find $BACKUP_DIR -name "solarapp_*.db" -mtime +7 -delete
```

Add to crontab:
```bash
chmod +x /home/pi/backup-solarapp.sh
crontab -e
# Add: 0 2 * * * /home/pi/backup-solarapp.sh
```

## Advanced: Read-Only Root Filesystem

For maximum SD card longevity, configure read-only root filesystem:

```bash
# Install overlay filesystem
sudo apt-get install overlayroot

# Configure
sudo nano /etc/overlayroot.conf
# Set: overlayroot="tmpfs"

# Reboot
sudo reboot
```

**Note:** This is advanced and makes system updates more complex.

## Performance Benchmarks

### Raspberry Pi 4 (4GB RAM)
- **Startup time:** ~5-8 seconds
- **API response time:** 20-50ms (local)
- **Dashboard load time:** 1-2 seconds
- **Concurrent users:** 5-10
- **Memory usage:** 300-500MB total

### Raspberry Pi 3 B+ (1GB RAM)
- **Startup time:** ~10-15 seconds
- **API response time:** 50-100ms (local)
- **Dashboard load time:** 2-4 seconds
- **Concurrent users:** 2-5
- **Memory usage:** 250-400MB total

### Raspberry Pi Zero 2 W (512MB RAM)
- **Startup time:** ~15-20 seconds (backend only)
- **API response time:** 100-200ms (local)
- **Concurrent users:** 1-2
- **Memory usage:** 150-250MB (backend only)

## Additional Resources

- [Official Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [FastAPI Performance Guide](https://fastapi.tiangolo.com/deployment/)
- [SQLite Optimization](https://www.sqlite.org/optoverview.html)
- [Docker on Raspberry Pi](https://docs.docker.com/engine/install/debian/)

## Support

For Raspberry Pi specific issues:
1. Check this guide's troubleshooting section
2. Review system logs: `journalctl -xe`
3. Monitor resources: `htop`, `iostat`
4. Open an issue on GitHub with:
   - Raspberry Pi model and RAM
   - Installation method used
   - Error logs
   - Output of `free -h` and `df -h`

---

**Optimized for Raspberry Pi with ❤️**
