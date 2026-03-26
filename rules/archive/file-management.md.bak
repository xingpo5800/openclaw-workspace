# 文件管理规则

## 根目录原则

根目录只允许：
- 核心配置文件：SOUL.md / USER.md / IDENTITY.md / AGENTS.md / MEMORY.md / TOOLS.md / HEARTBEAT.md / ORGANIZE.md
- 功能目录：memory/ / rules/ / projects/ / stock/ / scripts/ / tasks/ / knowledge/ / tools/ 等

临时文件、测试文件、截图、历史文档**一律禁止**放在根目录。

## 临时文件规则

**test_*.py / tmp_*.jpg / v*s.png / frame_*.jpg 等临时文件**

- 创建后当天清理，或由定时任务每两天自动清理
- 测试完毕 = 文件作废，不是归档
- 养成"做事收尾"的习惯，不是做事不管
- 定时任务：每两天03:00自动清理（scripts/workspace-cleanup.sh），保留48小时后悔窗口

## 媒体文件规则

截图、生成图、测试图统一归入 projects/media/

命名格式：{项目}_{类型}_{序号}.{ext}
- projects/media/stock_chart_001.png
- projects/media/pix_01.png
- projects/media/debug_01.png

## 大文件规则

超过10MB的文件：
- 立即归入projects/media/或对应项目目录
- 不放在根目录

## 项目文件规则

项目相关文件放在对应项目目录下，不在根目录散落。

## Session结束检查

每次Session结束前检查根目录：
- 有无临时文件残留
- 有无超过7天的媒体文件未清理
- 有无不在归定位置的文件

## 违反处理

违反以上规则 = 执行有偏差，发现即修正，不需要等毅哥提醒。
