# API Configuration Guide

This document explains how SolarApp handles API communication between the frontend and backend, and how to avoid common configuration issues.

## Overview

SolarApp uses a flexible configuration approach that works in different deployment scenarios:

1. **Development** (Vite dev server with proxy)
2. **Production with nginx** (nginx proxies /api)
3. **Production standalone** (direct API URL)

## How It Works

### The `VITE_API_URL` Environment Variable

The frontend uses the `VITE_API_URL` environment variable to determine how to connect to the backend:

```javascript
// frontend/src/services/api.js
const API_URL = import.meta.env.VITE_API_URL || ''
```

- **When empty (default)**: Uses relative URLs like `/api/v1/materials/`
- **When set**: Prepends the URL to all API requests

### Build-Time Baking

⚠️ **IMPORTANT**: The value of `VITE_API_URL` is baked into the JavaScript bundle at build time. Once built, it cannot be changed without rebuilding.

This means:
- ✅ If you build with `VITE_API_URL=` (empty), the bundle works anywhere with nginx proxy
- ❌ If you build with `VITE_API_URL=http://192.168.0.151`, it will ONLY work at that specific IP

## Configuration Scenarios

### Scenario 1: Development Mode (Recommended)

**Configuration**: Leave `VITE_API_URL` empty

```bash
# No .env file needed, or:
echo "VITE_API_URL=" > .env

npm run dev
```

**How it works**:
- Vite dev server runs on http://localhost:5173
- `vite.config.js` includes a proxy configuration:
  ```javascript
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
  ```
- Frontend makes requests to `/api/v1/materials/`
- Vite proxy forwards them to `http://localhost:8000/api/v1/materials/`
- Backend responds through Vite

**Benefits**:
- ✅ No CORS issues
- ✅ Simple setup
- ✅ Matches production behavior

### Scenario 2: Production with nginx (Recommended)

**Configuration**: Leave `VITE_API_URL` empty

```bash
# Build with no VITE_API_URL set
npm run build

# nginx configuration proxies /api to backend
```

**nginx configuration** (from dietpi-install.sh):
```nginx
location /api {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    # ... other headers
}
```

**How it works**:
- User accesses http://your-server/
- nginx serves the React app from `/path/to/frontend/dist`
- Frontend makes requests to `/api/v1/materials/`
- nginx proxies them to `http://127.0.0.1:8000/api/v1/materials/`
- Backend responds through nginx

**Benefits**:
- ✅ Single port (80 or 443 for HTTPS)
- ✅ No CORS issues
- ✅ SSL/TLS termination at nginx
- ✅ Works on any IP or domain
- ✅ Better caching and performance

### Scenario 3: Production Standalone (Not Recommended)

**Configuration**: Set `VITE_API_URL` to backend URL

```bash
# Build with specific backend URL
VITE_API_URL=https://api.mycompany.com npm run build
# or
VITE_API_URL=http://your-server:8000 npm run build
```

**How it works**:
- Frontend is served from one location (e.g., CDN, static host)
- Frontend makes requests to the hardcoded backend URL
- Backend must have CORS configured to allow the frontend origin

**When to use**:
- Frontend and backend are on completely different servers
- You're using a CDN for the frontend
- You have a fixed backend domain/URL

**Drawbacks**:
- ❌ Requires CORS configuration
- ❌ Different domains complicate authentication/cookies
- ❌ Must rebuild if backend URL changes
- ❌ Can't easily move between environments

## Common Mistakes

### Mistake 1: Hardcoded Development IP

❌ **Wrong**:
```bash
VITE_API_URL=http://192.168.0.151:8000 npm run build
```

**Problem**: This IP only works on your local network. When you deploy to production or the IP changes, the app breaks with "502 Bad Gateway" or "Connection Refused" errors.

✅ **Correct**:
```bash
npm run build  # No VITE_API_URL set
```

### Mistake 2: Building on Dev Machine for Production

❌ **Wrong**:
```bash
# On dev machine
VITE_API_URL=http://localhost:8000 npm run build
# Deploy to production
# App doesn't work - localhost on production refers to production server, not backend
```

✅ **Correct**:
```bash
# Build with empty VITE_API_URL, let nginx handle it
npm run build
```

### Mistake 3: Forgetting to Rebuild

❌ **Wrong**:
```bash
# Build once
npm run build
# Later, change VITE_API_URL in .env
# App still uses old URL - changes don't take effect!
```

✅ **Correct**:
```bash
# Change environment variable
# Then rebuild
npm run build
```

## Build Validation

The build process includes automatic validation (added in this PR):

```bash
npm run build
```

