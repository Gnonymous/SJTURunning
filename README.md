# SJTU 校园跑步工具 🏃

一键生成并上传 SJTU 校园跑步数据的桌面工具。

## ✨ 功能特点

- 🔐 自动登录 SJTU Jaccount（含验证码识别）
- 📍 自动生成 GPS 跑步轨迹
- ⚡ 批量上传多天跑步记录
- 🎲 支持随机距离、配速、时间
- 📅 支持指定日期或按天数生成
- 🎨 简洁易用的图形界面

## 🚀 快速开始

### macOS / Linux

```bash
pip3 install PySide6 requests tenacity
python3 qtui.py
```

### Windows

```bash
pip install PySide6 requests tenacity
python qtui.py
```

## ⚙️ 配置说明

修改 `config.json` 或在界面中设置后点击 **保存配置**：

| 参数 | 说明 |
|------|------|
| `指定日期模式` | `true` 使用指定日期 / `false` 按天数往前推 |
| `指定日期列表` | 格式 `YYYY-MM-DD`，用英文逗号分隔 |
| `跑步天数` | 往前生成多少天（指定日期模式=false时生效） |
| `参数随机` | `true` 随机距离和配速 / `false` 使用固定值 |
| `每日距离_米` | 固定距离（参数随机=false时生效） |
| `配速_分钟每公里` | 固定配速（参数随机=false时生效） |
| `距离最小_米` / `距离最大_米` | 随机距离范围 |
| `配速最小_分钟每公里` / `配速最大_分钟每公里` | 随机配速范围 |
| `跑步时间随机` | `true` 随机时间 / `false` 固定时间 |

## 📁 项目结构

```
├── config.json          # 配置文件
├── qtui.py              # GUI 入口
├── src/
│   ├── main.py          # 核心逻辑
│   ├── login.py         # 登录模块
│   ├── config.py        # 配置加载
│   ├── api_client.py    # API 客户端
│   └── data_generator.py # 数据生成
└── utils/
    └── auxiliary_util.py # 工具函数
```

## ⚠️ 免责声明

本工具仅供学习和研究，开发者不对因使用本工具造成的任何后果负责。请遵守学校相关规定。

---

**版本**: 2.0.0 | **更新**: 2025-12-14
