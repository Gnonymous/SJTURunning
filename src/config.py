import json
import os

global_version = "2.0.0"

def get_config_path():
    """获取 config.json 的路径"""
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    return os.path.join(root_dir, "config.json")

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