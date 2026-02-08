# Troubleshooting Guide: 502 Bad Gateway Error

This guide helps you fix the common "502 Bad Gateway" error when accessing the SolarApp API.

## Error Symptoms

You see errors in the browser console like:

```
GET http://192.168.0.151/api/v1/materials/ 502 (Bad Gateway)
(anonymous) @ data-vendor-BqleKcSk.js:1
```

Or similar errors showing:
- 502 Bad Gateway
- Connection refused
- Network Error
- Failed to fetch

## Root Cause

The frontend was built with a hardcoded IP address in the `VITE_API_URL` environment variable. This IP address got baked into the JavaScript bundle during the build process.

When the application tries to reach that hardcoded IP, one of these happens:
- The server at that IP is not running
- The IP address is not accessible from the current network
- The backend service on that IP is down
- The IP address has changed

## Quick Fix

### Option 1: Rebuild Frontend Without Hardcoded IP (Recommended)

This is the proper long-term solution:

```bash
cd /path/to/SolarApp/frontend

# Remove any .env file that might have VITE_API_URL set
rm -f .env .env.local .env.production

# Or edit .env to ensure VITE_API_URL is empty
echo "VITE_API_URL=" > .env

# Rebuild the frontend
npm run build

# If using nginx, restart it
sudo systemctl restart nginx

# If using systemd with the frontend service
sudo systemctl restart solarapp-frontend
```

### Option 2: Access via Correct IP/Domain

If you must use the current build, access the application via the IP or domain it was built for:

```
http://192.168.0.151/
```

But note that this only works if:
- You're on the same network as 192.168.0.151
- The backend is running on that server
- Port 80 (or the appropriate port) is accessible

## Detailed Solution Steps

### Step 1: Identify the Problem

Check the browser console (F12 → Console tab) and look for:
- What URL is being requested? (e.g., `http://192.168.0.151/api/...`)
- What error is returned? (502, 404, Connection Refused, etc.)

### Step 2: Check Backend Service

Verify the backend is running:

```bash
# Check service status
systemctl status solarapp-backend

# Check if backend is listening
curl http://localhost:8000/api/v1/materials/

# Check logs for errors
journalctl -u solarapp-backend -n 50
```

If the backend is not running:
```bash
sudo systemctl start solarapp-backend
```

### Step 3: Check nginx Configuration

If using nginx (recommended for production):

```bash
# Test nginx configuration
sudo nginx -t

# Check if nginx is running
systemctl status nginx

# Check nginx error logs
tail -n 50 /var/log/nginx/error.log

# Check if nginx is proxying correctly
curl -v http://localhost/api/v1/materials/
```

If nginx is not configured correctly, see [DIETPI.md](DIETPI.md) or [frontend/BUILD.md](frontend/BUILD.md).

### Step 4: Rebuild Frontend Properly

Navigate to the frontend directory:
```bash
cd /path/to/SolarApp/frontend
```

Check current configuration:
```bash
# Check if .env file exists
ls -la .env*

# If .env exists, check its contents
cat .env
```

Remove or fix VITE_API_URL:
```bash
# Option A: Remove all .env files
rm -f .env .env.local .env.production

# Option B: Edit .env to make VITE_API_URL empty
nano .env
# Change to: VITE_API_URL=
```

Rebuild:
```bash
# Install dependencies if needed
npm install

# Build with validation
npm run build
```

Watch for warnings from the build validator:
```
⚠️  WARNING: VITE_API_URL contains a hardcoded IP address!
```

If you see this warning, fix the `.env` file and rebuild.

### Step 5: Deploy the New Build

#### For nginx Deployments:

```bash
# Copy to nginx web root (adjust path as needed)
sudo cp -r dist/* /var/www/html/
# Or wherever your nginx root is configured

# Restart nginx
sudo systemctl restart nginx
```

#### For Docker Deployments:

```bash
# Rebuild the frontend container
docker-compose -f docker-compose.rpi.yml build frontend

# Restart containers
docker-compose -f docker-compose.rpi.yml up -d
```

### Step 6: Verify the Fix

Test the application:

