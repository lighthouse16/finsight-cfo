# ──────────────────────────────────────────────────────────
# Frontend build stage
# ──────────────────────────────────────────────────────────
FROM node:20-alpine AS build

ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

WORKDIR /app

# Install dependencies first (separate layer for caching)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build
COPY tsconfig.json tsconfig.node.json vite.config.ts index.html ./
COPY public/ public/ 2>/dev/null || true
COPY src/ src/
RUN npm run build

# ──────────────────────────────────────────────────────────
# Production serve stage
# ──────────────────────────────────────────────────────────
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
