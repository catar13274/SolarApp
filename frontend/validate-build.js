#!/usr/bin/env node

/**
 * Build Validation Script
 * Checks environment variables before build to prevent common mistakes
 */

// ANSI color codes
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const GREEN = '\x1b[32m';
const BLUE = '\x1b[34m';
const RESET = '\x1b[0m';

function log(message, color = '') {
  console.log(`${color}${message}${RESET}`);
}

function checkApiUrl() {
  const apiUrl = process.env.VITE_API_URL;
  
  // If not set or empty, that's fine - nginx will handle it
  if (!apiUrl || apiUrl.trim() === '') {
    log('✓ VITE_API_URL is not set (using nginx proxy or Vite dev proxy)', GREEN);
    return true;
  }
  
  // Check for hardcoded IP addresses (IPv4 pattern)
  const ipv4Pattern = /^https?:\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/;
  if (ipv4Pattern.test(apiUrl)) {
    log('\n⚠️  WARNING: VITE_API_URL contains a hardcoded IP address!', YELLOW);
    log(`   Current value: ${apiUrl}`, YELLOW);
    log('\n   Hardcoded IP addresses can cause issues:', YELLOW);
    log('   • App will fail if IP changes', YELLOW);
    log('   • Not suitable for production deployments', YELLOW);
    log('   • May cause CORS issues', YELLOW);
    log('\n   Recommended solutions:', BLUE);
    log('   • For nginx deployments: Leave VITE_API_URL empty', BLUE);
    log('   • For development: Leave empty to use Vite proxy', BLUE);
    log('   • For production: Use a domain name or relative path', BLUE);
    log('\n   To fix: unset VITE_API_URL or set it to empty string', BLUE);
    log('   Example: export VITE_API_URL="" or remove from .env\n', BLUE);
    
    // Don't fail the build, just warn
    return true;
  }
  
  // Check for localhost (fine for development)
  if (apiUrl.includes('localhost') || apiUrl.includes('127.0.0.1')) {
    log(`ℹ  VITE_API_URL is set to: ${apiUrl}`, BLUE);
    log('   Note: This will only work on the local machine', BLUE);
    return true;
  }
  
  // Relative path (good)
  if (apiUrl.startsWith('/')) {
    log(`✓ VITE_API_URL is set to relative path: ${apiUrl}`, GREEN);
    return true;
  }
  
  // Other URL (probably fine)
  log(`ℹ  VITE_API_URL is set to: ${apiUrl}`, BLUE);
  return true;
}

function main() {
  log('\n=== Build Environment Validation ===\n', BLUE);
  
  log('Checking build environment...\n');
  
  // Check API URL configuration
  checkApiUrl();
  
  log('\n=== Validation Complete ===\n', GREEN);
}

main();
