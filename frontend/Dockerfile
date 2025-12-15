FROM node:24-alpine AS build

WORKDIR /app

# Copy dependency files first for better caching
COPY package.json yarn.lock ./

# Install dependencies with frozen lockfile
RUN yarn install --frozen-lockfile --production=false

# Copy source files
COPY . .

# Build the application
RUN yarn build

# Production stage
FROM node:24-alpine

WORKDIR /app

# Install serve globally
RUN npm install -g serve && \
    adduser -D -H -s /sbin/nologin appuser && \
    mkdir -p /app/build && \
    chown -R appuser:appuser /app

# Copy built assets from build stage
COPY --from=build --chown=appuser:appuser /app/build ./build

# Run as non-root user
USER appuser

EXPOSE 9000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:9000/ || exit 1

CMD ["serve", "-s", "build", "-l", "9000"]
