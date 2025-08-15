# Setup and Deployment Guide

Complete guide for setting up Device Chat PWA in different environments.

## 🚀 Local Development Setup

### Prerequisites
- Node.js 18+ and Yarn
- Python 3.8+ and pip
- MongoDB (local installation or Docker)
- OpenAI API Key

### 1. Environment Setup

#### Backend Environment
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="device_chat_dev"
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# Generate these using: web-push generate-vapid-keys
VAPID_PRIVATE_KEY="your-vapid-private-key"
VAPID_PUBLIC_KEY="your-vapid-public-key" 
VAPID_EMAIL="mailto:dev@yourapp.com"

# Your OpenAI API key
OPENAI_API_KEY="sk-proj-your-openai-key-here"
```

#### Frontend Environment
```bash
cd frontend
cp .env.example .env
```

Edit `frontend/.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=3000
```

### 2. Install Dependencies

#### Backend
```bash
cd backend
pip install -r requirements.txt

# Install AI integration library
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
```

#### Frontend
```bash
cd frontend
yarn install
```

### 3. Generate VAPID Keys
```bash
# Install web-push CLI globally
npm install -g web-push

# Generate VAPID keys
web-push generate-vapid-keys

# Copy the keys to your backend/.env file
```

### 4. Start Services

#### Terminal 1 - MongoDB (if running locally)
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or if installed locally
mongod
```

#### Terminal 2 - Backend
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

#### Terminal 3 - Frontend
```bash
cd frontend
yarn start
```

### 5. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

## 🌐 Production Deployment

### Docker Deployment

#### 1. Create Dockerfile for Backend
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

COPY . .

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### 2. Create Dockerfile for Frontend
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS build

WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install

COPY . .
RUN yarn build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 3. Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password

  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://admin:password@mongodb:27017/device_chat?authSource=admin
    depends_on:
      - mongodb
    volumes:
      - ./backend/.env:/app/.env

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  mongodb_data:
```

### Cloud Deployment Options

#### Heroku Deployment

1. **Backend (Heroku)**
```bash
# Create Heroku app
heroku create your-app-backend

# Set environment variables
heroku config:set MONGO_URL="your-mongodb-atlas-url"
heroku config:set OPENAI_API_KEY="your-openai-key"
heroku config:set VAPID_PRIVATE_KEY="your-vapid-private-key"
heroku config:set VAPID_PUBLIC_KEY="your-vapid-public-key"

# Deploy
git subtree push --prefix backend heroku main
```

2. **Frontend (Vercel/Netlify)**
```bash
# Build settings
Build command: yarn build
Output directory: build

# Environment variables
REACT_APP_BACKEND_URL=https://your-app-backend.herokuapp.com
```

#### AWS Deployment

1. **Backend (AWS Lambda + API Gateway)**
2. **Frontend (AWS S3 + CloudFront)**
3. **Database (AWS DocumentDB or MongoDB Atlas)**

## 🔧 Configuration Options

### MongoDB Options

#### Local MongoDB
```env
MONGO_URL="mongodb://localhost:27017"
```

#### MongoDB Atlas (Cloud)
```env
MONGO_URL="mongodb+srv://username:password@cluster.mongodb.net/database"
```

#### Docker MongoDB
```env
MONGO_URL="mongodb://admin:password@localhost:27017/device_chat?authSource=admin"
```

### CORS Configuration

#### Development
```env
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

#### Production
```env
CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

### WebSocket Configuration

For production, ensure your deployment supports WebSocket connections:

- **Heroku**: Supports WebSocket out of the box
- **AWS ALB**: Enable sticky sessions
- **Nginx**: Configure proxy_pass with WebSocket headers

## 🧪 Testing in Different Environments

### Development Testing
```bash
# Backend tests
cd backend
python test_ai_chat.py
python test_new_apis.py

# Frontend tests (if you add them)
cd frontend
yarn test
```

### Production Testing
1. **API Health Check**: `GET /api/`
2. **WebSocket Connection**: Test via browser console
3. **Push Notifications**: Test subscription and delivery
4. **AI Chat**: Send test messages to verify OpenAI integration

## 🔒 Security Considerations

### API Keys Management
- Use environment variables only
- Never commit .env files to git
- Rotate keys regularly
- Monitor API usage and set limits

### HTTPS Requirements
- Use HTTPS in production for PWA features
- WebSocket requires WSS (secure WebSocket)
- Push notifications require HTTPS

### Database Security
- Use MongoDB authentication
- Enable MongoDB SSL/TLS
- Implement proper access controls
- Regular backups

### Rate Limiting
```python
# Add to backend for production
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.route("/api/chat/send")
@limiter.limit("10/minute")  # 10 requests per minute
async def send_chat_message():
    # ... your code
```

## 📊 Monitoring and Logging

### Application Monitoring
- Add health check endpoints
- Monitor API response times
- Track WebSocket connections
- Monitor OpenAI API usage and costs

### Error Handling
- Implement comprehensive error logging
- Set up alerts for critical errors
- Monitor database performance
- Track user engagement metrics

## 🔄 Updates and Maintenance

### Dependency Updates
```bash
# Backend
pip list --outdated
pip install -r requirements.txt --upgrade

# Frontend
yarn outdated
yarn upgrade
```

### Database Migrations
- Plan for schema changes
- Implement migration scripts
- Backup before major updates
- Test migrations in staging

## 📱 PWA Deployment Checklist

- ✅ HTTPS enabled
- ✅ Service worker registered
- ✅ Web app manifest configured
- ✅ Icons for different sizes
- ✅ Push notification setup
- ✅ Offline functionality tested
- ✅ Mobile viewport optimized
- ✅ Touch targets minimum 44px

## 🆘 Troubleshooting

### Common Issues

1. **WebSocket Connection Fails**
   - Check HTTPS/WSS configuration
   - Verify CORS settings
   - Check firewall/proxy settings

2. **Push Notifications Not Working**
   - Verify VAPID keys are correct
   - Check browser notification permissions
   - Ensure HTTPS is enabled

3. **AI Chat Not Responding**
   - Verify OpenAI API key
   - Check API rate limits
   - Monitor API usage and billing

4. **Database Connection Issues**
   - Verify MongoDB URL format
   - Check network connectivity
   - Ensure database is running

### Debug Commands
```bash
# Check logs
tail -f backend.log
docker logs container-name

# Test API endpoints
curl -X GET http://localhost:8001/api/
curl -X POST http://localhost:8001/api/chat/send

# MongoDB connection test
mongosh "your-mongodb-url"
```

---

**Happy Deploying! 🚀**