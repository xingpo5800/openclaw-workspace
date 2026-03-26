# 心跳任务（自动运行）

> 心跳每5分钟运行一次。有事才出声，没事不打扰。

## 行情监控

- 读取 monitor_loop.log 最新一行
- 如有5%以上涨跌 → 推送
- 如金风跌破27.94 → 语音报警
- 如有新的选股命中 → 推送

## 记忆自检

- 检查 memory/2026-03-XX.md（今日记忆）是否存在
- 如不存在 → 创建今天的记录
- 检查昨日记忆是否完整

## 自我进化检查
- 读取 `~/.openclaw/skills/self-improving/heartbeat-rules.md`
- 使用 `~/self-improving/heartbeat-state.md` 记录心跳状态
- 如果没有新内容，返回 HEARTBEAT_OK

## 主动汇报

- 收盘后（15:00-15:30）自动写今日复盘
- 每晚21:00检查一次任务完成情况
