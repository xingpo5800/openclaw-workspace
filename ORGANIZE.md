# OpenClaw 工作区组织结构

## 总索引

MEMORY.md 是总入口，指向各目录的SUMMARY.md

## 目录结构

| 目录 | 内容 | 索引 |
|------|------|------|
| memory/ | 每日记忆+专项记忆 | memory/SUMMARY.md |
| knowledge/ | 独立理论知识（道氏/波浪/缠论/蜡烛图） | knowledge/SUMMARY.md |
| projects/ | 完整项目（程序+设计+数据+配置） | projects/SUMMARY.md |
| tasks/ | 任务管理 | tasks/SUMMARY.md |
| scripts/ | 脚本工具 | scripts/SUMMARY.md |
| rules/ | 规则系统 | rules-index.md |

## 基础设施目录
LocalAI/ | akshare/ | akshare-env/ | books/ | fonts/ | security/ | skills/ | iflow-gateway-backup/

## 核心配置（根目录）
SOUL.md / USER.md / IDENTITY.md / AGENTS.md / MEMORY.md / TOOLS.md / HEARTBEAT.md / ORGANIZE.md

## 索引机制
每个一级目录有SUMMARY.md，记录该目录下所有文件的内容摘要。
任务/知识/项目完成后 → 文件归位 → 更新对应SUMMARY.md。

## 记忆加载流程
1. 读取SOUL.md、USER.md、IDENTITY.md、AGENTS.md
2. 读取MEMORY.md（总索引）
3. 读取memory/YYYY-MM-DD.md（今日记忆）
4. 按需查找：MEMORY.md → 对应SUMMARY.md → 具体文件

*更新时间：2026-03-25*
