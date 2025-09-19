#!/bin/bash

# 文件夹同步脚本启动器
# 使用方法: 
#   ./run_folder_sync.sh [--dry-run]                    # 同步列表中的所有文件夹
#   ./run_folder_sync.sh --folder <folder_name>         # 同步单个文件夹
#   ./run_folder_sync.sh --list-file <file_path>        # 使用指定的列表文件

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 检查依赖是否安装
if [ ! -f "venv/bin/activate" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 显示使用帮助
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "文件夹同步脚本使用说明："
    echo ""
    echo "1. 同步列表中的所有文件夹："
    echo "   ./run_folder_sync.sh [--dry-run]"
    echo ""
    echo "2. 同步单个文件夹："
    echo "   ./run_folder_sync.sh --folder <folder_name> [--dry-run]"
    echo ""
    echo "3. 使用指定的列表文件："
    echo "   ./run_folder_sync.sh --list-file <file_path> [--dry-run]"
    echo ""
    echo "4. 查看详细帮助："
    echo "   python3 sync_folders.py --help"
    echo ""
    exit 0
fi

# 运行文件夹同步脚本
echo "运行文件夹同步脚本..."
python3 sync_folders.py "$@"
