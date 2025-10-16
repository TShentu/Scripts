# Apps 同步脚本

这个脚本用于将 TShentu/apps 仓库的 sync 分支同步到 terminus-apps-origin 仓库。

## 功能特性

- 自动检测需要同步的新提交
- 创建同步分支并 cherry-pick 提交
- 自动解决冲突（使用来自 sync 分支的版本）
- 创建指向 main 分支的 draft Pull Request
- 记录同步状态，支持增量同步
- 详细的日志记录

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

### 方法一：交互式设置（推荐）

```bash
python3 sync_apps.py --setup
```

这会引导您完成所有必要的配置设置。

### 方法二：手动编辑配置文件

1. 复制配置文件模板：
   ```bash
   cp sync_config.template.json sync_config.json
   ```

2. 编辑 `sync_config.json` 文件：
   ```json
   {
     "last_synced_commit": null,
     "github": {
       "token": "YOUR_GITHUB_TOKEN_HERE",
       "username": "YOUR_GITHUB_USERNAME",
       "email": "YOUR_EMAIL@example.com"
     },
     "repositories": {
       "source": {
         "owner": "beclab",
         "repo": "apps",
         "branch": "sync"
       },
       "target": {
         "owner": "Above-Os",
         "repo": "terminus-apps",
         "branch": "main"
       }
     },
     "sync_settings": {
       "auto_resolve_conflicts": true,
       "create_draft_pr": true,
       "pr_title_template": "sync from prod {date}",
       "pr_body_template": "## 同步内容\n\n{sync_commits}\n\n同步了 {commit_count} 个提交。"
     }
   }
   ```

### 方法三：命令行参数

```bash
python3 sync_apps.py --github-token YOUR_TOKEN --github-username YOUR_USERNAME --github-email YOUR_EMAIL
```

## 快速开始

1. 进入项目目录：
   ```bash
   cd /Users/cid/Documents/GitHub/TShentu/Scripts/GithubSync
   ```

2. 设置GitHub配置：
   ```bash
   # 交互式设置（推荐）
   python3 sync_apps.py --setup
   ```

3. 运行同步：
   ```bash
   # 干运行（查看将要同步的内容）
   python3 sync_apps.py --dry-run
   
   # 实际同步
   python3 sync_apps.py
   
   # 或使用启动脚本
   ./run_sync.sh
   ```

## 使用方法

### 基本用法

```bash
# 执行同步
python3 sync_apps.py

# 干运行（只显示将要同步的内容）
python3 sync_apps.py --dry-run

# 指定配置文件
python3 sync_apps.py --config my_config.json

# 交互式设置配置
python3 sync_apps.py --setup
```

### 命令行参数

```bash
python3 sync_apps.py [选项]

选项:
  -h, --help              显示帮助信息
  --dry-run              只显示将要同步的内容，不实际执行
  --config CONFIG        配置文件路径 (默认: sync_config.json)
  --github-token TOKEN   GitHub token (会覆盖配置文件中的设置)
  --github-username USER GitHub用户名 (会覆盖配置文件中的设置)
  --github-email EMAIL   GitHub邮箱 (会覆盖配置文件中的设置)
  --setup               交互式设置GitHub配置
```

### 首次运行

首次运行时，脚本会：
1. 从 `origin/main` 到 `origin/sync` 的所有提交进行同步
2. 创建同步分支
3. 创建 draft PR
4. 记录同步状态

### 后续运行

后续运行时，脚本会：
1. 检查是否有新的提交需要同步
2. 只同步上次同步后的新提交
3. 如果没有新提交，显示"同步完成"

## 工作流程

1. **获取最新更改**: 从两个仓库获取最新的提交
2. **检测新提交**: 比较上次同步的 commit 和当前 sync 分支的最新 commit
3. **创建同步分支**: 在 terminus-apps-origin 中创建新的同步分支
4. **Cherry-pick 提交**: 将需要同步的提交应用到新分支
5. **解决冲突**: 如果遇到冲突，自动使用来自 sync 分支的版本
6. **推送分支**: 将同步分支推送到远程仓库
7. **创建 PR**: 创建指向 main 分支的 draft Pull Request
8. **更新状态**: 记录本次同步的 commit hash

## 日志

脚本会生成详细的日志，包括：
- 控制台输出
- `sync_apps.log` 文件

## 错误处理

- 自动处理 Git 冲突
- 详细的错误日志
- 失败时不会影响已同步的状态

## 更新日志

### v1.1.0 (2025-10-16)

**问题修复:**
- 修复了cherry-pick过程中文件变更检测失败的问题
- 解决了"空提交"导致PR创建失败的问题
- 改进了文件同步逻辑，确保所有变更都能正确应用

**技术改进:**
- 重写了`cherry_pick_commits`方法，使用更直接的文件同步方式
- 添加了`has_actual_changes`方法，用于检测源提交是否与目标仓库有实际差异
- 添加了`force_update_files`方法，强制更新文件确保git检测到变更
- 改进了`ensure_sync_version`方法，增加了强制更新git索引的逻辑

**问题背景:**
之前版本中，当源仓库的提交包含文件变更时，cherry-pick过程可能无法正确检测到这些变更，导致：
1. 程序显示"No changes to commit"，跳过有实际变更的提交
2. 创建的分支与main分支没有差异
3. GitHub API返回422错误："No commits between main and sync-branch"
4. PR创建失败

**修复效果:**
- 现在程序能够正确检测和应用所有文件变更
- 确保同步分支包含实际的代码差异
- PR创建成功，如测试中创建的PR #732

## 注意事项

- 确保有足够的权限访问两个仓库
- GitHub token 需要有创建 PR 的权限
- 建议在测试环境中先运行 `--dry-run` 模式
