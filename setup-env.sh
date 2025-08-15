#!/bin/bash

# Setup Environment Files Script
# Run this after cloning the repository

echo "🔧 Setting up environment files for Device Chat PWA..."

# Check if .env files already exist
if [ -f "backend/.env" ] || [ -f "frontend/.env" ]; then
    echo "⚠️  Environment files already exist!"
    read -p "Do you want to overwrite them? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled"
        exit 1
    fi
fi

# Copy example files to .env
echo "📁 Creating backend/.env from template..."
cp backend/.env.example backend/.env

echo "📁 Creating frontend/.env from template..."
cp frontend/.env.example frontend/.env

echo ""
echo "✅ Environment files created!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit backend/.env and add your:"
echo "   - OpenAI API key (OPENAI_API_KEY)"
echo "   - VAPID keys (generate with: web-push generate-vapid-keys)"
echo "   - MongoDB URL (if different from localhost)"
echo ""
echo "2. Edit frontend/.env and add your:"
echo "   - Backend URL (REACT_APP_BACKEND_URL)"
echo ""
echo "3. Generate VAPID keys:"
echo "   npm install -g web-push"
echo "   web-push generate-vapid-keys"
echo ""
echo "4. Install dependencies:"
echo "   cd backend && pip install -r requirements.txt"
echo "   cd frontend && yarn install"
echo ""
echo "5. Start services:"
echo "   Backend: uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
echo "   Frontend: yarn start"
echo ""
echo "📚 See SETUP.md for detailed instructions"