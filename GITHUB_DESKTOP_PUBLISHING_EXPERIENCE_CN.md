# 使用 GitHub Desktop 发布 Codex 生成的 Skill：经验与故障排查

本文记录一种在 Windows 上可靠发布 Skill 的协作方式：Codex 在受控工作区完成审查、修改、验证和本地 Git 提交；GitHub Desktop 使用用户桌面会话中的网络与 GitHub 登录状态完成 Fetch/Push；最后再从 Git 状态和远端提交双重验证发布结果。

适用场景：

- Codex/自动化执行环境可以读写本地仓库，但访问 `github.com:443` 超时或被重置。
- `gh auth status` 显示令牌过期，但 GitHub Desktop 仍已登录。
- 仓库由沙箱账户创建，GitHub Desktop 报 `detected dubious ownership`。
- 需要把生成内容安全加入既有 Skill 仓库，又不希望复制令牌、关闭安全检查或强制覆盖远端。

## 一、发布边界

发布分为三个独立阶段：

1. **内容阶段**：编辑、验证、测试。此时不访问远端，也不把求解结果或临时文件混进仓库。
2. **Git 阶段**：检查差异、提交到本地分支。提交成功不等于发布成功。
3. **远端阶段**：Fetch、Push、再次验证 `HEAD` 与 `origin/main`。只有第三阶段验证完成才算发布。

不要因为前两个阶段成功就报告“GitHub 已更新”。

## 二、本地发布前检查

在目标仓库中确认：

```powershell
git status --short --branch
git diff --check
git diff --stat
```

提交前至少验证以下事项：

- `SKILL.md` 的 YAML frontmatter、名称和描述有效。
- 新增 reference 能从 `SKILL.md` 或仓库 README 被发现。
- Python 脚本能编译；新增或修改的脚本完成有意义的回归测试。
- 不包含 `__pycache__`、临时目录、仿真大文件、令牌、邮箱密码或本机私密配置。
- `git diff --check` 没有意外尾随空格或冲突标记。
- 现有用户修改没有被覆盖或混入本次提交。

提交示例：

```powershell
git add README.md techwiz-lc-lens
git commit -m "Add validated TechWiz LC lens skill"
```

记录提交哈希。后续 Push 和远端验证都以这个哈希为准。

## 三、优先尝试命令行发布

先检查远端、分支和登录：

```powershell
git remote -v
git status --short --branch
gh auth status
```

网络和凭据正常时：

```powershell
git fetch origin main
git push origin main
```

停止条件：

- 本地分支落后或与远端分叉时，不执行强制推送；先审查远端提交并决定 merge/rebase。
- 身份不明确、目标仓库不符或出现权限提示时，不尝试复制/读取令牌。
- 同一种网络错误连续出现后，转用 GitHub Desktop，不进行无休止重试。

## 四、命令行失败时使用 GitHub Desktop

### 1. 确认失败类型

| 症状 | 含义 | 处理 |
|---|---|---|
| DNS 能解析，但 443 超时或 `Connection reset` | 命令执行环境的网络路径受限 | 转用 GitHub Desktop 的桌面网络会话 |
| `gh auth status` 显示 token invalid | GitHub CLI 凭据失效 | 可重新 `gh auth login`，或使用已登录的 GitHub Desktop |
| `git: 'remote-https' is not a git command` | 当前 Git 运行时未正确找到 HTTPS helper | 使用完整 Git 安装或 GitHub Desktop，不复制未知 helper 到系统目录 |
| `schannel: SEC_E_NO_CREDENTIALS` | 当前 Git/SSL/Windows 凭据组合不可用 | 使用 GitHub Desktop 自带 Git 与登录会话 |
| `detected dubious ownership` | 仓库所有者与桌面用户不同 | 仅把准确仓库路径加入 `safe.directory` |

网络诊断要区分 DNS 与 TCP：DNS 成功并不代表 HTTPS 可连接。本次案例中 `github.com` 能解析，但命令行连接 443 超时/重置；GitHub Desktop 随后能在数秒内 Fetch，证明仓库和电脑网络本身没有问题，限制发生在具体执行环境。

### 2. 只信任准确仓库路径

沙箱创建的仓库可能属于另一个 Windows SID。GitHub Desktop 会正确拒绝它，日志中通常出现：

```text
fatal: detected dubious ownership in repository at 'D:/path/to/repository'
```

使用 GitHub Desktop 附带的 Git，只添加该仓库：

```powershell
& '<GitHub Desktop git.exe>' config --global --add safe.directory 'D:/path/to/repository'
```

安全要求：

- 使用解析后的绝对路径并再次核对仓库。
- 不设置 `safe.directory '*'`。
- 不为无关父目录或整个磁盘添加例外。
- 添加后用 `git config --global --get-all safe.directory` 检查范围。

### 3. 在 GitHub Desktop 中打开仓库

可使用菜单 **File → Add Local Repository…**，选择仓库目录；也可使用 GitHub Desktop 自带命令：

```powershell
github open D:\path\to\repository
```

打开后核对：

- **Current repository** 是目标仓库。
- **Current branch** 是预期分支，例如 `main`。
- 本地提交哈希/提交消息与待发布内容一致。
- 点击 **Fetch origin** 后没有出现分叉或待拉取提交。
- 按钮显示 **Push origin**，待推送提交数符合预期。

然后点击 **Push origin**。不要使用 Force Push 解决普通同步问题。

## 五、发布后验证

GitHub Desktop 的按钮变化只是第一层证据。再做本地 Git 验证：

```powershell
git status --short --branch
git rev-list --left-right --count origin/main...main
git log -1 --oneline --decorate
```

成功状态应满足：

- `status` 不再显示 `[ahead N]` 或 `[behind N]`。
- `rev-list` 返回 `0  0`。
- `HEAD`、`origin/main` 和 `origin/HEAD` 指向预期提交。
- 工作树没有意外未提交文件。

必要时再打开 GitHub 仓库网页，确认目录、README 入口和提交哈希。远端网页验证尤其适用于跨机器交付。

本次 TechWiz Skill 发布的闭环结果是：本地提交 `ee544d8` 经 GitHub Desktop Push 后，`HEAD -> main`、`origin/main`、`origin/HEAD` 均指向该提交。

## 六、推荐的协作分工

Codex/自动化端负责：

- 保留并审查用户已有改动。
- 编辑、测试、清理临时文件、生成本地提交。
- 报告准确的提交哈希和未完成状态。
- 在 Push 后验证远端引用。

用户桌面会话负责：

- GitHub 登录、验证码或交互式授权。
- 在 GitHub Desktop 中确认目标仓库/分支并点击 Push。
- 处理必须由账户所有者确认的安全提示。

任何一方都不应通过聊天、日志或脚本传递 GitHub 密码、PAT、OAuth token 或验证码。

## 七、发布清单

- [ ] 目标仓库和分支已核对
- [ ] Skill 校验与脚本测试通过
- [ ] `git diff --check` 通过
- [ ] 临时文件和敏感信息已排除
- [ ] 本地提交已创建并记录哈希
- [ ] Fetch 后确认没有未审查的远端变化
- [ ] Push 使用普通快进更新，不是 Force Push
- [ ] `HEAD` 与 `origin/main` 指向同一预期提交
- [ ] GitHub 网页或远端引用确认新文件可见
