#!/bin/bash

# AI Portfolio Dashboard Deployment Script
# Choose your deployment platform

echo "🚀 AI Portfolio Dashboard Deployment"
echo "=================================="
echo ""
echo "Choose your deployment platform:"
echo "1. Railway (Recommended - Easiest)"
echo "2. Render (Free tier available)"
echo "3. Heroku (Classic platform)"
echo "4. DigitalOcean (Professional)"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🚂 Deploying to Railway..."
        echo "1. Go to https://railway.app"
        echo "2. Sign up and connect GitHub"
        echo "3. Select your repository"
        echo "4. Railway will auto-deploy!"
        echo "5. Add custom domain in Railway dashboard"
        ;;
    2)
        echo "🎨 Deploying to Render..."
        echo "1. Go to https://render.com"
        echo "2. Sign up and connect GitHub"
        echo "3. Create new Web Service"
        echo "4. Select your repository"
        echo "5. Use these settings:"
        echo "   - Build Command: pip install -r requirements.txt"
        echo "   - Start Command: python run_production.py"
        echo "6. Deploy and add custom domain"
        ;;
    3)
        echo "🟣 Deploying to Heroku..."
        echo "1. Install Heroku CLI"
        echo "2. Run: heroku login"
        echo "3. Run: heroku create your-app-name"
        echo "4. Run: git push heroku main"
        echo "5. Run: heroku open"
        ;;
    4)
        echo "🌊 Deploying to DigitalOcean..."
        echo "1. Go to https://cloud.digitalocean.com"
        echo "2. Create new App Platform"
        echo "3. Connect GitHub repository"
        echo "4. Configure build settings"
        echo "5. Deploy and add domain"
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment instructions provided!"
echo "📖 For detailed steps, see DEPLOYMENT_GUIDE.md"
echo "🌐 Your dashboard will be live with a custom domain!"
