# GitHub自动备份配置指南

## 🎯 配置目标
实现真正的全自动备份：本地备份 + GitHub远程备份

## 🔧 配置步骤

### 1. 创建GitHub仓库
1. 登录GitHub
2. 创建新仓库：`openclaw-backup`
3. 设置为私有（推荐）
4. 不要初始化README（我们会自动添加）

### 2. 生成GitHub Personal Access Token
1. 进入 GitHub → Settings → Developer settings → Personal access tokens
2. 点击 "Generate new token"
3. 设置token名称：`OpenClaw Auto Backup`
4. 设置过期时间：建议90天
5. 勾选权限：
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
6. 点击 "Generate token"
7. **立即复制token**，关闭页面后将无法再次查看

### 3. 配置备份脚本
编辑 `/Users/kevin/.openclaw/workspace/scripts/github-auto-backup.sh`：

```bash
# 修改这两行：
GITHUB_REPO="your-username/openclaw-backup"  # 替换为你的用户名和仓库名
GITHUB_TOKEN="your-github-token"  # 替换为刚才生成的token
```

### 4. 测试GitHub备份
```bash
# 测试GitHub备份功能
/Users/kevin/.openclaw/workspace/scripts/github-auto-backup.sh
```

### 5. 更新定时任务
编辑 `/Users/kevin/.openclaw/backup.plist`，将脚本路径改为完整备份脚本：

```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/kevin/.openclaw/workspace/scripts/full-auto-backup.sh</string>
</array>
```

然后重新加载：
```bash
launchctl unload /Users/kevin/.openclaw/backup.plist
launchctl load /Users/kevin/.openclaw/backup.plist
```

## 🚀 自动化流程

### 每日执行流程
1. **凌晨2:00**：启动完整备份脚本
2. **本地备份**：备份到 `/Volumes/data-backup/openclawbackup/`
3. **GitHub备份**：自动推送到GitHub仓库
4. **清理旧备份**：删除7天前的本地备份
5. **记录日志**：详细记录备份过程

### 备份内容
- ✅ 配置文件 (openclaw.json)
- ✅ 记忆系统 (memory/)
- ✅ 规则文件 (rules/)
- ✅ 任务管理 (tasks/)
- ✅ 脚本工具 (scripts/)
- ✅ 日志文件 (logs/, 最近7天)

## 🔒 安全说明

### Token安全
- Token具有读写权限，请妥善保管
- 建议设置较短的有效期
- 不要在代码中硬编码token，使用环境变量更安全

### 备份安全
- 本地备份：防止硬件故障
- GitHub备份：防止灾难性丢失
- 7天保留期：平衡空间和数据安全

## 🐛 故障排除

### 常见问题
1. **认证失败**
   - 检查GitHub token是否正确
   - 检查token是否过期
   - 检查仓库权限

2. **网络问题**
   - 检查网络连接
   - 检查防火墙设置
   - 检查代理配置

3. **空间不足**
   - 检查GitHub仓库大小限制
   - 检查本地磁盘空间

### 日志查看
```bash
# 查看最新备份日志
tail -f /Users/kevin/.openclaw/workspace/logs/full-backup-$(date +%Y-%m-%d).log

# 查看所有备份日志
ls -la /Users/kevin/.openclaw/workspace/logs/backup-*.log
```

## 📊 备份状态监控

### 检查备份状态
```bash
# 检查本地备份
ls -la /Volumes/data-backup/openclawbackup/

# 检查GitHub仓库
cd /Volumes/data-backup/openclawbackup/backup-$(date +%Y-%m-%d)
git log --oneline -5
```

### 备份统计
- 本地备份大小：`du -sh /Volumes/data-backup/openclawbackup/`
- 文件数量：`find /Volumes/data-backup/openclawbackup/ -type f | wc -l`
- GitHub仓库大小：查看GitHub仓库页面

---

**配置完成后的效果：真正的全自动备份！** 🎉