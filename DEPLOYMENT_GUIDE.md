# 🌐 MCP Chat Interface - Deployment Guide

Deploy your MCP Chat Interface to the cloud and share it with anyone worldwide!

## 🚀 Quick Deploy Options (Free)

### Option 1: Railway.app (Recommended - Free Tier)
1. **Sign up** at [railway.app](https://railway.app) with GitHub
2. **Click** "Deploy from GitHub repo"
3. **Connect** your GitHub repo or upload these files
4. **Auto-deploy** - Railway will detect the `railway.json` and deploy automatically
5. **Get URL** - Railway provides a public URL like `https://your-app.railway.app`

### Option 2: Render.com (Free Tier)
1. **Sign up** at [render.com](https://render.com)
2. **Create** a new Web Service
3. **Connect** your GitHub repo
4. **Settings**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python3 web_chat_interface.py`
   - Health Check Path: `/api/health`
5. **Deploy** and get your public URL

### Option 3: Heroku (Free tier discontinued, but instructions for reference)
```bash
# Install Heroku CLI
# Create Procfile
echo "web: python3 web_chat_interface.py" > Procfile

# Deploy
heroku create your-mcp-chat
git push heroku main
```

### Option 4: Vercel (Serverless)
1. **Install** Vercel CLI: `npm i -g vercel`
2. **Deploy**: `vercel --prod`
3. **Auto-configure** with `vercel.json` (create if needed)

## 📁 Required Files for Deployment

Ensure these files are in your project:

```
├── web_chat_interface.py      # Main application
├── workbench_role_manager.py  # Role management
├── models.py                  # Database models
├── ops_center.db             # SQLite database
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container config
├── railway.json            # Railway config
├── render.yaml            # Render config
└── templates/
    └── chat.html          # Generated automatically
```

## 🔧 Environment Variables

Most platforms support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8080 | Port number |
| `HOST` | 0.0.0.0 | Host address |
| `MCP_SERVER_URL` | http://localhost:8000 | MCP server URL |

## 🌐 Step-by-Step: Railway Deployment

### Step 1: Prepare Your Code
```bash
# Make sure all files are ready
ls -la
# Should show: web_chat_interface.py, requirements.txt, railway.json, etc.
```

### Step 2: Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway auto-detects Python and deploys

### Step 3: Get Your Public URL
- Railway provides: `https://your-app-name.railway.app`
- Share this URL with anyone!

## 🐳 Docker Deployment

### Local Docker Test
```bash
# Build image
docker build -t mcp-chat .

# Run container
docker run -p 8080:8080 mcp-chat

# Test
curl http://localhost:8080/api/health
```

### Deploy to Cloud with Docker
```bash
# Push to Docker Hub
docker tag mcp-chat your-dockerhub/mcp-chat
docker push your-dockerhub/mcp-chat

# Deploy to any cloud that supports Docker
```

## 🔒 Security for Production

### Basic Security Setup
```python
# Add to web_chat_interface.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Environment Variables for Security
```bash
# Add these to your cloud platform
ALLOWED_ORIGINS=https://yourdomain.com
SECRET_KEY=your-secret-key-here
```

## 📱 Free Cloud Platforms Comparison

| Platform | Free Tier | Custom Domain | Always On | Deploy Time |
|----------|-----------|---------------|-----------|-------------|
| **Railway** | 500 hours/month | ✅ | ❌ (sleeps) | ~2 min |
| **Render** | 750 hours/month | ✅ | ❌ (sleeps) | ~3 min |
| **Fly.io** | 3 VMs free | ✅ | ✅ | ~2 min |
| **Heroku** | No longer free | ✅ | ❌ | ~3 min |

## 🚀 Quick Deploy Commands

### Railway (Easiest)
```bash
# Install Railway CLI (optional)
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Render
```bash
# Just push to GitHub and connect via Render dashboard
git add .
git commit -m "Deploy MCP Chat"
git push origin main
```

### Fly.io
```bash
# Install flyctl
# Sign up at fly.io
flyctl launch
flyctl deploy
```

## 🌍 Share Your Deployment

Once deployed, share your public URL:

### Example URLs:
- Railway: `https://mcp-chat-production.railway.app`
- Render: `https://mcp-chat.onrender.com`
- Fly.io: `https://mcp-chat.fly.dev`

### Share Message Template:
```
🤖 MCP Chat Interface is live!

Access here: https://your-app.railway.app

Available commands:
• help - Show all commands
• agents - List agents
• workbenches - Show workbenches
• roles 1 - View Dispute roles
• coverage - Role coverage report

Try typing "help" to get started!
```

## 🛠️ Troubleshooting

### Common Issues:

**Build Fails**
- Check `requirements.txt` has correct dependencies
- Ensure Python 3.8+ is specified

**App Won't Start**
- Verify `PORT` environment variable is set
- Check health endpoint: `/api/health`

**Database Issues**
- SQLite database should be included in deployment
- Check file permissions

**WebSocket Issues**
- Ensure platform supports WebSockets
- Check CORS settings for production

### Debug Commands:
```bash
# Check health
curl https://your-app.railway.app/api/health

# Test WebSocket (using websocat if installed)
websocat wss://your-app.railway.app/ws/test

# Check logs (Railway)
railway logs
```

## 📊 Monitoring Your Deployment

### Health Checks
Your app includes a health endpoint at `/api/health`:
```json
{
  "status": "healthy",
  "mcp_available": false,
  "workbench_manager_available": true,
  "deployment": "cloud",
  "timestamp": "2025-01-27T12:00:00"
}
```

### Usage Analytics
Most platforms provide:
- Request logs
- Performance metrics
- Error monitoring
- Uptime tracking

## 🎯 Next Steps

After deployment:
1. **Test** all features work correctly
2. **Share** the URL with your team
3. **Monitor** usage and performance
4. **Scale** if needed (upgrade to paid tiers)
5. **Customize** branding and features

## 💡 Pro Tips

- **Custom Domain**: Most platforms allow custom domains
- **SSL**: HTTPS is included automatically
- **Scaling**: Start with free tier, upgrade as needed
- **Backups**: Keep your database backed up
- **Updates**: Push to GitHub to auto-deploy updates

---

**Happy Deploying! 🚀**

Your MCP Chat Interface will be accessible worldwide once deployed!