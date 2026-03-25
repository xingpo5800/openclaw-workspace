# TOOLS-CN.md - 本地配置

技能定义工具的使用方法，此文件记录你的特定配置。

## TTS语音
- macOS内置中文语音: Ting-Ting
- 命令: say -v "Ting-Ting" "文本内容"
- 可用于朗读报告、提醒等

## 记录内容

- 摄像头名称和位置
- SSH主机和别名
- TTS语音偏好
- 扬声器/房间名称
- 设备昵称
- 环境特定信息

## SSH连接

- 小智：ssh xiaozhi（已配置，~/.ssh/config）
- 小智服务器：kevin@192.168.8.171（密码：zyyp@ssw0rd）
- 连接命令：sshpass -p 'zyyp@ssw0rd' ssh kevin@192.168.8.171
- 小智工作目录：~/.openclaw/workspace/stock
- 小智记忆目录：~/.openclaw/workspace/memory/

## 作用

技能是共享的，你的配置是私有的。分开保存可以更新技能时不丢失配置，共享技能时不泄露基础设施信息。

添加任何有助于工作的内容，这是你的备忘录。
