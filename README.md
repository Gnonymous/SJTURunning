# SJTU 校园跑步工具 🏃

一键生成并上传 SJTU 校园跑步数据的桌面工具。

## ✨ 功能特点

- 🔐 自动登录 SJTU Jaccount（含验证码自动识别）
- 📍 自动生成 GPS 跑步轨迹
- ⚡ 批量上传多天跑步记录
- 🎲 支持随机跑步时间
- 🎨 简洁易用的图形界面

## 🚀 快速开始

### macOS / Linux

```bash
# 安装依赖
pip3 install PySide6 requests tenacity

# 运行
python3 qtui.py
```

### Windows

```bash
pip install PySide6 requests tenacity
python qtui.py
```

## ⚙️ 配置说明

修改 `config.json` 即可自定义参数：

```json
{
  "跑步天数": 25,
  "每日距离_米": 5000,
  "配速_分钟每公里": 3.5,
  "跑步时间随机": true,
  "随机时间范围_开始时": 7,
  "随机时间范围_结束时": 20
}
```

| 参数 | 说明 |
|------|------|
| `跑步天数` | 往前生成多少天记录 |
| `每日距离_米` | 每天跑步距离（米） |
| `配速_分钟每公里` | 跑步配速 |
| `跑步时间随机` | `true` 随机时间 / `false` 固定时间 |

## 📁 项目结构

```
├── config.json          # 配置文件
├── qtui.py              # GUI 入口
├── src/
│   ├── main.py          # 核心逻辑
│   ├── login.py         # 登录模块
│   ├── api_client.py    # API 客户端
│   └── data_generator.py # 数据生成
└── utils/
    └── auxiliary_util.py # 工具函数
```

## ⚠️ 免责声明

本工具仅供学习和研究目的，开发者不对因使用本工具造成的任何后果负责。请遵守学校相关规定。

---

**版本**: 2.0.0 | **日期**: 2025-12-14
