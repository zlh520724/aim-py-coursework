# AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块

> **全部题目、规范、评分、提交见 [题面.pdf](题面.pdf)。** 本 README 只讲怎么把环境跑起来；没在这里出现的规格细节，一律以题面为准。

## 1. 环境要求

- Python 3.8+，仅标准库（不允许第三方运行时依赖）；
- 开发工具只需 `pytest`（测试）与 `autopep8`（风格，CI 会检查）；
- VS Code 打开仓库会推荐安装 `ms-python.autopep8` 插件（`.vscode/extensions.json`），保存即格式化即可过风格检查。

## 2. 快速开始

```bash
# 1. 用 GitHub 的 Use this template 创建你自己的仓库，然后 clone
git clone https://github.com/<你的用户名>/<你的仓库>.git
cd <你的仓库>   # 直接在 main 分支上开发

# 创建虚拟环境

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. 装依赖
python -m pip install pytest autopep8

# 3. 启用 AI 会话归档钩子（课程要求，见下方第 3 节）
python -m pip install 'agent-session-commit[pre-commit]==0.1.3' -i https://pypi.org/simple
agent-session-commit install --pre-commit   # 交互选择你的 AI 助手与会话目录

# 4. 跑测试（刚到手：全部 skip，CI 是绿的）
python -m pytest

# 5. 看演示
python main.py

# 6. 打开 题面.pdf 读题，开始实现 src/main/__init__.py 里的 TODO
```

## 3. AI 会话归档（pre-commit）

