# Frontend Build Guide

This guide explains how to properly build the SolarApp frontend to avoid common configuration issues.

## Quick Start

### Development Mode
```bash
npm install
npm run dev
```
The dev server will run on http://localhost:5173 and automatically proxy API requests to the backend.

### Production Build
```bash
npm install
npm run build
```
The production build will be created in the `dist/` directory.

## API Configuration

The frontend needs to know how to connect to the backend API. This is configured via the `VITE_API_URL` environment variable.

### ⚠️ IMPORTANT: Avoiding Hardcoded IP Addresses

**DO NOT** set `VITE_API_URL` to a hardcoded IP address like `http://192.168.0.151` unless you have a very specific reason. This will cause the following issues:

- ❌ App will fail when the IP address changes
- ❌ Not suitable for production deployments
- ❌ May cause CORS (Cross-Origin Resource Sharing) errors
- ❌ Will show "502 Bad Gateway" or "Network Error" when the server is unavailable

### Recommended Configurations

#### 1. nginx Deployment (Recommended for Production)

**Leave `VITE_API_URL` empty** - This is the default and recommended approach.

```bash
# .env file (or don't create one at all)
VITE_API_URL=
```

nginx will proxy all `/api` requests to the backend. This is configured in:
- `nginx.conf` (Docker deployments)
- `/etc/nginx/sites-available/solarapp` (Native Diet Pi deployments)

**How it works:**
1. User accesses http://your-server/
2. nginx serves the React app
3. When React makes API calls to `/api/v1/materials/`, nginx proxies them to `http://localhost:8000/api/v1/materials/`
4. Backend responds through nginx

**Benefits:**
- ✅ Works on any IP address or domain
- ✅ No CORS issues
- ✅ Single port for frontend and backend
- ✅ SSL/TLS termination at nginx
- ✅ Better performance and caching

#### 2. Development Mode

**Leave `VITE_API_URL` empty** - Vite's dev server includes a proxy.

The `vite.config.js` includes this proxy configuration:
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

This means requests to `/api` are automatically forwarded to the backend at `http://localhost:8000`.

#### 3. Standalone Frontend (Without nginx)

If you're running the frontend separately from nginx and need to connect to a remote backend, use a domain name or relative path:

```bash
# Using a domain name (recommended)
VITE_API_URL=https://api.mycompany.com

# Using localhost (development only)
VITE_API_URL=http://localhost:8000

# Using relative path (works with nginx)
VITE_API_URL=/api
```

## Build Validation

The build process includes automatic validation to check for common mistakes:

```bash
npm run build
```

This will:
1. Run `validate-build.js` to check environment variables
2. Warn if hardcoded IP addresses are detected
3. Proceed with the build

Example output:
```
=== Build Environment Validation ===

Checking build environment...

✓ VITE_API_URL is not set (using nginx proxy or Vite dev proxy)

=== Validation Complete ===
```

## Common Issues and Solutions

### Issue: 502 Bad Gateway Error

**Symptom:** Console shows errors like:
```
GET http://192.168.0.151/api/v1/materials/ 502 (Bad Gateway)
```

**Cause:** The frontend was built with `VITE_API_URL=http://192.168.0.151` which hardcoded that IP into the JavaScript bundle.

**Solution:**
1. Remove or unset `VITE_API_URL`:
   ```bash
   # Remove .env file if it exists
   rm .env
   
   # Or edit .env and leave VITE_API_URL empty
   echo "VITE_API_URL=" > .env
   ```

2. Rebuild the frontend:
   ```bash
   npm run build
   ```

3. Ensure nginx is properly configured to proxy `/api` requests.

### Issue: CORS Errors

**Symptom:** Console shows:
```
Access to XMLHttpRequest at 'http://other-server:8000/api/...' from origin 'http://my-server' has been blocked by CORS policy
```

**Cause:** Frontend and backend are on different origins and CORS is not configured.

**Solution:** Use nginx to proxy requests (recommended) or configure CORS in the backend.

### Issue: API Not Found (404)

**Symptom:** All API requests return 404 errors.

**Cause:** Either:
- Backend is not running
- nginx is not configured correctly
- Wrong `VITE_API_URL` setting

**Solution:**
1. Check backend is running:
   ```bash
   systemctl status solarapp-backend
   curl http://localhost:8000/api/v1/materials/
   ```

2. Check nginx configuration:
   ```bash
   nginx -t
   curl http://localhost/api/v1/materials/
   ```

3. Verify `VITE_API_URL` is empty or correct.

## Environment Files

### .env.example
Template file with documentation - copy this to create `.env`:
```bash
cp .env.example .env
```

### .env (Git Ignored)
Your local environment configuration. **This file is not committed to git.**

### .env.production
Used automatically when running `npm run build`.

## Docker Builds

When building with Docker, the Dockerfile should not set `VITE_API_URL`:

```dockerfile
# Good - no VITE_API_URL set
RUN npm run build

# Bad - hardcodes API URL
RUN VITE_API_URL=http://192.168.0.1:8000 npm run build
```

The Docker setup uses nginx to proxy API requests, so `VITE_API_URL` should remain empty.

## Deployment Checklist

Before deploying to production:

- [ ] `VITE_API_URL` is empty or uses relative path
- [ ] nginx is configured to proxy `/api` requests
- [ ] Build validation passes without warnings
- [ ] Backend service is running and accessible
- [ ] nginx service is running
- [ ] Test API requests work: `curl http://your-server/api/v1/materials/`

## Testing the Build

After building, you can test locally:

```bash
# Build the frontend
npm run build

# Preview the production build
npm run preview
```

The preview server will run on http://localhost:4173.

To test with nginx:

```bash
# Copy build to nginx directory (example)
sudo cp -r dist/* /var/www/html/

# Restart nginx
sudo systemctl restart nginx

# Test in browser
curl http://localhost/
curl http://localhost/api/v1/materials/
```

## Additional Resources

- [Vite Environment Variables Documentation](https://vitejs.dev/guide/env-and-mode.html)
- [DIETPI.md](../DIETPI.md) - nginx configuration for Diet Pi
- [README.md](../README.md) - General installation guide

## Support

If you encounter issues:

1. Check the build validation output
2. Verify your `.env` file (or that it doesn't exist)
3. Check nginx configuration: `nginx -t`
4. Check backend logs: `journalctl -u solarapp-backend -f`
5. Check nginx logs: `journalctl -u nginx -f`
6. See [LOGGING.md](../LOGGING.md) for detailed logging commands
