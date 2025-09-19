# 文件夹同步脚本

这个脚本用于将 terminus-apps-origin 仓库中指定的文件夹同步到 apps 仓库。

## 功能特性

- 从配置文件读取要同步的文件夹列表
- 逐个复制文件夹到apps目录，替换原有文件
- 自动检测文件夹版本（从Chart.yaml读取）
- 根据文件夹是否存在自动设置PR类型（NEW/UPDATE）
- 创建Draft Pull Request
- 如果没有修改内容则跳过PR创建
- 使用sync_config.json中的GitHub登录信息

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

1. **编辑文件夹列表文件** `folders_to_sync.txt`：
   ```
   # 要同步的文件夹列表，每行一个文件夹名称
   example-app
   another-app
   test-app
   ```

2. **确保GitHub配置正确**（使用sync_config.json）：
   - GitHub token
   - 用户名和邮箱

## 使用方法

### 基本用法

#### 1. 列表同步模式（默认）
```bash
# 同步列表中的所有文件夹
python3 sync_folders.py

# 干运行（只显示将要同步的文件夹）
python3 sync_folders.py --dry-run

# 指定配置文件
python3 sync_folders.py --config my_config.json --folders my_folders.txt

# 使用指定的列表文件
python3 sync_folders.py --list-file /path/to/custom_folders.txt
```

#### 2. 单个文件夹同步模式
```bash
# 同步单个文件夹
python3 sync_folders.py --folder chinesesubfinder

# 干运行单个文件夹
python3 sync_folders.py --folder chinesesubfinder --dry-run

# 指定配置文件同步单个文件夹
python3 sync_folders.py --folder rsshub --config my_config.json
```

### 使用启动脚本

```bash
# 给脚本执行权限
chmod +x run_folder_sync.sh

# 1. 同步列表中的所有文件夹
./run_folder_sync.sh
./run_folder_sync.sh --dry-run

# 2. 同步单个文件夹
./run_folder_sync.sh --folder chinesesubfinder
./run_folder_sync.sh --folder rsshub --dry-run

# 3. 使用指定的列表文件
./run_folder_sync.sh --list-file /path/to/custom_folders.txt

# 4. 查看帮助
./run_folder_sync.sh --help
```

### 命令行参数说明

- `--folder <name>`: 同步单个文件夹（优先级最高）
- `--list-file <path>`: 指定文件夹列表文件路径
- `--folders <path>`: 默认文件夹列表文件路径（默认：folders_to_sync.txt）
- `--config <path>`: 配置文件路径（默认：sync_config.json）
- `--dry-run`: 干运行模式，只显示将要同步的文件夹
- `--help`: 显示帮助信息

## 工作流程

1. **读取配置**：从sync_config.json读取GitHub信息
2. **读取文件夹列表**：从folders_to_sync.txt读取要同步的文件夹
3. **获取最新更改**：从两个仓库获取最新提交
4. **逐个处理文件夹**：
   - 检查源文件夹是否存在
   - 获取版本信息（从Chart.yaml）
   - 复制文件夹到apps仓库
   - 检查是否有修改内容
   - 如果没有修改，跳过并提示
   - 如果有修改，创建分支并提交
   - 推送分支到GitHub
   - 创建Draft PR

## PR规则

### PR标题格式
```
[PR Type][FolderName][version]
```

- **PR Type**: 
  - `NEW` - 如果目标分支中不存在同名文件夹
  - `UPDATE` - 如果目标分支中存在同名文件夹
- **FolderName**: 本次操作的文件夹名称
- **version**: 文件夹下Chart.yaml中version字段的值

### PR内容
- 文件夹名称
- 版本信息
- 同步类型
- 同步时间

## 日志

脚本会生成详细的日志，包括：
- 控制台输出
- `sync_folders.log` 文件

## 错误处理

- 如果某个文件夹同步失败，会继续处理下一个文件夹
- 详细的错误日志记录
- 自动跳过没有修改内容的文件夹

## 注意事项

- 确保有足够的权限访问两个仓库
- 文件夹必须存在于terminus-apps-origin目录下
- 建议先使用--dry-run模式测试
- 每次只操作一个文件夹，确保PR成功后再处理下一个
