# PDF Q&A App - Ngrok Setup Guide

## 🚀 Quick Start

### Step 1: Get Your Ngrok Auth Token
1. Go to: https://dashboard.ngrok.com/signup
2. Sign up for free account
3. Copy your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken

### Step 2: Configure Ngrok (One-time setup)
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```
Replace `YOUR_AUTH_TOKEN_HERE` with your actual token.

### Step 3: Launch Your Public App
Simply double-click: **`start-ngrok.bat`**

Or run from command line:
```bash
start-ngrok.bat
```

## 🔗 What You'll Get

After running the script, you'll see:
```
ngrok

Session Status                online
Forwarding                    https://abc123-def-456.ngrok.io -> http://localhost:5000
```

**Share this HTTPS URL with anyone!** 🌐

## 📱 Features Available

✅ Upload PDF documents  
✅ Ask questions about PDF content  
✅ AI-powered document analysis  
✅ Real-time Q&A interface  
✅ Mobile-friendly design  

## 🔧 Manual Commands

If you prefer manual control:

```bash
# Start Docker container
docker-compose up -d

# Create ngrok tunnel
ngrok http 5000

# Stop everything
docker-compose down
```

## 🔄 Restart Process

To restart your public app:
1. Close ngrok (Ctrl+C)
2. Run `start-ngrok.bat` again

## 📊 Monitor Usage

- **Ngrok dashboard**: http://127.0.0.1:4040
- **App logs**: `docker-compose logs -f`

## ⚠️ Important Notes

- **Free ngrok**: URL changes each restart
- **Session limit**: 4 hours on free plan
- **For permanent URLs**: Consider paid ngrok or deploy to cloud platforms

## 🆘 Troubleshooting

**App not loading?**
```bash
# Check if container is running
docker-compose ps

# View logs
docker-compose logs -f

# Restart container
docker-compose restart
```

**Ngrok connection issues?**
```bash
# Test local app first
curl http://localhost:5000

# Verify ngrok auth
ngrok config check
```

## 🔗 Alternative: Permanent Hosting

For permanent public links, consider:
- **Cloud Platforms**: Various free tiers available (Heroku, Railway, etc.)
- **Railway**: Free tier available  
- **Ngrok Pro**: Custom domains

---

**Happy sharing! 🎉**
