# OpenClaw iFlow Gateway 部署指南

## 🎯 部署前准备

### 系统要求
- **操作系统**: macOS 10.15+ 或 Linux
- **Python**: 3.9+
- **内存**: 最少 512MB，推荐 2GB+
- **磁盘**: 最少 1GB 可用空间
- **网络**: 需要访问 iFlow 服务

### 依赖检查
```bash
# 检查 Python 版本
python3 --version  # 需要 3.9+

# 检查 pip
pip3 --version

# 检查 Git（可选）
git --version
```

## 📦 部署方式

### 方式一：完整部署（推荐）

#### 1. 下载项目
```bash
# 如果从 Git 仓库克隆
git clone <repository-url>
cd iflow-gateway-backup

# 或者直接复制已存在的项目
cp -r /Users/kevin/.openclaw/workspace/iflow-gateway-backup /path/to/your/project
cd /path/to/your/project
```

#### 2. 一键安装
```bash
chmod +x INSTALL.sh
./INSTALL.sh
```

#### 3. 启动服务
```bash
./scripts/start-all.sh
```

#### 4. 验证部署
```bash
./scripts/test-connection.sh
```

### 方式二：手动部署

#### 1. 创建项目目录
```bash
mkdir -p iflow-gateway-deployment
cd iflow-gateway-deployment
```

#### 2. 创建虚拟环境
```bash
python3 -m venv iflow-sdk-venv
source iflow-sdk-venv/bin/activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置服务
```bash
# 复制配置文件
mkdir -p config logs
cp config/gateway.json config/gateway.json.backup

# 编辑配置（可选）
vim config/gateway.json
```

#### 5. 启动服务
```bash
# 启动 iFlow ACP
nohup iflow --experimental-acp --stream --port 8090 > logs/iflow-acp.log 2>&1 &

# 启动网关服务器
nohup python3 server-simple.py > logs/server-simple.log 2>&1 &
```

## 🚀 生产环境部署

### 使用 PM2 进程管理器

#### 1. 安装 PM2
```bash
npm install -g pm2
```

#### 2. 创建 PM2 配置文件
```json
{
  "apps": [
    {
      "name": "iflow-acp",
      "script": "iflow",
      "args": "--experimental-acp --stream --port 8090",
      "cwd": "/path/to/iflow-gateway-backup",
      "exec_mode": "fork",
      "instances": 1,
      "autorestart": true,
      "max_restarts": 10,
      "max_memory_restart": "1G",
      "log_file": "./logs/iflow-acp.log",
      "error_file": "./logs/iflow-acp.err.log",
      "out_file": "./logs/iflow-acp.out.log",
      "log_date_format": "YYYY-MM-DD HH:mm:ss Z"
    },
    {
      "name": "iflow-gateway",
      "script": "python3",
      "args": "server-simple.py",
      "cwd": "/path/to/iflow-gateway-backup",
      "exec_mode": "fork",
      "instances": 1,
      "autorestart": true,
      "max_restarts": 10,
      "max_memory_restart": "1G",
      "log_file": "./logs/server-simple.log",
      "error_file": "./logs/server-simple.err.log",
      "out_file": "./logs/server-simple.out.log",
      "log_date_format": "YYYY-MM-DD HH:mm:ss Z"
    }
  ]
}
```

#### 3. 启动服务
```bash
pm2 start ecosystem.config.json
pm2 save
pm2 startup
```

#### 4. 管理服务
```bash
# 查看状态
pm2 status

# 查看日志
pm2 logs iflow-acp
pm2 logs iflow-gateway

# 重启服务
pm2 restart all

# 停止服务
pm2 stop all
```

### 使用 Docker 部署

#### 1. 创建 Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8086 8090

# 启动命令
CMD ["python3", "server-simple.py"]
```

#### 2. 创建 docker-compose.yml
```yaml
version: '3.8'

services:
  iflow-gateway:
    build: .
    ports:
      - "8086:8086"
    environment:
      - IFLOW_HTTP_PORT=8086
      - IFLOW_ACP_PORT=8090
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - iflow-acp
    restart: unless-stopped

  iflow-acp:
    image: iflow:latest
    ports:
      - "8090:8090"
    environment:
      - IFLOW_PORT=8090
    restart: unless-stopped
```

#### 3. 构建和运行
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 🔒 安全配置

### 防火墙设置
```bash
# macOS (pfctl)
sudo pfctl -f /etc/pf.conf

# Linux (ufw)
sudo ufw allow 8086/tcp
sudo ufw allow 8090/tcp
sudo ufw enable
```

### SSL/TLS 配置
```bash
# 使用 Nginx 反向代理
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8086;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8090;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 📊 监控和告警

### 健康检查脚本
```bash
#!/bin/bash
# health-check.sh

# 检查 iFlow ACP
if ! curl -s -f http://127.0.0.1:8090/ > /dev/null; then
    echo "iFlow ACP 服务异常" | mail -s "iFlow ACP 告警" admin@example.com
fi

# 检查网关服务
if ! curl -s -f http://127.0.0.1:8086/health | grep -q "healthy"; then
    echo "网关服务异常" | mail -s "网关服务告警" admin@example.com
fi

# 检查内存使用
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}')
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "内存使用率过高: ${MEMORY_USAGE}%" | mail -s "内存告警" admin@example.com
fi
```

### 定时任务
```bash
# 添加到 crontab
crontab -e

# 每5分钟检查一次健康状态
*/5 * * * * /path/to/health-check.sh
```

## 🔄 备份和恢复

### 数据备份脚本
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/iflow-gateway"
PROJECT_DIR="/path/to/iflow-gateway-backup"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份配置文件
cp -r $PROJECT_DIR/config $BACKUP_DIR/config_$DATE

# 备份日志文件
cp -r $PROJECT_DIR/logs $BACKUP_DIR/logs_$DATE

# 备份虚拟环境
tar -czf $BACKUP_DIR/venv_$DATE.tar.gz -C $PROJECT_DIR iflow-sdk-venv

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "*" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR/"
```

### 恢复流程
```bash
# 1. 停止服务
./scripts/stop-all.sh

# 2. 恢复配置
cp -r /backups/iflow-gateway/config_20240321_120000 /path/to/iflow-gateway-backup/config

# 3. 恢复虚拟环境
tar -xzf /backups/iflow-gateway/venv_20240321_120000.tar.gz -C /path/to/iflow-gateway-backup/

# 4. 重启服务
./scripts/start-all.sh
```

## 🚀 升级和维护

### 版本升级
```bash
# 1. 备份当前版本
./backup.sh

# 2. 停止服务
./scripts/stop-all.sh

# 3. 更新代码
git pull origin main
# 或者手动替换文件

# 4. 更新依赖
source iflow-sdk-venv/bin/activate
pip install -r requirements.txt

# 5. 重启服务
./scripts/start-all.sh
```

### 定期维护
```bash
# 清理日志
find logs/ -name "*.log" -mtime +30 -delete

# 清理缓存
rm -rf cache/*

# 更新系统
sudo apt update && sudo apt upgrade
```

---

**部署指南完成**  
**最后更新**: 2026-03-21