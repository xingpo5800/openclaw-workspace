# 知识地图

> 这是AI的"大脑目录"。每次新session启动后读此文件，快速建立全局观。

## 一、我的基本信息

| 属性 | 值 |
|------|-----|
| 姓名 | 灵犀 |
| 主人 | 毅哥 |
| 类型 | AI助手 |
| 工作区 | ~/.openclaw/workspace |

## 二、知识库（knowledge/）

### stock/ 股票分析知识库
理论体系：
- `01-dow-theory.md` — 道氏理论
- `02-elliott-wave.md` — 波浪理论
- `03-chan-theory.md` — 缠论核心概念
- `蜡烛图深度.md` — 日本蜡烛图技术（356页）
- `蜡烛图量价.md` — 蜡烛图量价关系
- `股市认知框架.md` — 宏观+技术分析框架

实战笔记：
- `chan-reading-2026-03-25.md` — 缠论全书笔记（713页）
- `操盘之神读书笔记.md` — 《操盘之神》笔记（612页）
- `candle-chan-integration-2026-03-25.md` — 蜡烛图×缠论整合框架
- `2026-03-23-实战经验沉淀.md` — 实战经验

量化系统：
- `内部量化标准.md` — 四维打分体系（缠论/蜡烛图/量价/真技术）

## 三、项目（projects/）

### 股票分析系统
代码：
- `chan_core.py` — 缠论核心算法v3.0（K线包含/分型/笔/中枢/背驰）
- `chan.py` — 缠论分析主程序
- `quant_system.py` — 量化系统
- `monitor.py` — 行情监控
- `market_hot.py` — 强势股筛选
- `stock_monitor.py` — 股票监控

数据文件：
- `portfolio.json` — 追踪股票池
- `holdings.json` — 持仓记录
- `signals.json` — 信号记录
- `analysis.json` — 分析结果
- `backtest.json` — 回测记录
- `tracking-pool.md` — 追踪池详情

系统设计：
- `个股技术诊断系统设计.md`
- `网页版股票诊断系统设计.md`
- `系统愿景.md`

### 外部
- `books/` — PDF书籍（缠论/蜡烛图/操盘之神）
- `media/` — 媒体文件归档
- `docs/` — 历史文档

## 四、规则体系（rules/）

共13个规则文件，4级层级：

| 层级 | 文件 |
|------|------|
| 最高 | 核心规则.md |
| 高 | 审查规则.md |
| 中 | system-rules.md |
| 低 | session-rules.md、执行感知.md、file-management.md、学习边界.md、task-management.md、token-saver.md、rule-creation.md、animation-script.md、备份规则.md、rules-index.md |

**六问速查：**
- 这是规则问题吗？→ 审查规则.md
- 要修改/创建规则吗？→ rule-creation.md
- 怎么执行任务？→ session-rules.md
- 执行中发现问题？→ 执行感知.md
- 学的东西对不对？→ 学习边界.md
- 记忆/规则要更新？→ system-rules.md

## 五、记忆系统（memory/）

每日记忆：`2026-03-XX.md`（每日一份）

专项记忆：
- `MEMORY.md` — 总索引
- `rules-index.md` — 规则索引
- `knowledge-map.md` — 知识地图（本文）
- `SUMMARY.md` — 记忆目录索引
- `core-memory.md` — 核心记忆
- `core-trigger.md` — 核心触发词
- `today.md` — **工作状态追踪（新session必读）**
- `predictions.md` — **预判追踪记录**
- `训练规划.md` — 训练方向
- `进化规划.md` — 进化路径

## 六、任务系统（tasks/）

- `task-center.md` — 任务中心
- `todo/` — 待执行
- `done/` — 已完成（含勋章记录）
- `doing/` — 进行中

## 七、脚本系统（scripts/）

核心脚本：
- `workspace-cleanup.sh` — 临时文件清理（每两天）
- `smart-reminder.sh` — 智能提醒
- `tavily-search.sh` — 搜索
- `rule-check.sh` — 规则检查

自动化：
- `auto-backup.sh` — 自动备份
- `github-auto-backup.sh` — GitHub备份

## 八、GitHub项目

| 项目 | 地址 |
|------|------|
| 缠论分析系统 | https://github.com/xingpo5800/chan-analysis |
| Workspace备份 | https://github.com/xingpo5800/openclaw-workspace |

## 九、当前核心能力（2026-03-25）

### 量化分析体系（四维共振）
1. **缠论**：笔/段/中枢/背驰/买卖点
2. **蜡烛图**：单根反转/吞没/星线/孕线/早晨黄昏之星
3. **量价**：平量/倍量/巨量/量能斜率
4. **真技术**（操盘之神）：概率思维+成本分析+风控前置+级别仓位匹配

### 核心策略
- **5日均量上穿60日均量策略**：slope>30 + RSI<52，成功率70%+
- **四维打分**：每只股票结构/形态/能量/心法各10分
- **多级别联立**：日线→30分钟→15分钟区间套

### 已追踪股票
详见 projects/股票分析系统/tracking-pool.md

## 十、启动流程

1. SOUL.md → 个性设定
2. USER.md → 用户信息
3. 今日+昨日记忆 → 最近动态
4. MEMORY.md → 总索引
5. **knowledge-map.md** → 知识地图（快速定位文件）
6. 相关SUMMARY.md → 定向读取

---

*更新时间：2026-03-26 07:37*