This runs `validate-build.js` before building, which:
- ✅ Checks if `VITE_API_URL` is set
- ⚠️  Warns if it contains a hardcoded IP address
- ℹ️  Provides recommendations for proper configuration

Example output with hardcoded IP:
```
⚠️  WARNING: VITE_API_URL contains a hardcoded IP address!
   Current value: http://192.168.0.151:8000

   Hardcoded IP addresses can cause issues:
   • App will fail if IP changes
   • Not suitable for production deployments
   • May cause CORS issues

   Recommended solutions:
   • For nginx deployments: Leave VITE_API_URL empty
   • For development: Leave empty to use Vite proxy
   • For production: Use a domain name or relative path
```

## Environment Files

### `.env.example`

Template with documentation. Copy to create `.env`:
```bash
cp .env.example .env
```

Contains:
```bash
# Leave empty for nginx deployments (recommended)
VITE_API_URL=
```

### `.env` (gitignored)

Your local environment configuration. **Not committed to git.**

For nginx deployments, should be empty or not exist:
```bash
# Option 1: Don't create it
# Option 2: Create with empty value
echo "VITE_API_URL=" > .env
```

### `.env.production`

Used automatically by Vite when building. Usually not needed.

## Troubleshooting

### Issue: 502 Bad Gateway

**Symptom**: Console shows:
```
GET http://192.168.0.151/api/v1/materials/ 502 (Bad Gateway)
```

**Cause**: Frontend was built with hardcoded IP

**Solution**: See [TROUBLESHOOTING_502.md](TROUBLESHOOTING_502.md)

Quick fix:
```bash
cd frontend
rm -f .env .env.local .env.production
npm run build
sudo systemctl restart nginx
```

### Issue: CORS Errors

**Symptom**: Console shows:
```
Access to XMLHttpRequest blocked by CORS policy
```

**Cause**: Frontend and backend on different origins without proper configuration

**Solution**: Use nginx proxy (Scenario 2) instead of standalone (Scenario 3)

### Issue: Connection Refused

**Symptom**: Console shows:
```
GET http://192.168.0.151/api/v1/materials/ net::ERR_CONNECTION_REFUSED
```

**Causes**:
1. Backend is not running
2. Firewall blocking the port
3. Wrong IP/port in `VITE_API_URL`

**Solution**:
1. Check backend: `systemctl status solarapp-backend`
2. Use nginx proxy instead of hardcoded URL

## Best Practices

1. **Always use nginx proxy in production**
   - Simpler configuration
   - No CORS issues
   - Better performance

2. **Never commit `.env` files**
   - Already in `.gitignore`
   - Contains environment-specific settings

3. **Use domain names, not IP addresses**
   - If you must set `VITE_API_URL`, use a domain
   - Example: `VITE_API_URL=https://api.mycompany.com`

4. **Test after building**
   - Always test the built app, not just dev mode
   - `npm run build && npm run preview`

5. **Document your deployment**
   - If using a non-standard configuration, document it
   - Include in deployment notes or README

## Architecture Diagrams

### With nginx Proxy (Recommended)

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ http://server/
       │ http://server/api/v1/materials/
       ▼
┌─────────────────────────────┐
│   nginx (Port 80)           │
│                             │
│  / → Frontend (dist/)       │
│  /api → http://127.0.0.1:8000  │
└─────────────┬───────────────┘
              │
              ▼
     ┌────────────────┐
     │ Backend :8000  │
     └────────────────┘
```

### Without nginx (Standalone)

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ http://server:3000/
       │ http://backend:8000/api/v1/materials/
       │
       ├──────────────────────┐
       │                      │
       ▼                      ▼
┌──────────────┐      ┌────────────────┐
│ Frontend     │      │ Backend :8000  │
│ (Port 3000)  │      │ (CORS enabled) │
└──────────────┘      └────────────────┘
```

## Additional Resources

- [frontend/BUILD.md](frontend/BUILD.md) - Detailed build guide
- [TROUBLESHOOTING_502.md](TROUBLESHOOTING_502.md) - Fix 502 errors
- [DIETPI.md](DIETPI.md) - Diet Pi installation with nginx
- [README.md](README.md) - General documentation
- [Vite Documentation](https://vitejs.dev/guide/env-and-mode.html) - Environment variables

## Summary

For most deployments:
1. Leave `VITE_API_URL` empty (default)
2. Use nginx to proxy `/api` to backend
3. Build with `npm run build`
4. Let the validation warn you if something's wrong

This approach:
- ✅ Works on any IP or domain
- ✅ No CORS issues
- ✅ Single port
- ✅ Easy to maintain
- ✅ Production-ready