```bash
# Test frontend access
curl http://localhost/

# Test API access through nginx
curl http://localhost/api/v1/materials/

# Check browser console for errors
# Open browser, press F12, go to Console tab
# Refresh the page and check for errors
```

You should see API requests going to `/api/v1/...` instead of `http://192.168.x.x/api/v1/...`.

## Prevention

To prevent this issue in the future:

### 1. Use .env.example as Template

Always copy from `.env.example`:
```bash
cp .env.example .env
```

The example file has proper documentation and safe defaults.

### 2. Never Commit .env Files

The `.gitignore` file excludes `.env` files. Don't commit them.

### 3. Follow Deployment Guidelines

- **For nginx deployments**: Leave `VITE_API_URL` empty
- **For development**: Leave `VITE_API_URL` empty (uses Vite proxy)
- **For standalone**: Use domain names, not IP addresses

See [frontend/BUILD.md](frontend/BUILD.md) for detailed guidelines.

### 4. Use Build Validation

The build script (`npm run build`) automatically validates your configuration and warns about hardcoded IPs.

### 5. Document Your Setup

If you must use a specific configuration, document it in your deployment notes.

## Understanding the Architecture

### With nginx (Recommended):

```
Browser → http://your-server/
        ↓
    nginx (Port 80)
        ↓ (proxies /api → localhost:8000)
        ↓
    Backend (Port 8000)
```

The frontend doesn't need to know the backend URL - nginx handles it.

### Without nginx:

```
Browser → http://your-server:3000/ (Frontend)
        ↓
    Direct API calls to http://your-server:8000/api/
        ↓
    Backend (Port 8000)
```

The frontend needs `VITE_API_URL=http://your-server:8000` set at build time.

## Common Mistakes

❌ **Building with development IP**
```bash
VITE_API_URL=http://192.168.0.151:8000 npm run build
```

✅ **Correct approach**
```bash
npm run build  # No VITE_API_URL set
```

❌ **Using IP in .env**
```
VITE_API_URL=http://192.168.0.151:8000
```

✅ **Correct .env**
```
VITE_API_URL=
# or just don't create .env file
```

❌ **Building on one machine for another**
```bash
# Building on dev machine for production
VITE_API_URL=http://localhost:8000 npm run build
# This won't work on production!
```

✅ **Correct approach**
```bash
# Build on production or use empty VITE_API_URL with nginx
npm run build
```

## Still Having Issues?

### Check All Services:

```bash
# Backend
systemctl status solarapp-backend
curl http://localhost:8000/api/v1/materials/

# XML Parser
systemctl status solarapp-xml-parser
curl http://localhost:5000/health || echo "No health endpoint"

# nginx
systemctl status nginx
curl http://localhost/api/v1/materials/

# All logs
journalctl -u solarapp-backend -u nginx -n 100
```

### Get More Help:

See also:
- [LOGGING.md](LOGGING.md) - Comprehensive logging guide
- [frontend/BUILD.md](frontend/BUILD.md) - Build configuration guide
- [DIETPI.md](DIETPI.md) - Diet Pi specific setup
- [README.md](README.md) - General troubleshooting

### Report an Issue:

If you still can't resolve the issue, gather logs:

```bash
# Collect diagnostic information
echo "=== System Info ===" > ~/solarapp-diagnostic.txt
uname -a >> ~/solarapp-diagnostic.txt
echo "=== Services ===" >> ~/solarapp-diagnostic.txt
systemctl status solarapp-backend >> ~/solarapp-diagnostic.txt
systemctl status nginx >> ~/solarapp-diagnostic.txt
echo "=== Backend Logs ===" >> ~/solarapp-diagnostic.txt
journalctl -u solarapp-backend -n 100 >> ~/solarapp-diagnostic.txt
echo "=== nginx Logs ===" >> ~/solarapp-diagnostic.txt
journalctl -u nginx -n 100 >> ~/solarapp-diagnostic.txt
echo "=== nginx Config Test ===" >> ~/solarapp-diagnostic.txt
nginx -t >> ~/solarapp-diagnostic.txt 2>&1

# Review and share the file (remove any sensitive information first)
cat ~/solarapp-diagnostic.txt
```

Open an issue on GitHub with this diagnostic information.
