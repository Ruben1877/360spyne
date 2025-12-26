# Clone Spyne API Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source
COPY tsconfig.json ./
COPY src ./src

# Build
RUN npm run build

# Production image
FROM node:20-alpine AS runner

WORKDIR /app

# Install Python for processing
RUN apk add --no-cache python3 py3-pip python3-dev build-base

# Copy built files
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

# Copy Python scripts
COPY python ./python

# Install Python dependencies
RUN pip3 install --no-cache-dir -r python/requirements.txt

# Create logs directory
RUN mkdir -p logs

ENV NODE_ENV=production
ENV PORT=3001

EXPOSE 3001

CMD ["node", "dist/index.js"]

