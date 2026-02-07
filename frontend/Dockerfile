FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
# Install all dependencies (production + dev) for build
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

FROM nginx:alpine

# Optimize nginx for Raspberry Pi - use minimal worker processes
RUN sed -i 's/worker_processes auto;/worker_processes 1;/' /etc/nginx/nginx.conf

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Add gzip compression configuration for better performance
RUN echo 'gzip on; gzip_vary on; gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;' > /etc/nginx/conf.d/gzip.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
