# 技能速查（8个核心技能）

> 每次遇到对应场景，直接查阅，不要凭印象。

---

## 1. find-skills
**什么时候用：** 毅哥说"有没有能做X的技能"，或者想找新能力时。
**怎么用：** 读 SKILL.md，用 clawhub CLI 搜索安装。

---

## 2. py
**什么时候用：** 写Python代码前/后。
**核心规则：**
- ❌ `def f(items=[])` → ✅ `def f(items=None): items=items or []`
- ❌ `except:` → ✅ `except Exception:`
- ❌ float算钱 → ✅ `Decimal`
- ❌ 遍历时改list → ✅ `for x in list(items):`

---

## 3. todo-skill
**什么时候用：** 大任务来了，先拆再干。
**流程：** 输入→拆子任务→优化顺序→执行→调整→输出
**触发词：** "Plan and execute [任务]"

---

## 4. gh
**什么时候用：** 操作GitHub仓库/PR/issue。
**核心命令：**
```bash
gh auth status          # 检查登录
gh issue list          # 列出issue
gh issue create        # 创建issue
gh pr create           # 创建PR
gh pr merge            # 合并PR
```

---

## 5. git-cli
**什么时候用：** 日常Git操作（比gh更底层）。
**核心命令：**
```bash
git status             # 看改动
git diff               # 看差异
git add / git commit   # 提交
git branch / checkout  # 分支
git stash              # 暂存
```

---

## 6. tavily-search
**什么时候用：** Brave搜索不可用时，做网络搜索。
**要求：** 需要 TAVILY_API_KEY（在 ~/.openclaw/.env 里配置）
**用法：** 读 SKILL.md 后用 `tavily-search.sh` 脚本

---

## 7. agent-browser
**什么时候用：** 网页复杂交互，鼠标点击、表单填写、截图等。
**核心：** 无头浏览器 + 辅助功能树定位元素
**命令：** `agent-browser` CLI

---

## 8. cli-anything
**什么时候用：** 想用命令行自动化某个GUI软件/工具。
**流程：** 输入软件路径或GitHub地址 → 生成Python harness → 自动运行
**要求：** 需要读 HARNESS.md 规范

---

## 当前安装状态

| 技能 | 状态 | 备注 |
|------|------|------|
| find-skills | ✅ 可用 | workspace/skills/ |
| py | ✅ 可用 | workspace/skills/ |
| todo-skill | ✅ 可用 | workspace/skills/ |
| gh | ⚠️ 需gh认证 | 已登录github.com |
| git-cli | ✅ 可用 | workspace/skills/ |
| tavily-search | ✅ 可用 | API key已配置，SSL已修复 |
| agent-browser | ✅ 可用 | 系统Chrome即可，无需下载Chromium |
| cli-anything | ✅ 可用 | ~/.openclaw/skills/ |

---

*更新时间：2026-03-26*
