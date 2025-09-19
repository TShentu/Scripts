#!/usr/bin/env python3
"""
文件夹同步脚本：将terminus-apps-origin仓库中指定的文件夹同步到apps仓库
"""

import os
import sys
import json
import subprocess
import logging
import shutil
import yaml
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import argparse
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_folders.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FolderSyncManager:
    """文件夹同步管理器"""
    
    def __init__(self, config_file: str = "sync_config.json", folders_file: str = "folders_to_sync.txt"):
        self.config_file = config_file
        self.folders_file = folders_file
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
            raise FileNotFoundError(f"Config file not found: {self.config_file}")
    
    def load_folders_list(self) -> List[str]:
        """加载要同步的文件夹列表"""
        folders_path = Path(self.folders_file)
        if not folders_path.exists():
            raise FileNotFoundError(f"Folders file not found: {self.folders_file}")
        
        with open(folders_path, 'r', encoding='utf-8') as f:
            folders = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith('#')]
        
        logger.info(f"Loaded {len(folders)} folders to sync: {folders}")
        return folders
    
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
    
    def fetch_latest_changes(self):
        """获取最新更改"""
        logger.info("Fetching latest changes from both repositories...")
        self.run_git_command(self.apps_repo_path, ["fetch", "origin"])
        self.run_git_command(self.terminus_apps_origin_path, ["fetch", "origin"])
    
    def get_folder_version(self, folder_path: Path) -> str:
        """获取文件夹中Chart.yaml的version字段"""
        chart_yaml_path = folder_path / "Chart.yaml"
        if not chart_yaml_path.exists():
            logger.warning(f"Chart.yaml not found in {folder_path}")
            return "1.0.0"
        
        try:
            with open(chart_yaml_path, 'r', encoding='utf-8') as f:
                chart_data = yaml.safe_load(f)
                version = chart_data.get('version', '1.0.0')
                logger.debug(f"Found version {version} in {folder_path}")
                return str(version)
        except Exception as e:
            logger.warning(f"Failed to read Chart.yaml in {folder_path}: {e}")
            return "1.0.0"
    
    def folder_exists_in_target(self, folder_name: str) -> bool:
        """检查目标仓库中是否存在同名文件夹"""
        target_folder_path = self.apps_repo_path / folder_name
        return target_folder_path.exists()
    
    def copy_folder(self, source_folder: Path, target_folder: Path) -> bool:
        """复制文件夹，替换目标文件夹"""
        try:
            # 如果目标文件夹存在，先删除
            if target_folder.exists():
                shutil.rmtree(target_folder)
                logger.debug(f"Removed existing folder: {target_folder}")
            
            # 复制文件夹
            shutil.copytree(source_folder, target_folder)
            logger.info(f"Copied folder from {source_folder} to {target_folder}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy folder from {source_folder} to {target_folder}: {e}")
            return False
    
    def has_changes(self, repo_path: Path) -> bool:
        """检查仓库是否有未提交的更改"""
        status_result = self.run_git_command(repo_path, ["status", "--porcelain"], check=False)
        return bool(status_result.stdout.strip())
    
    def create_branch(self, repo_path: Path, branch_name: str) -> bool:
        """创建分支"""
        try:
            # 检查分支是否已存在
            result = self.run_git_command(repo_path, ["branch", "--list", branch_name], check=False)
            
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"Branch {branch_name} already exists, deleting it...")
                self.run_git_command(repo_path, ["branch", "-D", branch_name])
            
            # 创建新分支
            self.run_git_command(repo_path, ["checkout", "-b", branch_name])
            logger.info(f"Created branch: {branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False
    
    def commit_changes(self, repo_path: Path, folder_name: str, version: str) -> bool:
        """提交更改"""
        try:
            # 配置Git用户信息
            github_config = self.config.get("github", {})
            if github_config.get("username") and github_config.get("email"):
                self.run_git_command(repo_path, [
                    "config", "user.name", github_config["username"]
                ])
                self.run_git_command(repo_path, [
                    "config", "user.email", github_config["email"]
                ])
            
            # 添加所有更改
            self.run_git_command(repo_path, ["add", "."])
            
            # 提交更改
            commit_message = f"[{self.get_pr_type(folder_name)}][{folder_name}][{version}]"
            self.run_git_command(repo_path, ["commit", "-m", commit_message])
            logger.info(f"Committed changes: {commit_message}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes: {e}")
            return False
    
    def get_pr_type(self, folder_name: str) -> str:
        """获取PR类型"""
        if self.folder_exists_in_target(folder_name):
            return "UPDATE"
        else:
            return "NEW"
    
    def push_branch(self, repo_path: Path, branch_name: str) -> bool:
        """推送分支"""
        try:
            github_config = self.config.get("github", {})
            if github_config.get("token"):
                # 使用token进行推送
                remote_url = f"https://{github_config['token']}@github.com/{self.config['repositories']['source']['owner']}/{self.config['repositories']['source']['repo']}.git"
                self.run_git_command(repo_path, ["push", remote_url, branch_name])
            else:
                # 使用默认推送
                self.run_git_command(repo_path, ["push", "origin", branch_name])
            logger.info(f"Pushed branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push branch {branch_name}: {e}")
            return False
    
    def create_pull_request(self, folder_name: str, version: str, branch_name: str) -> Optional[str]:
        """创建Pull Request"""
        github_config = self.config.get("github", {})
        if not github_config.get("token"):
            logger.warning("GitHub token not configured, skipping PR creation")
            return None
        
        try:
            import requests
            
            # 准备PR内容
            pr_type = self.get_pr_type(folder_name)
            pr_title = f"[{pr_type}][{folder_name}][{version}]"
            
            pr_body = f"### App Title\n{folder_name}\n\n### Description\n\n### Statement\n- [x] I have tested this application to ensure it is compatible with the Olares OS version stated in the `OlaresManifest.yaml`"
            
            # 创建PR
            source_repo = self.config['repositories']['source']
            url = f"https://api.github.com/repos/{source_repo['owner']}/{source_repo['repo']}/pulls"
            headers = {
                "Authorization": f"token {github_config['token']}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "title": pr_title,
                "body": pr_body,
                "head": branch_name,
                "base": "main",
                "draft": True
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
    
    def sync_folder(self, folder_name: str) -> bool:
        """同步单个文件夹"""
        logger.info(f"Starting sync for folder: {folder_name}")
        
        try:
            # 1. 检查源文件夹是否存在
            source_folder = self.terminus_apps_origin_path / folder_name
            if not source_folder.exists():
                logger.error(f"Source folder not found: {source_folder}")
                return False
            
            # 2. 获取版本信息
            version = self.get_folder_version(source_folder)
            logger.info(f"Folder version: {version}")
            
            # 3. 确保在main分支上
            logger.info("Switching to main branch...")
            self.run_git_command(self.apps_repo_path, ["checkout", "main"])
            
            # 4. 拉取最新的main分支
            logger.info("Pulling latest changes from main branch...")
            self.run_git_command(self.apps_repo_path, ["pull", "origin", "main"])
            
            # 5. 复制文件夹到apps仓库
            target_folder = self.apps_repo_path / folder_name
            if not self.copy_folder(source_folder, target_folder):
                return False
            
            # 6. 检查是否有更改
            if not self.has_changes(self.apps_repo_path):
                logger.info(f"文件夹 {folder_name} 没有修改内容，跳过PR创建")
                return True
            
            # 7. 创建分支
            branch_name = f"sync-{folder_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            if not self.create_branch(self.apps_repo_path, branch_name):
                return False
            
            # 8. 提交更改
            if not self.commit_changes(self.apps_repo_path, folder_name, version):
                return False
            
            # 9. 推送分支
            if not self.push_branch(self.apps_repo_path, branch_name):
                return False
            
            # 10. 创建PR
            pr_url = self.create_pull_request(folder_name, version, branch_name)
            if pr_url:
                logger.info(f"Successfully synced folder {folder_name}, PR: {pr_url}")
                # 等待5秒避免提交过快
                logger.info("Waiting 5 seconds before next operation...")
                time.sleep(5)
            else:
                logger.warning(f"Folder {folder_name} synced but PR creation failed")
            
            # 11. 切换回main分支，为下一个文件夹做准备
            logger.info("Switching back to main branch for next folder...")
            self.run_git_command(self.apps_repo_path, ["checkout", "main"])
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync folder {folder_name}: {e}")
            # 确保在出错时也切换回main分支
            try:
                self.run_git_command(self.apps_repo_path, ["checkout", "main"])
            except:
                pass
            return False
    
    def sync_single_folder(self, folder_name: str, dry_run: bool = False):
        """同步单个文件夹"""
        logger.info(f"Starting single folder sync: {folder_name}")
        
        try:
            # 1. 获取最新更改
            self.fetch_latest_changes()
            
            # 2. 同步单个文件夹
            if dry_run:
                logger.info(f"Dry run: would sync folder {folder_name}")
                return True
            
            if self.sync_folder(folder_name):
                logger.info(f"Successfully synced folder: {folder_name}")
                return True
            else:
                logger.error(f"Failed to sync folder: {folder_name}")
                return False
                
        except Exception as e:
            logger.error(f"Single folder sync failed: {e}")
            raise
    
    def sync_all_folders(self, dry_run: bool = False):
        """同步所有文件夹"""
        logger.info("Starting folder sync process...")
        
        try:
            # 1. 获取最新更改
            self.fetch_latest_changes()
            
            # 2. 确保在main分支上开始
            logger.info("Ensuring we start from main branch...")
            self.run_git_command(self.apps_repo_path, ["checkout", "main"])
            
            # 3. 加载文件夹列表
            folders = self.load_folders_list()
            
            if not folders:
                logger.info("No folders to sync")
                return
            
            # 4. 逐个同步文件夹
            success_count = 0
            for i, folder_name in enumerate(folders, 1):
                logger.info(f"Processing folder {i}/{len(folders)}: {folder_name}")
                
                if dry_run:
                    logger.info(f"Dry run: would sync folder {folder_name}")
                    continue
                
                if self.sync_folder(folder_name):
                    success_count += 1
                    logger.info(f"Successfully synced folder {i}/{len(folders)}: {folder_name}")
                else:
                    logger.error(f"Failed to sync folder {i}/{len(folders)}: {folder_name}")
                    # 继续处理下一个文件夹
                    continue
            
            logger.info(f"Folder sync completed. Successfully synced {success_count}/{len(folders)} folders")
            
        except Exception as e:
            logger.error(f"Folder sync failed: {e}")
            # 确保在出错时也切换回main分支
            try:
                self.run_git_command(self.apps_repo_path, ["checkout", "main"])
            except:
                pass
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="同步terminus-apps-origin仓库中的指定文件夹到apps仓库")
    parser.add_argument("--dry-run", action="store_true", help="只显示将要同步的文件夹，不实际执行")
    parser.add_argument("--config", default="sync_config.json", help="配置文件路径")
    parser.add_argument("--folders", default="folders_to_sync.txt", help="文件夹列表文件路径")
    parser.add_argument("--folder", help="同步单个文件夹名称")
    parser.add_argument("--list-file", help="指定文件夹列表文件路径（覆盖--folders参数）")
    
    args = parser.parse_args()
    
    try:
        # 确定使用哪个文件夹列表文件
        folders_file = args.list_file if args.list_file else args.folders
        
        manager = FolderSyncManager(args.config, folders_file)
        
        if args.folder:
            # 单个文件夹同步模式
            logger.info(f"Single folder sync mode: {args.folder}")
            manager.sync_single_folder(args.folder, dry_run=args.dry_run)
        else:
            # 列表同步模式
            logger.info(f"List sync mode: {folders_file}")
            manager.sync_all_folders(dry_run=args.dry_run)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
