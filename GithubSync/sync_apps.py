#!/usr/bin/env python3
"""
同步脚本：将TShentu/apps仓库的sync分支同步到terminus-apps-origin仓库
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_apps.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AppSyncManager:
    """应用同步管理器"""
    
    def __init__(self, config_file: str = "sync_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
        # 设置路径
        self.base_path = Path("/Users/cid/Documents/GitHub/TShentu")
        self.apps_repo_path = self.base_path / "apps"
        self.terminus_apps_origin_path = self.base_path / "terminus-apps-origin"
        
        # 验证仓库路径
        self._validate_repos()
        
    def load_config(self) -> Dict:
        """加载配置文件"""
        config_path = Path(self.config_file)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 创建默认配置
            default_config = {
                "last_synced_commit": None,
                "github": {
                    "token": None,
                    "username": None,
                    "email": None
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
                    "auto_resolve_conflicts": True,
                    "create_draft_pr": True,
                    "pr_title_template": "sync from prod {date}",
                    "pr_body_template": "## 同步内容\n\n{sync_commits}\n\n同步了 {commit_count} 个提交。"
                }
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict = None):
        """保存配置文件"""
        if config is None:
            config = self.config
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _validate_repos(self):
        """验证仓库路径是否存在"""
        if not self.apps_repo_path.exists():
            raise FileNotFoundError(f"Apps repository not found: {self.apps_repo_path}")
        if not self.terminus_apps_origin_path.exists():
            raise FileNotFoundError(f"Terminus apps origin repository not found: {self.terminus_apps_origin_path}")
    
    def run_git_command(self, repo_path: Path, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """运行Git命令"""
        full_command = ["git"] + command
        logger.debug(f"Running git command in {repo_path}: {' '.join(full_command)}")
        
        try:
            result = subprocess.run(
                full_command,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise
    
    def get_commit_hash(self, repo_path: Path, ref: str = "HEAD") -> str:
        """获取指定引用的commit hash"""
        result = self.run_git_command(repo_path, ["rev-parse", ref])
        return result.stdout.strip()
    
    def find_remote_branch(self, repo_path: Path, branch_name: str) -> Optional[str]:
        """查找可用的远程分支"""
        try:
            # 首先尝试 origin/branch_name
            result = self.run_git_command(repo_path, ["rev-parse", f"origin/{branch_name}"], check=False)
            if result.returncode == 0:
                return f"origin/{branch_name}"
        except:
            pass
        
        try:
            # 然后尝试 upstream/branch_name
            result = self.run_git_command(repo_path, ["rev-parse", f"upstream/{branch_name}"], check=False)
            if result.returncode == 0:
                return f"upstream/{branch_name}"
        except:
            pass
        
        try:
            # 最后尝试本地分支
            result = self.run_git_command(repo_path, ["rev-parse", branch_name], check=False)
            if result.returncode == 0:
                return branch_name
        except:
            pass
        
        return None
    
    def get_commit_log(self, repo_path: Path, from_commit: str, to_commit: str = "HEAD") -> List[Dict]:
        """获取commit日志"""
        if from_commit == to_commit:
            return []
        
        # 获取commit列表
        result = self.run_git_command(repo_path, [
            "log", "--oneline", "--format=%H|%s|%an|%ad", 
            "--date=short", f"{from_commit}..{to_commit}"
        ])
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3]
                    })
        
        return commits
    
    def fetch_latest_changes(self):
        """获取最新更改"""
        logger.info("Fetching latest changes from apps repository...")
        self.run_git_command(self.apps_repo_path, ["fetch", "origin"])
        
        logger.info("Fetching latest changes from terminus-apps-origin repository...")
        self.run_git_command(self.terminus_apps_origin_path, ["fetch", "origin"])
    
    def create_sync_branch(self, branch_name: str) -> bool:
        """创建同步分支"""
        try:
            # 检查分支是否已存在
            result = self.run_git_command(
                self.terminus_apps_origin_path, 
                ["branch", "--list", branch_name], 
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"Branch {branch_name} already exists, deleting it...")
                self.run_git_command(self.terminus_apps_origin_path, ["branch", "-D", branch_name])
            
            # 创建新分支
            self.run_git_command(self.terminus_apps_origin_path, ["checkout", "-b", branch_name])
            logger.info(f"Created branch: {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False
    
    def cherry_pick_commits(self, commits: List[Dict]) -> bool:
        """Cherry-pick指定的commits"""
        if not commits:
            logger.info("No commits to cherry-pick")
            return True
        
        logger.info(f"Cherry-picking {len(commits)} commits...")
        
        for commit in commits:
            try:
                logger.info(f"Cherry-picking commit: {commit['hash'][:8]} - {commit['message']}")
                
                # 直接使用sync分支的版本，确保文件内容完全一致
                logger.debug(f"Ensuring sync version for commit {commit['hash'][:8]}...")
                self.ensure_sync_version(commit['hash'])
                
                # 检查是否有更改需要提交
                status_result = self.run_git_command(
                    self.terminus_apps_origin_path, 
                    ["status", "--porcelain"], 
                    check=False
                )
                
                if status_result.stdout.strip():
                    # 有更改，提交它们
                    self.run_git_command(self.terminus_apps_origin_path, [
                        "commit", "-m", commit['message'],
                        "--author", f"{commit['author']} <{commit['author']}@users.noreply.github.com>",
                        "--date", commit['date']
                    ])
                    logger.info(f"Successfully cherry-picked: {commit['hash'][:8]}")
                else:
                    # 没有更改，检查是否真的没有差异
                    # 比较源提交和目标仓库的当前状态
                    if self.has_actual_changes(commit['hash']):
                        logger.warning(f"Commit {commit['hash'][:8]} has changes but git status shows no changes. Forcing commit...")
                        # 强制更新文件并提交
                        self.force_update_files(commit['hash'])
                        self.run_git_command(self.terminus_apps_origin_path, [
                            "commit", "-m", commit['message'],
                            "--author", f"{commit['author']} <{commit['author']}@users.noreply.github.com>",
                            "--date", commit['date']
                        ])
                        logger.info(f"Force committed changes: {commit['hash'][:8]}")
                    else:
                        logger.info(f"No changes to commit for {commit['hash'][:8]}, skipping...")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to cherry-pick commit {commit['hash'][:8]}: {e}")
                return False
        
        return True
    
    def has_actual_changes(self, commit_hash: str) -> bool:
        """检查源提交是否与目标仓库当前状态有实际差异"""
        try:
            # 获取源提交中修改的文件列表
            files_result = self.run_git_command(
                self.apps_repo_path,
                ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
            )
            
            modified_files = [f.strip() for f in files_result.stdout.strip().split('\n') if f.strip()]
            
            if not modified_files:
                return False
            
            # 检查每个文件是否有差异
            for file_path in modified_files:
                try:
                    # 获取源文件内容
                    source_content = self.run_git_command(
                        self.apps_repo_path,
                        ["show", f"{commit_hash}:{file_path}"]
                    )
                    
                    # 获取目标文件内容
                    target_file = self.terminus_apps_origin_path / file_path
                    if target_file.exists():
                        target_content = target_file.read_text(encoding='utf-8')
                    else:
                        target_content = ""
                    
                    # 比较内容
                    if source_content.stdout != target_content:
                        logger.debug(f"File {file_path} has differences")
                        return True
                        
                except subprocess.CalledProcessError:
                    # 如果源文件中不存在该文件，检查目标文件是否存在
                    target_file = self.terminus_apps_origin_path / file_path
                    if target_file.exists():
                        logger.debug(f"File {file_path} exists in target but not in source")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for actual changes: {e}")
            return False
    
    def force_update_files(self, commit_hash: str):
        """强制更新文件，确保git检测到变更"""
        try:
            # 获取commit中修改的文件列表
            files_result = self.run_git_command(
                self.apps_repo_path,
                ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
            )
            
            modified_files = [f.strip() for f in files_result.stdout.strip().split('\n') if f.strip()]
            
            if not modified_files:
                return
            
            logger.debug(f"Force updating {len(modified_files)} files...")
            
            for file_path in modified_files:
                try:
                    # 从apps仓库获取文件内容
                    file_content = self.run_git_command(
                        self.apps_repo_path,
                        ["show", f"{commit_hash}:{file_path}"]
                    )
                    
                    # 写入文件
                    full_path = self.terminus_apps_origin_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(file_content.stdout, encoding='utf-8')
                    
                    # 强制添加到暂存区
                    self.run_git_command(self.terminus_apps_origin_path, ["add", file_path])
                    logger.debug(f"Force updated file: {file_path}")
                    
                except subprocess.CalledProcessError as e:
                    # 如果文件在commit中不存在，删除它
                    full_path = self.terminus_apps_origin_path / file_path
                    if full_path.exists():
                        full_path.unlink()
                        self.run_git_command(self.terminus_apps_origin_path, ["rm", file_path])
                        logger.debug(f"Force removed file: {file_path}")
            
            # 强制更新git索引
            self.run_git_command(self.terminus_apps_origin_path, ["add", "."])
            logger.debug("Force updated git index")
            
        except Exception as e:
            logger.error(f"Error force updating files: {e}")
            raise
    
    def resolve_conflicts_with_sync(self, commit_hash: str):
        """解决冲突，使用来自sync的文件版本"""
        try:
            # 获取所有修改的文件（包括冲突文件）
            status_result = self.run_git_command(
                self.terminus_apps_origin_path, 
                ["status", "--porcelain"], 
                check=False
            )
            
            modified_files = []
            for line in status_result.stdout.strip().split('\n'):
                if line.strip():
                    # 获取文件路径（去掉状态标记）
                    file_path = line[3:].strip()
                    modified_files.append(file_path)
            
            if not modified_files:
                logger.info("No files to resolve conflicts for")
                return
            
            logger.info(f"Resolving conflicts for {len(modified_files)} files using sync version...")
            
            for file_path in modified_files:
                try:
                    # 从apps仓库获取文件内容
                    file_content = self.run_git_command(
                        self.apps_repo_path,
                        ["show", f"{commit_hash}:{file_path}"]
                    )
                    
                    # 写入文件
                    full_path = self.terminus_apps_origin_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(file_content.stdout, encoding='utf-8')
                    
                    # 添加到暂存区
                    self.run_git_command(self.terminus_apps_origin_path, ["add", file_path])
                    logger.debug(f"Resolved conflict for file: {file_path}")
                    
                except subprocess.CalledProcessError as e:
                    # 如果文件在commit中不存在，删除它
                    full_path = self.terminus_apps_origin_path / file_path
                    if full_path.exists():
                        full_path.unlink()
                        self.run_git_command(self.terminus_apps_origin_path, ["rm", file_path])
                        logger.debug(f"Removed file: {file_path}")
                    else:
                        logger.debug(f"File {file_path} already removed or doesn't exist")
            
            # 确保所有更改都已暂存
            self.run_git_command(self.terminus_apps_origin_path, ["add", "."])
            
        except Exception as e:
            logger.error(f"Error resolving conflicts: {e}")
            raise
    
    def ensure_sync_version(self, commit_hash: str):
        """确保使用sync分支的版本，覆盖所有文件"""
        try:
            # 获取commit中修改的文件列表
            files_result = self.run_git_command(
                self.apps_repo_path,
                ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
            )
            
            modified_files = [f.strip() for f in files_result.stdout.strip().split('\n') if f.strip()]
            
            if not modified_files:
                logger.debug("No files modified in this commit")
                return
            
            logger.debug(f"Ensuring sync version for {len(modified_files)} files...")
            
            files_updated = False
            for file_path in modified_files:
                try:
                    # 从apps仓库获取文件内容
                    file_content = self.run_git_command(
                        self.apps_repo_path,
                        ["show", f"{commit_hash}:{file_path}"]
                    )
                    
                    # 写入文件
                    full_path = self.terminus_apps_origin_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(file_content.stdout, encoding='utf-8')
                    
                    # 强制添加到暂存区（即使内容相同）
                    self.run_git_command(self.terminus_apps_origin_path, ["add", file_path])
                    files_updated = True
                    logger.debug(f"Updated file: {file_path}")
                    
                except subprocess.CalledProcessError as e:
                    # 如果文件在commit中不存在，删除它
                    full_path = self.terminus_apps_origin_path / file_path
                    if full_path.exists():
                        full_path.unlink()
                        self.run_git_command(self.terminus_apps_origin_path, ["rm", file_path])
                        files_updated = True
                        logger.debug(f"Removed file: {file_path}")
                    else:
                        logger.debug(f"File {file_path} already removed or doesn't exist")
            
            # 如果更新了文件但没有检测到变更，强制更新git索引
            if files_updated:
                # 强制更新索引，确保所有更改都被检测到
                self.run_git_command(self.terminus_apps_origin_path, ["add", "."])
                logger.debug("Forced git index update")
            
        except Exception as e:
            logger.error(f"Error ensuring sync version: {e}")
            raise
    
    def resolve_unmerged_files(self, commit_hash: str):
        """解决未合并的文件，使用sync分支的版本"""
        try:
            # 检查是否有未合并的文件
            status_result = self.run_git_command(
                self.terminus_apps_origin_path, 
                ["status", "--porcelain"], 
                check=False
            )
            
            unmerged_files = []
            for line in status_result.stdout.strip().split('\n'):
                if line.strip() and (line.startswith('UU') or line.startswith('AA') or line.startswith('DD') or line.startswith('U')):
                    file_path = line[3:].strip()
                    unmerged_files.append(file_path)
            
            if not unmerged_files:
                logger.debug("No unmerged files found")
                return
            
            logger.info(f"Resolving {len(unmerged_files)} unmerged files using sync version...")
            
            for file_path in unmerged_files:
                try:
                    # 从apps仓库获取文件内容
                    file_content = self.run_git_command(
                        self.apps_repo_path,
                        ["show", f"{commit_hash}:{file_path}"]
                    )
                    
                    # 写入文件
                    full_path = self.terminus_apps_origin_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(file_content.stdout, encoding='utf-8')
                    
                    # 添加到暂存区
                    self.run_git_command(self.terminus_apps_origin_path, ["add", file_path])
                    logger.debug(f"Resolved unmerged file: {file_path}")
                    
                except subprocess.CalledProcessError as e:
                    # 如果文件在commit中不存在，删除它
                    full_path = self.terminus_apps_origin_path / file_path
                    if full_path.exists():
                        full_path.unlink()
                        self.run_git_command(self.terminus_apps_origin_path, ["rm", file_path])
                        logger.debug(f"Removed unmerged file: {file_path}")
                    else:
                        logger.debug(f"Unmerged file {file_path} already removed or doesn't exist")
            
            # 确保所有更改都已暂存
            self.run_git_command(self.terminus_apps_origin_path, ["add", "."])
            
        except Exception as e:
            logger.error(f"Error resolving unmerged files: {e}")
            raise
    
    def create_pull_request(self, branch_name: str, commits: List[Dict]) -> Optional[str]:
        """创建Pull Request"""
        github_config = self.config.get("github", {})
        if not github_config.get("token"):
            logger.warning("GitHub token not configured, skipping PR creation")
            return None
        
        if not self.config.get("sync_settings", {}).get("create_draft_pr", True):
            logger.info("PR creation disabled in config")
            return None
        
        try:
            import requests
            
            # 准备PR内容
            sync_settings = self.config.get("sync_settings", {})
            pr_title = sync_settings.get("pr_title_template", "sync from prod {date}").format(
                date=datetime.now().strftime('%Y-%m-%d')
            )
            
            # 构建同步commits列表
            sync_commits_text = ""
            for commit in commits:
                sync_commits_text += f"- {commit['hash'][:8]}: {commit['message']} (by {commit['author']})\n"
            
            pr_body = sync_settings.get("pr_body_template", "## 同步内容\n\n{sync_commits}\n\n同步了 {commit_count} 个提交。").format(
                sync_commits=sync_commits_text,
                commit_count=len(commits)
            )
            
            # 创建PR
            target_repo = self.config['repositories']['target']
            url = f"https://api.github.com/repos/{target_repo['owner']}/{target_repo['repo']}/pulls"
            headers = {
                "Authorization": f"token {github_config['token']}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "title": pr_title,
                "body": pr_body,
                "head": branch_name,
                "base": target_repo['branch'],
                "draft": True,
                "labels": ["enhancement"]
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            pr_data = response.json()
            pr_url = pr_data['html_url']
            logger.info(f"Created draft PR: {pr_url}")
            
            return pr_url
            
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return None
    
    def sync(self, dry_run: bool = False):
        """执行同步"""
        logger.info("Starting sync process...")
        
        try:
            # 1. 获取最新更改
            self.fetch_latest_changes()
            
            # 2. 智能查找sync分支
            sync_branch_ref = self.find_remote_branch(self.apps_repo_path, "sync")
            if not sync_branch_ref:
                logger.error("Cannot find sync branch in any remote repository")
                return
            
            logger.info(f"Using sync branch: {sync_branch_ref}")
            current_sync_commit = self.get_commit_hash(self.apps_repo_path, sync_branch_ref)
            last_synced_commit = self.config.get("last_synced_commit")
            
            if last_synced_commit == current_sync_commit:
                logger.info("No new commits to sync")
                return
            
            # 3. 获取需要同步的commits
            if last_synced_commit:
                commits_to_sync = self.get_commit_log(
                    self.apps_repo_path, 
                    last_synced_commit, 
                    current_sync_commit
                )
            else:
                # 第一次同步，查找main分支作为基准
                main_branch_ref = self.find_remote_branch(self.apps_repo_path, "main")
                if not main_branch_ref:
                    logger.error("Cannot find main branch in any remote repository")
                    return
                
                logger.info(f"Using main branch as baseline: {main_branch_ref}")
                commits_to_sync = self.get_commit_log(
                    self.apps_repo_path, 
                    main_branch_ref, 
                    current_sync_commit
                )
            
            if not commits_to_sync:
                logger.info("No commits to sync")
                return
            
            logger.info(f"Found {len(commits_to_sync)} commits to sync")
            
            if dry_run:
                logger.info("Dry run mode - would sync the following commits:")
                for commit in commits_to_sync:
                    logger.info(f"  {commit['hash'][:8]}: {commit['message']}")
                return
            
            # 4. 创建同步分支
            branch_name = f"sync-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            if not self.create_sync_branch(branch_name):
                logger.error("Failed to create sync branch")
                return
            
            # 5. Cherry-pick commits
            if not self.cherry_pick_commits(commits_to_sync):
                logger.error("Failed to cherry-pick commits")
                return
            
            # 6. 配置Git用户信息并推送分支
            github_config = self.config.get("github", {})
            if github_config.get("username") and github_config.get("email"):
                self.run_git_command(self.terminus_apps_origin_path, [
                    "config", "user.name", github_config["username"]
                ])
                self.run_git_command(self.terminus_apps_origin_path, [
                    "config", "user.email", github_config["email"]
                ])
                logger.info(f"Configured Git user: {github_config['username']} <{github_config['email']}>")
            
            # 推送分支（使用token认证）
            github_config = self.config.get("github", {})
            if github_config.get("token"):
                # 使用token进行推送
                remote_url = f"https://{github_config['token']}@github.com/{self.config['repositories']['target']['owner']}/{self.config['repositories']['target']['repo']}.git"
                self.run_git_command(self.terminus_apps_origin_path, ["push", remote_url, branch_name])
            else:
                # 使用默认推送
                self.run_git_command(self.terminus_apps_origin_path, ["push", "origin", branch_name])
            logger.info(f"Pushed branch: {branch_name}")
            
            # 7. 创建PR
            pr_url = self.create_pull_request(branch_name, commits_to_sync)
            
            # 8. 更新配置
            self.config["last_synced_commit"] = current_sync_commit
            self.save_config()
            
            logger.info("Sync completed successfully!")
            if pr_url:
                logger.info(f"PR created: {pr_url}")
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="同步apps仓库的sync分支到terminus-apps-origin")
    parser.add_argument("--dry-run", action="store_true", help="只显示将要同步的内容，不实际执行")
    parser.add_argument("--config", default="sync_config.json", help="配置文件路径")
    parser.add_argument("--github-token", help="GitHub token (会覆盖配置文件中的设置)")
    parser.add_argument("--github-username", help="GitHub username (会覆盖配置文件中的设置)")
    parser.add_argument("--github-email", help="GitHub email (会覆盖配置文件中的设置)")
    parser.add_argument("--setup", action="store_true", help="交互式设置GitHub配置")
    
    args = parser.parse_args()
    
    try:
        manager = AppSyncManager(args.config)
        
        # 交互式设置
        if args.setup:
            setup_github_config(manager)
            return
        
        # 如果提供了GitHub信息，更新配置
        if args.github_token or args.github_username or args.github_email:
            if "github" not in manager.config:
                manager.config["github"] = {}
            
            if args.github_token:
                manager.config["github"]["token"] = args.github_token
            if args.github_username:
                manager.config["github"]["username"] = args.github_username
            if args.github_email:
                manager.config["github"]["email"] = args.github_email
            
            manager.save_config()
            logger.info("GitHub configuration updated")
        
        manager.sync(dry_run=args.dry_run)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

def setup_github_config(manager: AppSyncManager):
    """交互式设置GitHub配置"""
    print("=== GitHub 配置设置 ===")
    
    # 确保github配置存在
    if "github" not in manager.config:
        manager.config["github"] = {}
    
    # 获取GitHub token
    current_token = manager.config["github"].get("token")
    if current_token and current_token != "YOUR_GITHUB_TOKEN_HERE":
        print(f"当前GitHub token: {current_token[:8]}...")
        update_token = input("是否更新token? (y/N): ").lower().strip()
        if update_token == 'y':
            new_token = input("请输入新的GitHub token: ").strip()
            if new_token:
                manager.config["github"]["token"] = new_token
    else:
        new_token = input("请输入GitHub token: ").strip()
        if new_token:
            manager.config["github"]["token"] = new_token
    
    # 获取GitHub用户名
    current_username = manager.config["github"].get("username")
    if current_username and current_username != "YOUR_GITHUB_USERNAME":
        print(f"当前GitHub用户名: {current_username}")
        update_username = input("是否更新用户名? (y/N): ").lower().strip()
        if update_username == 'y':
            new_username = input("请输入新的GitHub用户名: ").strip()
            if new_username:
                manager.config["github"]["username"] = new_username
    else:
        new_username = input("请输入GitHub用户名: ").strip()
        if new_username:
            manager.config["github"]["username"] = new_username
    
    # 获取邮箱
    current_email = manager.config["github"].get("email")
    if current_email and current_email != "YOUR_EMAIL@example.com":
        print(f"当前邮箱: {current_email}")
        update_email = input("是否更新邮箱? (y/N): ").lower().strip()
        if update_email == 'y':
            new_email = input("请输入新的邮箱: ").strip()
            if new_email:
                manager.config["github"]["email"] = new_email
    else:
        new_email = input("请输入邮箱: ").strip()
        if new_email:
            manager.config["github"]["email"] = new_email
    
    # 保存配置
    manager.save_config()
    print("GitHub配置已保存!")

if __name__ == "__main__":
    main()
