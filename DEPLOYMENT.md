# 🍅 Tomato AI Deployment Guide

This guide provides multiple deployment options for your Tomato Ripeness & Disease Checker application.

## 📋 Prerequisites

- Python 3.8+ installed
- Docker and Docker Compose (for containerized deployment)
- Git (for cloning to remote servers)
- Basic knowledge of command line

## 🚀 Deployment Options

### Option 1: Local Development (Quick Start)

```bash
# 1. Navigate to project directory
cd "c:\CODING\Tomato AI Final"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py --server.headless true
```

**Access:** http://localhost:8501

---

### Option 2: Docker Deployment (Recommended)

#### Method A: Using Docker Compose (Easiest)

```bash
# 1. Build and run with Docker Compose
docker-compose up --build

# 2. Run in background
docker-compose up -d --build

# 3. Stop the container
docker-compose down
```

#### Method B: Using Docker directly

```bash
# 1. Build the image
docker build -t tomato-ai .

# 2. Run the container
docker run -p 8501:8501 -v $(pwd)/user_scans:/app/user_scans tomato-ai

# 3. Run in background
docker run -d -p 8501:8501 -v $(pwd)/user_scans:/app/user_scans --name tomato-ai-app tomato-ai
```

**Access:** http://localhost:8501

---

### Option 3: Cloud Deployment

#### A. Streamlit Community Cloud (Easiest Cloud Option)

1. **Create a GitHub repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/tomato-ai.git
   git push -u origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Set main file to `app.py`
   - Click Deploy

#### B. Heroku

1. **Install Heroku CLI** and login:
   ```bash
   heroku login
   ```

2. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```

3. **Create Procfile**:
   ```bash
   echo "web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile
   ```

4. **Deploy**:
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

#### C. AWS EC2

1. **Launch EC2 instance** (t2.micro or larger)
2. **Connect via SSH**:
   ```bash
   ssh -i your-key.pem ec2-user@your-ec2-ip
   ```

3. **Setup environment**:
   ```bash
   sudo yum update -y
   sudo yum install python3 python3-pip git -y
   pip3 install --user streamlit
   ```

4. **Clone and run**:
   ```bash
   git clone your-repo-url
   cd tomato-ai
   pip3 install -r requirements.txt
   streamlit run app.py --server.address=0.0.0.0
   ```

#### D. Google Cloud Platform

1. **Create VM instance** in Google Cloud Console
2. **SSH into instance**
3. **Setup Docker** (recommended):
   ```bash
   sudo apt-get update
   sudo apt-get install docker.io docker-compose -y
   sudo usermod -aG docker $USER
   ```
4. **Deploy with Docker**:
   ```bash
   git clone your-repo-url
   cd tomato-ai
   docker-compose up -d
   ```

---

### Option 4: Production Deployment with Nginx (Advanced)

#### Setup with Nginx Reverse Proxy

1. **Install Nginx**:
   ```bash
   sudo apt update
   sudo apt install nginx -y
   ```

2. **Create Nginx config** (`/etc/nginx/sites-available/tomato-ai`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Enable site**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/tomato-ai /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. **Run app with systemd service**:
   ```bash
   sudo nano /etc/systemd/system/tomato-ai.service
   ```

   ```ini
   [Unit]
   Description=Tomato AI App
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/tomato-ai
   ExecStart=/usr/local/bin/streamlit run app.py --server.headless true
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   sudo systemctl enable tomato-ai
   sudo systemctl start tomato-ai
   ```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file for production:

```bash
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
```

### Security Considerations

1. **Change default passwords** in authentication system
2. **Use HTTPS** in production (Let's Encrypt recommended)
3. **Regularly update dependencies**
4. **Backup user data** (`users_db.json`, `scan_history.json`)
5. **Monitor logs** for suspicious activity

### Performance Optimization

1. **Use GPU** if available for faster model inference
2. **Implement caching** for model loading
3. **Use CDN** for static assets
4. **Optimize image sizes** before processing

---

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Find process using port 8501
   netstat -tulpn | grep :8501
   # Kill the process
   sudo kill -9 <PID>
   ```

2. **Model loading errors**:
   - Ensure `.pt` files are in the correct directory
   - Check file permissions

3. **Docker build fails**:
   - Check Dockerfile syntax
   - Ensure all files are copied correctly

4. **Memory issues**:
   - Increase server RAM
   - Use lighter models or quantization

### Logs

- **Streamlit logs**: Check console output
- **Docker logs**: `docker-compose logs -f`
- **Nginx logs**: `/var/log/nginx/error.log`

---

## 📊 Monitoring

### Health Checks

The app includes a health check endpoint at `/_stcore/health`

### Monitoring Tools

- **Uptime monitoring**: UptimeRobot, Pingdom
- **Performance**: New Relic, DataDog
- **Error tracking**: Sentry

---

## 🔄 Updates and Maintenance

### Updating the App

1. **Backup data**:
   ```bash
   cp users_db.json users_db.json.backup
   cp scan_history.json scan_history.json.backup
   ```

2. **Update code**:
   ```bash
   git pull origin main
   ```

3. **Update dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

4. **Restart service**:
   ```bash
   sudo systemctl restart tomato-ai
   # or
   docker-compose restart
   ```

### Backup Strategy

- **Daily backups** of user data
- **Weekly full backups** including models
- **Version control** for code changes

---

## 📞 Support

For deployment issues:
1. Check this guide first
2. Review application logs
3. Check GitHub issues
4. Contact your hosting provider if needed

---

**🎉 Congratulations! Your Tomato AI app is now ready for production deployment!**
