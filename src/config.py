import json
import os
import shutil
import sys

global_version = "2.1.1"

APP_NAME = "SJTURunning"

def _is_frozen():
    """是否运行于 PyInstaller 等打包环境。"""
    return getattr(sys, "frozen", False)

def _user_config_dir():
    """按平台返回用户可写的配置目录。"""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, APP_NAME)

def _project_config_path():
    """源码运行时的配置路径(项目根目录)。"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    return os.path.join(root_dir, "config.json")

def get_config_path():
    """获取 config.json 的路径。

    源码运行时使用项目根目录,便于本地调试;打包运行时(PyInstaller)写入
    用户可写目录(macOS: ~/Library/Application Support/SJTURunning,
    Windows: %APPDATA%\\SJTURunning),避免写入只读的程序目录或重启即清空的
    临时解包目录导致 [Errno 30] Read-only file system 或配置丢失。
    """
    if not _is_frozen():
        return _project_config_path()

    config_dir = _user_config_dir()
    try:
        os.makedirs(config_dir, exist_ok=True)
    except OSError:
        # 极端情况下用户目录不可写,退回临时目录,至少本次运行可用
        import tempfile
        config_dir = os.path.join(tempfile.gettempdir(), APP_NAME)
        os.makedirs(config_dir, exist_ok=True)

    config_path = os.path.join(config_dir, "config.json")

    # 一次性迁移:若用户目录尚无配置,但可执行文件同级存在旧 config.json,则迁移过来
    if not os.path.exists(config_path):
        legacy_path = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "config.json")
        if os.path.exists(legacy_path) and os.path.abspath(legacy_path) != os.path.abspath(config_path):
            try:
                shutil.copyfile(legacy_path, config_path)
            except OSError:
                pass

    return config_path

def load_config():
    """从 config.json 加载配置"""
    config_path = get_config_path()
    
    # 默认配置
    default_config = {
        "指定日期模式": False,
        "指定日期列表": [],
        "跑步天数": 25,
        "每日距离_米": 5000,
        "配速_分钟每公里": 3.5,
        "GPS采样间隔_秒": 3,
        "跑步时间随机": False,
        "固定跑步时间_时": 8,
        "固定跑步时间_分": 0,
        "随机时间范围_开始时": 7,
        "随机时间范围_结束时": 20,
        "起点纬度": 31.031599,
        "起点经度": 121.442938,
        "终点纬度": 31.0264,
        "终点经度": 121.4551
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 合并用户配置和默认配置
                default_config.update(user_config)
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认配置")
    
    return default_config