本课程允许使用 AI，提交的 commit 需要携带 AI 会话归档作为透明化记录：每次 `git commit` 后，钩子会把新增会话自动 amend 进同一个提交（`.agent-sessions/bundles/`），不产生额外的归档提交。支持 Claude Code、OpenAI Codex CLI、GitHub Copilot CLI、Qoder、ZCode、Trae、Tencent CodeBuddy 等（完整名单见 [AgentLedger](https://github.com/Gentle-Lijie/AgentLedger)）。

- 配置是仓库本地的：每个 clone 运行一次 `agent-session-commit install --pre-commit`，方向键选择 agent、确认其会话目录即可；
- 不想用 TUI 可手动配置：`git config --local agent-session.agent claude`、`git config --local agent-session.source "<会话目录>"`，然后 `python -m pip install 'pre-commit>=3.2.0' && pre-commit install`；
- 归档是普通 Git 内容且会推送到公开仓库——不要在 AI 会话里粘贴令牌等敏感信息；
- 换了 agent 或目录就重跑一次安装命令；卸载：从 `.pre-commit-config.yaml` 移除该条目后重跑 `pre-commit install`。

## 4. 本地开发循环

- **写代码**：全部作业在 `src/main/__init__.py`，按题面各题规范补全每个标有 TODO 的函数；注释里标注了对应的题面主题，推荐顺序 Q1 → Q6。
- **跑测试**：`python -m pytest` —— 可见测试是规格书的一部分，未实现的函数自动 skip，实现一个、对应测试亮一个。本地全绿 ≠ 满分（见题面）。
- **看演示**：`python main.py`（等价于 `PYTHONPATH=src python -m main`），随实现进度逐段点亮，不进测试。
- **Q6 自测**：`python tools/run_seeds.py --q6`（200 张固定地图统计），单 seed 渲染 `python tools/run_seeds.py --q6 --seed <N> --render`，Bonus 模式 `python tools/run_seeds.py --bonus`。

## 5. 仓库结构（哪些能改）

| 路径 | 说明 | 能否修改 |
|---|---|---|
| `src/main/__init__.py` | 你的全部作业（TODO 所在） | ✅ |
| `README.md` | 仅末尾两个"你来写"小节 | ✅ |
| `题面.pdf` | 题面（唯一规格说明） | ❌ 勿改 |
| `src/main/legacy_patrol.py` | Q7 模块（与主体同步发布，修复其缺陷） | Q7 时 ✅ |
| `.pre-commit-config.yaml` | AI 会话归档钩子配置 | ❌ 勿改 |
| `src/tests/`、`tools/`、`.github/`、`conftest.py`、`pytest.ini`、`main.py` | 测试与基础设施 | ❌ 勿改 |

CI 只允许修改 `src/main/**`、`README.md` 与 `.agent-sessions/**`（AI 会话归档）——其余文件改了直接红；autopep8 `--diff` 非空即败。提交方式（push、问卷、commit 粒度）见题面"提交与验收"一节。

## 读题笔记（你来写）

- Q1 需要实现血量百分比计算和机器人状态报告。
- 电量低于 20 为 LOW，20 至不足 60 为 WARNING，60 及以上为 OK。
- 状态报告需要严格满足字段宽度、对齐和分隔符要求。

## 实现与自测记录（你来写）

### Q7 六处缺陷分析

以下分析依据函数契约、初始版本与修复版本的差异，以及本地验证结果；
没有根据提交说明中的 `fix` 标签判断代码正确性。

1. **路线统计的单位不一致**
   - 定位：`segment_length_cm` 返回厘米，但 `total_route_meters` 将累计值直接作为米返回。
     路径 `(0, 0) → (3, 0) → (3, 4)` 原先得到 700，契约要求 7 米。
   - 修复：保留单段厘米计算，在累计结果返回前除以 100。
   - 验证：路线长度测试通过；单段函数仍按厘米返回。

2. **脏事件日志可能抛出异常**
   - 定位：原实现直接调用 `line.strip()`，非字符串输入会失败；
     `isdigit()` 为真也不保证可由 `int()` 解析，例如上标数字 `²`。
   - 修复：先校验字符串类型，对整数转换的 `ValueError` 返回 `None`；
     仍拒绝未知事件类型、错误字段数量和非法计数。
   - 验证：事件解析测试通过，并补查非字符串和 `MOVE,²` 均返回 `None`。

3. **没有正样本时将 None 用于数值运算**
   - 定位：`first_positive` 在没有正样本时按契约返回 `None`，
     原 `calibrate` 继续执行 `sample - baseline`，触发类型错误。
   - 修复：基线为 `None` 时直接返回 0；有正基线时累计所有样本与基线之差。
   - 验证：无正样本测试通过，空样本和正常漂移计算也单独检查。

4. **事件 ID 上限遗漏相等情况**
   - 定位：契约要求统计 ID“不超过 max_id”的事件，原条件 `<` 排除了等于上限的事件。
     这一层过滤可能先遮蔽事件内部的样本漂移错误。
   - 修复：改为 `event["id"] <= max_id`，保留步数加漂移的统计方式。
   - 验证：等于上限的事件被统计，超过上限的事件被排除。

5. **默认历史列表跨调用共享**
   - 定位：原 `history=[]` 在函数定义时只创建一次，无显式历史的多次调用会互相污染。
   - 修复：默认值改为 `None`，每次未传入历史时创建新列表；
     显式传入列表时仍在原列表上追加并返回它。
   - 验证：默认历史独立性测试通过，并检查显式列表的对象身份和内容。

6. **模拟循环推进与停止条件错误**
   - 定位：原 while 循环未递增轮号，且在体力 `>20` 时退出。
     错误的提前退出遮蔽了轮号不推进的问题；只修退出条件又可能造成无限循环。
   - 修复：使用 `for round_ in range(rounds)` 依次推进；每轮扣 8，
     轮号从 3 起再扣 5，记录轮末状态后在体力 `<=20` 时立即停止。
   - 验证：基础模拟和阈值停止测试通过；零轮、轮号 3 的额外消耗、恰好 20 的停止均补查。

### Q7 验证结果

- 可见测试：`python -m pytest -k Q7 -vv --tb=short`，7 项全部通过。
- 补充边界检查：脏输入、空样本、显式历史列表、ID 上限、零轮及体力阈值通过。
- 这是本地可见测试和边界验证记录，不代表隐藏测试已通过。

### Q1 精度与边界复核

- 将整数血量百分比改为整数乘除，避免先转浮点导致大整数溢出或精度损失。
- 保留最大血量非正返回 0、百分比限制在 0–100 的现有约定。
- 补查负血量、超出满血量、零分母、极大整数，以及电量 19/20/59/60 的边界。
- 验证：Q1 可见测试和上述补充断言通过；电量阈值按本次作业的补充要求。

### Q2 去重性能与脏行复核

- 普通可哈希 JSON ID 改用集合去重，避免长日志对每条 ID 都线性扫描。
- 列表或对象 ID 仍保留相等比较，未新增题面未要求的 ID 类型限制。
- 正则表达式每次函数调用只编译一次；整行验证完毕后才累计传感器事件。
- 验证：Q2 可见测试通过；布尔伤害、非法分段整行丢弃、有效 ID 去重、无 ID 独立计数、空日志通过补查。
- 伤害相等时暂按 front、left、right 的顺序取首个；题面没有明示平局优先级。

### Q3 初始化与位置校验复核

- 构造函数复用 current_pos setter，使初始坐标也执行长度与类型校验。
- 按题面允许的改写方式保留坐标转整数、地图范围夹取与起点障碍检查。
- 验证：Q3 可见测试通过；非法起点、列表坐标、越界碰撞、最后一单位电量、断电后前进和四次旋转通过补查。
