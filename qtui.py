import sys
import os
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QProgressBar, QFormLayout, QGroupBox, QDateTimeEdit,
    QMessageBox, QScrollArea, QSizePolicy, QCheckBox, QSpinBox, QDoubleSpinBox,
    QSpacerItem, QRadioButton, QButtonGroup, QFrame
)
from PySide6.QtCore import QThread, Signal, QDateTime, Qt, QUrl, QEvent, QTimer
from PySide6.QtGui import QTextCursor, QFont, QColor, QTextCharFormat, QPalette, QBrush, QIcon, QDesktopServices

from src.main import run_sports_upload
import src.login as login
from src.config import load_config
from utils.auxiliary_util import SportsUploaderError, get_base_path
import src.config as config


from src.info_dialog import HelpWidget

RESOURCES_SUB_DIR = "assets"

RESOURCES_FULL_PATH = os.path.join(get_base_path(), RESOURCES_SUB_DIR)

class WorkerThread(QThread):
    """
    工作线程，用于在后台执行跑步数据上传任务，避免UI冻结。
    """
    progress_update = Signal(int, int, str)
    log_output = Signal(str, str)
    finished = Signal(bool, str)

    def __init__(self, config_data):
        super().__init__()
        self.config_data = config_data

    def run(self):
        success = False
        message = "任务已完成。"
        try:
            success, message = run_sports_upload(
                self.config_data,
                progress_callback=self.progress_callback,
                log_cb=self.log_callback,
                stop_check_cb=self.isInterruptionRequested
            )
        except SportsUploaderError as e:
            self.log_output.emit(f"任务中断: {e}", "error")
            message = str(e)
            success = False
        except Exception as e:
            self.log_output.emit(f"发生未预期的错误: {e}", "error")
            message = f"未预期的错误: {e}"
            success = False
        finally:
            if self.isInterruptionRequested() and not success:
                 self.finished.emit(False, "任务已手动终止。")
            else:
                 self.finished.emit(success, message)

    def progress_callback(self, current, total, message):
        self.progress_update.emit(current, total, message)

    def log_callback(self, message, level):
        self.log_output.emit(message, level)


class SportsUploaderUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SJTU 校园轻松跑 - Version " + config.global_version)
        self.setWindowIcon(QIcon(os.path.join(RESOURCES_FULL_PATH, "SJTURM.png")))

        # 存储对外部工作线程的引用
        self._thread = None
        # 关于窗口引用，防止被垃圾回收
        self._help_window = None

        # 加载配置（供 get_settings_from_ui 使用原始 config 引用）
        self.config = load_config()

        # 自动保存防抖定时器（500ms 延迟）
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.setInterval(500)
        self._auto_save_timer.timeout.connect(self._auto_save_config)

        self.setup_ui_style()
        self.init_ui()

        # 设置最小和最大窗口大小供用户调节
        # 最小：确保基本元素可用（如 320 宽）
        # 最大：限制为主显示器可用区域宽度，以避免内容拉伸过多
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                available_width = 600
            else:
                available_width = screen.availableGeometry().width()
        except Exception:
            available_width = 600
        self.setGeometry(300, 100, 500, 650)
        self.setMinimumSize(450, 550)

        # 根据当前窗口宽度调整内容区域宽度
        self.adjust_content_width(self.width())
        # 启动时居中主窗口
        try:
            self.center_window()
        except Exception:
            pass

    def setup_ui_style(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.WindowText, QColor(51, 51, 51))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(51, 51, 51))
        palette.setColor(QPalette.Text, QColor(51, 51, 51))
        palette.setColor(QPalette.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ButtonText, QColor(51, 51, 51))
        palette.setColor(QPalette.BrightText, QColor("red"))
        palette.setColor(QPalette.Link, QColor(74, 144, 226))
        palette.setColor(QPalette.Highlight, QColor(74, 144, 226))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)

        self.setStyleSheet("""
            QWidget, QScrollArea, QGroupBox {
                background-color: rgb(255, 255, 255);
            }

            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                margin-top: 15px;
                border: 1px solid rgb(220, 220, 220);
                border-radius: 6px;
                padding-top: 25px;
                padding-bottom: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                color: rgb(74, 144, 226);
            }
            QLineEdit, QDateTimeEdit {
                background-color: rgb(255, 255, 255);
                border: 1px solid rgb(204, 204, 204);
                border-radius: 4px;
                padding: 8px;
                selection-background-color: rgb(74, 144, 226);
                color: rgb(51, 51, 51);
            }
            QLineEdit:focus, QDateTimeEdit:focus {
                border: 1px solid rgb(74, 144, 226);
            }
            QDateTimeEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: rgb(204, 204, 204);
                border-left-style: solid;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QPushButton {
                background-color: rgb(255, 255, 255);
                color: rgb(51, 51, 51);
                border: 1px solid rgb(204, 204, 204);
                border-radius: 4px;
                padding: 8px 16px;
                min-height: 24px;
                max-height: 36px;
            }
            QPushButton:hover {
                border: 1px solid rgb(74, 144, 226);
                background-color: rgb(250, 250, 250);
            }
            QPushButton:pressed {
                background-color: rgb(240, 240, 240);
            }
            QPushButton:disabled {
                background-color: rgb(255, 255, 255);
                color: rgb(180, 180, 180);
                border: 1px solid rgb(230, 230, 230);
            }
            QProgressBar {
                border: 1px solid rgb(220, 220, 220);
                border-radius: 4px;
                text-align: center;
                background-color: rgb(255, 255, 255);
                color: rgb(51, 51, 51);
                max-height: 20px;
            }
            QProgressBar::chunk {
                background-color: rgb(74, 144, 226);
                border-radius: 4px;
            }
            QTextEdit {
                background-color: rgb(245, 245, 247);
                border: 1px solid rgb(220, 220, 220);
                border-radius: 4px;
                padding: 8px;
                color: rgb(51, 51, 51);
            }
            QScrollArea {
                border: none;
            }
            QCheckBox {
                spacing: 8px;
                color: rgb(51, 51, 51);
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid rgb(180, 180, 180);
                background-color: rgb(255, 255, 255);
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgb(74, 144, 226);
            }
            QCheckBox::indicator:checked {
                background-color: rgb(76, 175, 80);
                border: 2px solid rgb(76, 175, 80);
            }
            QCheckBox::indicator:disabled {
                border: 2px solid rgb(220, 220, 220);
                background-color: rgb(245, 245, 245);
            }
            QFormLayout QLabel {
                padding-top: 8px;
                padding-bottom: 8px;
                color: rgb(102, 102, 102);
            }
            #startButton {
                background-color: rgb(76, 175, 80);
                color: white;
                border: 1px solid rgb(76, 175, 80);
            }
            #startButton:hover {
                background-color: rgb(67, 160, 71);
                border: 1px solid rgb(67, 160, 71);
            }
            #startButton:pressed {
                background-color: rgb(56, 142, 60);
            }
            #stopButton {
                background-color: rgb(220, 53, 69);
                color: white;
                border: 1px solid rgb(220, 53, 69);
            }
            #stopButton:hover {
                background-color: rgb(179, 43, 56);
                border: 1px solid rgb(179, 43, 56);
            }
            #stopButton:pressed {
                background-color: rgb(140, 34, 44);
            }
            QLabel#getCookieLink {
                color: rgb(74, 144, 226);
                text-decoration: underline;
                padding: 0;
            }
            QLabel#getCookieLink:hover {
                color: rgb(52, 120, 198);
            }
        """)

    def init_ui(self):
        top_h_layout = QHBoxLayout()
        top_h_layout.setContentsMargins(20, 20, 20, 20)
        top_h_layout.setSpacing(0)

        self.center_widget = QWidget()
        main_layout = QVBoxLayout(self.center_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_content = QWidget()
        scroll_layout = QVBoxLayout(self.scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_content)

        main_layout.addWidget(self.scroll_area)

        user_group = QGroupBox("用户配置")
        user_form_layout = QFormLayout()
        user_form_layout.setVerticalSpacing(15)
        user_form_layout.setContentsMargins(15, 15, 15, 15)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Jaccount用户名")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)

        user_form_layout.addRow("用户名:", self.username_input)
        user_form_layout.addRow("密码:", self.password_input)
        user_group.setLayout(user_form_layout)
        scroll_layout.addWidget(user_group)

        # ========== 跑步配置区域 ==========
        run_group = QGroupBox("跑步配置")
        run_layout = QVBoxLayout()
        run_layout.setContentsMargins(15, 20, 15, 15)
        run_layout.setSpacing(15)

        # 加载当前配置
        app_config = load_config()

        # --- 模式选择 ---
        mode_layout = QHBoxLayout()
        mode_label = QLabel("生成模式:")
        mode_label.setStyleSheet("font-weight: bold; color: #333;")
        self.mode_days_radio = QRadioButton("按天数往前推")
        self.mode_dates_radio = QRadioButton("指定日期")
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.mode_days_radio, 0)
        self.mode_group.addButton(self.mode_dates_radio, 1)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_days_radio)
        mode_layout.addWidget(self.mode_dates_radio)
        mode_layout.addStretch()
        run_layout.addLayout(mode_layout)

        # --- 天数设置容器 (可切换显示) ---
        self.days_widget = QWidget()
        days_inner_layout = QHBoxLayout(self.days_widget)
        days_inner_layout.setContentsMargins(0, 0, 0, 0)
        days_label = QLabel("往前推天数:")
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 100)
        self.days_spin.setValue(app_config.get("跑步天数", 25))
        self.days_spin.setFixedWidth(100)
        self.days_spin.valueChanged.connect(self._schedule_auto_save)
        days_hint = QLabel("天 (从昨天开始)")
        days_hint.setStyleSheet("color: #888;")
        days_inner_layout.addWidget(days_label)
        days_inner_layout.addWidget(self.days_spin)
        days_inner_layout.addWidget(days_hint)
        days_inner_layout.addStretch()
        run_layout.addWidget(self.days_widget)

        # --- 指定日期容器 (可切换显示) ---
        self.dates_widget = QWidget()
        dates_inner_layout = QVBoxLayout(self.dates_widget)
        dates_inner_layout.setContentsMargins(0, 0, 0, 0)
        dates_inner_layout.setSpacing(8)
        dates_label = QLabel("指定日期 (用英文逗号分隔):")
        self.dates_input = QLineEdit()
        self.dates_input.setPlaceholderText("例如: 2025-12-13, 2025-12-10")
        dates_list = app_config.get("指定日期列表", [])
        self.dates_input.setText(", ".join(dates_list) if dates_list else "")
        self.dates_input.textChanged.connect(self._schedule_auto_save)
        dates_inner_layout.addWidget(dates_label)
        dates_inner_layout.addWidget(self.dates_input)
        run_layout.addWidget(self.dates_widget)

        # 设置初始模式并连接信号
        if app_config.get("指定日期模式", False):
            self.mode_dates_radio.setChecked(True)
            self.days_widget.hide()
            self.dates_widget.show()
        else:
            self.mode_days_radio.setChecked(True)
            self.days_widget.show()
            self.dates_widget.hide()
        
        # 连接模式切换信号（同时触发自动保存）
        self.mode_days_radio.toggled.connect(self.on_mode_changed)
        self.mode_days_radio.toggled.connect(self._schedule_auto_save)

        # 分隔线
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFixedHeight(1)
        line1.setStyleSheet("background-color: #e0e0e0;")
        run_layout.addWidget(line1)

        # --- 距离和配速 ---
        dist_pace_label = QLabel("跑步参数")
        dist_pace_label.setStyleSheet("font-weight: bold; color: #333;")
        run_layout.addWidget(dist_pace_label)

        self.random_params_check = QCheckBox("使用随机参数（更真实）")
        self.random_params_check.setChecked(app_config.get("参数随机", False))
        self.random_params_check.toggled.connect(self.on_params_mode_changed)
        self.random_params_check.toggled.connect(self._schedule_auto_save)
        run_layout.addWidget(self.random_params_check)

        # 固定参数容器
        self.fixed_params_widget = QWidget()
        fixed_params_layout = QHBoxLayout(self.fixed_params_widget)
        fixed_params_layout.setContentsMargins(20, 0, 0, 0)
        fixed_params_layout.setSpacing(15)
        
        dist_label = QLabel("距离:")
        self.dist_spin = QSpinBox()
        self.dist_spin.setRange(1000, 20000)
        self.dist_spin.setSingleStep(500)
        self.dist_spin.setValue(app_config.get("每日距离_米", 5000))
        self.dist_spin.setFixedWidth(100)
        self.dist_spin.valueChanged.connect(self._schedule_auto_save)
        self.dist_spin.setSuffix(" 米")
        
        pace_label = QLabel("配速:")
        self.pace_spin = QDoubleSpinBox()
        self.pace_spin.setRange(3.0, 9.0)
        self.pace_spin.setSingleStep(0.5)
        self.pace_spin.setValue(app_config.get("配速_分钟每公里", 3.5))
        self.pace_spin.setFixedWidth(100)
        self.pace_spin.valueChanged.connect(self._schedule_auto_save)
        self.pace_spin.setSuffix(" 分/km")
        
        fixed_params_layout.addWidget(dist_label)
        fixed_params_layout.addWidget(self.dist_spin)
        fixed_params_layout.addSpacing(20)
        fixed_params_layout.addWidget(pace_label)
        fixed_params_layout.addWidget(self.pace_spin)
        fixed_params_layout.addStretch()
        run_layout.addWidget(self.fixed_params_widget)

        # 随机参数容器
        self.random_params_widget = QWidget()
        random_params_main = QVBoxLayout(self.random_params_widget)
        random_params_main.setContentsMargins(20, 0, 0, 0)
        random_params_main.setSpacing(8)

        # 距离范围
        dist_range_layout = QHBoxLayout()
        dist_range_label = QLabel("距离范围:")
        self.dist_min_spin = QSpinBox()
        self.dist_min_spin.setRange(1000, 20000)
        self.dist_min_spin.setSingleStep(500)
        self.dist_min_spin.setValue(app_config.get("距离最小_米", 4000))
        self.dist_min_spin.setFixedWidth(90)
        self.dist_min_spin.setSuffix(" 米")
        self.dist_min_spin.valueChanged.connect(self._schedule_auto_save)
        dist_to = QLabel("~")
        self.dist_max_spin = QSpinBox()
        self.dist_max_spin.setRange(1000, 20000)
        self.dist_max_spin.setSingleStep(500)
        self.dist_max_spin.setValue(app_config.get("距离最大_米", 6000))
        self.dist_max_spin.setFixedWidth(90)
        self.dist_max_spin.setSuffix(" 米")
        self.dist_max_spin.valueChanged.connect(self._schedule_auto_save)
        dist_range_layout.addWidget(dist_range_label)
        dist_range_layout.addWidget(self.dist_min_spin)
        dist_range_layout.addWidget(dist_to)
        dist_range_layout.addWidget(self.dist_max_spin)
        dist_range_layout.addStretch()
        random_params_main.addLayout(dist_range_layout)

        # 配速范围
        pace_range_layout = QHBoxLayout()
        pace_range_label = QLabel("配速范围:")
        self.pace_min_spin = QDoubleSpinBox()
        self.pace_min_spin.setRange(3.0, 9.0)
        self.pace_min_spin.setSingleStep(0.5)
        self.pace_min_spin.setValue(app_config.get("配速最小_分钟每公里", 3.5))
        self.pace_min_spin.setFixedWidth(90)
        self.pace_min_spin.setSuffix(" 分")
        self.pace_min_spin.valueChanged.connect(self._schedule_auto_save)
        pace_to = QLabel("~")
        self.pace_max_spin = QDoubleSpinBox()
        self.pace_max_spin.setRange(3.0, 9.0)
        self.pace_max_spin.setSingleStep(0.5)
        self.pace_max_spin.setValue(app_config.get("配速最大_分钟每公里", 5.0))
        self.pace_max_spin.setFixedWidth(90)
        self.pace_max_spin.setSuffix(" 分")
        self.pace_max_spin.valueChanged.connect(self._schedule_auto_save)
        pace_range_layout.addWidget(pace_range_label)
        pace_range_layout.addWidget(self.pace_min_spin)
        pace_range_layout.addWidget(pace_to)
        pace_range_layout.addWidget(self.pace_max_spin)
        pace_range_layout.addStretch()
        random_params_main.addLayout(pace_range_layout)

        run_layout.addWidget(self.random_params_widget)

        # 初始化参数模式显示
        self.on_params_mode_changed(self.random_params_check.isChecked())

        # 分隔线
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFixedHeight(1)
        line2.setStyleSheet("background-color: #e0e0e0;")
        run_layout.addWidget(line2)

        # --- 时间设置 ---
        time_label = QLabel("跑步时间")
        time_label.setStyleSheet("font-weight: bold; color: #333;")
        run_layout.addWidget(time_label)

        self.random_time_check = QCheckBox("使用随机时间（更真实）")
        self.random_time_check.setChecked(app_config.get("跑步时间随机", False))
        self.random_time_check.toggled.connect(self.on_time_mode_changed)
        self.random_time_check.toggled.connect(self._schedule_auto_save)
        run_layout.addWidget(self.random_time_check)

        # 固定时间容器
        self.fixed_time_widget = QWidget()
        fixed_time_layout = QHBoxLayout(self.fixed_time_widget)
        fixed_time_layout.setContentsMargins(20, 0, 0, 0)
        fixed_label = QLabel("固定时间:")
        self.fixed_hour_spin = QSpinBox()
        self.fixed_hour_spin.setRange(0, 23)
        self.fixed_hour_spin.setValue(app_config.get("固定跑步时间_时", 8))
        self.fixed_hour_spin.setFixedWidth(60)
        self.fixed_hour_spin.valueChanged.connect(self._schedule_auto_save)
        hour_label = QLabel(":")
        self.fixed_min_spin = QSpinBox()
        self.fixed_min_spin.setRange(0, 59)
        self.fixed_min_spin.setValue(app_config.get("固定跑步时间_分", 0))
        self.fixed_min_spin.valueChanged.connect(self._schedule_auto_save)
        self.fixed_min_spin.setFixedWidth(60)
        fixed_time_layout.addWidget(fixed_label)
        fixed_time_layout.addWidget(self.fixed_hour_spin)
        fixed_time_layout.addWidget(hour_label)
        fixed_time_layout.addWidget(self.fixed_min_spin)
        fixed_time_layout.addStretch()
        run_layout.addWidget(self.fixed_time_widget)

        # 随机时间范围容器
        self.random_time_widget = QWidget()
        random_time_layout = QHBoxLayout(self.random_time_widget)
        random_time_layout.setContentsMargins(20, 0, 0, 0)
        random_label = QLabel("随机范围:")
        self.rand_start_spin = QSpinBox()
        self.rand_start_spin.setRange(0, 23)
        self.rand_start_spin.setValue(app_config.get("随机时间范围_开始时", 7))
        self.rand_start_spin.setFixedWidth(60)
        self.rand_start_spin.valueChanged.connect(self._schedule_auto_save)
        to_label = QLabel("~")
        self.rand_end_spin = QSpinBox()
        self.rand_end_spin.setRange(0, 23)
        self.rand_end_spin.setValue(app_config.get("随机时间范围_结束时", 20))
        self.rand_end_spin.setFixedWidth(60)
        self.rand_end_spin.valueChanged.connect(self._schedule_auto_save)
        end_label = QLabel("时")
        random_time_layout.addWidget(random_label)
        random_time_layout.addWidget(self.rand_start_spin)
        random_time_layout.addWidget(to_label)
        random_time_layout.addWidget(self.rand_end_spin)
        random_time_layout.addWidget(end_label)
        random_time_layout.addStretch()
        run_layout.addWidget(self.random_time_widget)

        # 初始化时间模式显示
        self.on_time_mode_changed(self.random_time_check.isChecked())

        # 自动保存提示文字（绿色，表示配置会自动保存）
        hint_label = QLabel("✅ 配置修改后将自动保存")
        hint_label.setStyleSheet("color: #4CAF50; font-size: 12px; padding: 8px 0;")
        run_layout.addWidget(hint_label)

        run_group.setLayout(run_layout)
        scroll_layout.addWidget(run_group)


        action_button_layout = QHBoxLayout()
        action_button_layout.setSpacing(12)
        self.start_button = QPushButton("一键跑步")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.start_upload)
        action_button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("停止")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_upload)
        action_button_layout.addWidget(self.stop_button)

        self.info_button = QPushButton("关于")
        self.info_button.clicked.connect(self.show_info_dialog)
        action_button_layout.addWidget(self.info_button)

        scroll_layout.addLayout(action_button_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        scroll_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("状态: 待命")
        scroll_layout.addWidget(self.status_label)
        
        self.log_output_area = QTextEdit()
        self.log_output_area.setReadOnly(True)
        self.log_output_area.setFont(QFont("Monospace", 9))
        self.log_output_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_layout.addWidget(self.log_output_area)

        top_h_layout.addWidget(self.center_widget)

        self.setLayout(top_h_layout)

    def on_mode_changed(self, checked):
        """模式切换：按天数 / 指定日期"""
        if self.mode_days_radio.isChecked():
            self.days_widget.show()
            self.dates_widget.hide()
        else:
            self.days_widget.hide()
            self.dates_widget.show()

    def on_time_mode_changed(self, use_random):
        """时间模式切换：随机 / 固定"""
        if use_random:
            self.fixed_time_widget.hide()
            self.random_time_widget.show()
        else:
            self.fixed_time_widget.show()
            self.random_time_widget.hide()

    def on_params_mode_changed(self, use_random):
        """参数模式切换：随机 / 固定"""
        if use_random:
            self.fixed_params_widget.hide()
            self.random_params_widget.show()
        else:
            self.fixed_params_widget.show()
            self.random_params_widget.hide()

    def resizeEvent(self, event):
        """
        槽函数，用于处理窗口大小调整事件。
        根据窗口宽度调整内部内容区域的最大宽度。
        """
        super().resizeEvent(event)
        self.adjust_content_width(event.size().width())

    def adjust_content_width(self, window_width):
        """
        根据给定的窗口宽度，计算并设置 center_widget 的固定宽度。
        """
        # 不强制很大的最小宽度，使用窗口宽度的 90% 或最大 600 的限制
        calculated_width = int(min(window_width * 0.9, 600))
        # 保证最小为 280，以适配窄窗口（比如 300px）
        calculated_width = max(280, calculated_width)
        self.center_widget.setFixedWidth(calculated_width)

    def center_window(self):
        """将主窗口居中到主显示器的可用区域中心。"""
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                return
            available = screen.availableGeometry()

            fg = self.frameGeometry()
            fg.moveCenter(available.center())
            self.move(fg.topLeft())
        except Exception:
            return

    def _schedule_auto_save(self):
        """触发自动保存（带防抖）"""
        self._auto_save_timer.start()

    def _auto_save_config(self):
        """静默自动保存配置到 config.json（不弹出提示框）"""
        import json
        from src.config import get_config_path
        
        try:
            # 解析指定日期列表
            dates_text = self.dates_input.text().strip()
            dates_list = []
            if dates_text:
                dates_list = [d.strip() for d in dates_text.split(",") if d.strip()]
            
            new_config = {
                "// 说明": "SJTU 校园跑步工具配置文件",
                "指定日期模式": self.mode_dates_radio.isChecked(),
                "指定日期列表": dates_list,
                "跑步天数": self.days_spin.value(),
                "参数随机": self.random_params_check.isChecked(),
                "每日距离_米": self.dist_spin.value(),
                "配速_分钟每公里": self.pace_spin.value(),
                "距离最小_米": self.dist_min_spin.value(),
                "距离最大_米": self.dist_max_spin.value(),
                "配速最小_分钟每公里": self.pace_min_spin.value(),
                "配速最大_分钟每公里": self.pace_max_spin.value(),
                "GPS采样间隔_秒": 3,
                "跑步时间随机": self.random_time_check.isChecked(),
                "固定跑步时间_时": self.fixed_hour_spin.value(),
                "固定跑步时间_分": self.fixed_min_spin.value(),
                "随机时间范围_开始时": self.rand_start_spin.value(),
                "随机时间范围_结束时": self.rand_end_spin.value(),
                "起点纬度": 31.031599,
                "起点经度": 121.442938,
                "终点纬度": 31.0264,
                "终点经度": 121.4551
            }
            
            config_path = get_config_path()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=4)
            
            # 静默保存成功，不弹出提示框
        except Exception as e:
            # 自动保存失败时在日志中显示错误（不打扰用户）
            self.log_output_text(f"自动保存配置失败: {e}", "error")

    def get_settings_from_ui(self):
        """从UI获取当前配置并返回字典"""
        try:
            username = self.username_input.text().strip()
            password = self.password_input.text()

            current_config = {
                "USER_ID": username,
                "PASSWORD": password,
                "START_LATITUDE": float(self.config.get("START_LATITUDE", 31.031599)),
                "START_LONGITUDE": float(self.config.get("START_LONGITUDE", 121.442938)),
                "END_LATITUDE": float(self.config.get("END_LATITUDE", 31.0264)),
                "END_LONGITUDE": float(self.config.get("END_LONGITUDE", 121.4551)),
                "RUNNING_SPEED_MPS": round(1000.0 / (3.5 * 60), 3),
                "INTERVAL_SECONDS": int(self.config.get("INTERVAL_SECONDS", 3)),
                "HOST": "pe.sjtu.edu.cn",
                "UID_URL": "https://pe.sjtu.edu.cn/sports/my/uid",
                "MY_DATA_URL": "https://pe.sjtu.edu.cn/sports/my/data",
                "POINT_RULE_URL": "https://pe.sjtu.edu.cn/api/running/point-rule",
                "UPLOAD_URL": "https://pe.sjtu.edu.cn/api/running/result/upload"
            }

            # START_TIME_EPOCH_MS 由后端生成，不从 UI 获取

            if not current_config["USER_ID"] or not current_config["PASSWORD"]:
                raise ValueError("用户名和密码不能为空。")

            return current_config

        except ValueError as e:
            raise ValueError(f"输入错误: {e}")
        except Exception as e:
            raise Exception(f"获取配置时发生未知错误: {e}")

    def start_upload(self):
        # 先确保配置已保存
        self._auto_save_config()
        
        # 构建配置摘要供用户确认
        if self.mode_dates_radio.isChecked():
            date_info = f"指定日期: {self.dates_input.text().strip() or '(未填写)'}"
        else:
            date_info = f"往前推 {self.days_spin.value()} 天"
        
        if self.random_params_check.isChecked():
            params_info = f"距离: {self.dist_min_spin.value()}~{self.dist_max_spin.value()} 米\n配速: {self.pace_min_spin.value()}~{self.pace_max_spin.value()} 分/km"
        else:
            params_info = f"距离: {self.dist_spin.value()} 米\n配速: {self.pace_spin.value()} 分/km"
        
        if self.random_time_check.isChecked():
            time_info = f"随机时间: {self.rand_start_spin.value()}:00 ~ {self.rand_end_spin.value()}:00"
        else:
            time_info = f"固定时间: {self.fixed_hour_spin.value():02d}:{self.fixed_min_spin.value():02d}"
        
        # 获取用户名
        username = self.username_input.text().strip() or "(未填写)"
        
        confirm_msg = f"""请确认以下配置：

👤 用户
{username}

📅 日期设置
{date_info}

🏃 跑步参数 {'(随机)' if self.random_params_check.isChecked() else '(固定)'}
{params_info}

⏰ 时间设置 {'(随机)' if self.random_time_check.isChecked() else '(固定)'}
{time_info}

是否开始上传？"""
        
        reply = QMessageBox.question(
            self, 
            "确认配置", 
            confirm_msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.log_output_area.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("状态: 准备中...")
        self.log_output_text("准备开始上传...", "info")

        try:
            current_config_to_send = self.get_settings_from_ui()
        except (ValueError, Exception) as e:
            self.log_output_text(f"配置错误: {e}", "error")
            self.status_label.setText("状态: 错误")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.info_button.setEnabled(False)
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)

        # 调用 login.py 获取 session，使用 UI 中的用户名/密码
        try:
            username = current_config_to_send.get("USER_ID")
            password = current_config_to_send.get("PASSWORD")
            session = login.login(username, password)
            current_config_to_send["SESSION"] = session
            # USER_ID 即 Jaccount 用户名
            current_config_to_send["USER_ID"] = username
        except Exception as e:
            self.log_output_text(f"登录失败: {e}", "error")
            QMessageBox.critical(self, "登录失败", str(e))
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.username_input.setEnabled(True)
            self.password_input.setEnabled(True)
            self.info_button.setEnabled(True)
            return

        self._thread = WorkerThread(current_config_to_send)
        self._thread.progress_update.connect(self.update_progress)
        self._thread.log_output.connect(self.log_output_text)
        self._thread.finished.connect(self.upload_finished)
        self._thread.start()

    def stop_upload(self):
        """请求工作线程停止。"""
        if self._thread and self._thread.isRunning():
            self._thread.requestInterruption()
            self.log_output_text("已发送停止请求，请等待任务清理并退出...", "warning")
            self.stop_button.setEnabled(False)
            self.status_label.setText("状态: 正在停止...")
        else:
            self.log_output_text("没有运行中的任务可以停止。", "info")


    def update_progress(self, current, total, message):
        """更新进度条和状态信息"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"状态: {message}")

    def log_output_text(self, message, level="info"):
        """将日志信息添加到文本区域，并根据级别着色"""
        cursor = self.log_output_area.textCursor()
        cursor.movePosition(QTextCursor.End)

        format = QTextCharFormat()
        if level == "error":
            format.setForeground(QColor("#DC3545"))
        elif level == "warning":
            format.setForeground(QColor("#FFA500"))
        elif level == "success":
            format.setForeground(QColor("#4CAF50"))
        else:
            format.setForeground(QColor("#333333"))

        # 如果是进度类短消息（例如: 已完成1/25），尝试替换最后一行以便在同一行更新
        try:
            if re.match(r"^已完成\d+/\d+", message):
                # 选择最后一段文本（最后一个 block）并检查是否包含“已完成”关键词
                doc = self.log_output_area.document()
                last_block = doc.lastBlock()
                if last_block.isValid() and "已完成" in last_block.text():
                    # 选中最后一个 block 并替换
                    cursor.movePosition(QTextCursor.End)
                    cursor.select(QTextCursor.BlockUnderCursor)
                    cursor.removeSelectedText()
                    # 插入新的进度信息（不额外换行），随后插入换行字符
                    cursor.insertText(f"[{level.upper()}] {message}\n", format)
                    self.log_output_area.ensureCursorVisible()
                    return
        except Exception:
            # 如果替换失败，退回到普通追加方式
            pass

        cursor.insertText(f"[{level.upper()}] {message}\n", format)
        self.log_output_area.ensureCursorVisible()

    def upload_finished(self, success, message):
        """上传任务完成后的处理"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.info_button.setEnabled(True)
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)

        self.progress_bar.setValue(100)

        if success:
            self.status_label.setText("状态: 上传成功！")
            self.log_output_text(f"操作完成: {message}", "success")
            QMessageBox.information(self, "上传结果", message)
        else:
            self.status_label.setText("状态: 上传失败！")
            self.log_output_text(f"操作失败: {message}", "error")

        self._thread = None


    def show_info_dialog(self):
        """显示关于对话框（非模态）。

        使用 HelpWidget，作为非模态窗口显示，并保留对实例的引用以防止被垃圾回收。
        当窗口关闭时清理引用。
        """
        try:
            # 如果已有关于窗口实例：
            # - 若窗口仍可见，则激活并返回；
            # - 若已被隐藏/关闭但引用未清理，则清理引用并继续创建新的实例
            existing = getattr(self, "_help_window", None)
            if existing is not None:
                try:
                    if existing.isVisible():
                        try:
                            existing.activateWindow()
                            existing.raise_()
                        except Exception:
                            pass
                        return
                    else:
                        # 已存在但不可见，尝试移除事件过滤并清理引用以便重新创建
                        try:
                            existing.removeEventFilter(self)
                        except Exception:
                            pass
                        self._help_window = None
                except Exception:
                    self._help_window = None

            # 创建 HelpWidget 实例并以非模态方式显示
            self._help_window = HelpWidget()
            self._help_window.setWindowModality(Qt.WindowModality.NonModal)
            try:
                self._help_window.installEventFilter(self)
            except Exception:
                pass

            def _on_help_destroyed():
                try:
                    if getattr(self, "_help_window", None) is not None:
                        self._help_window = None
                except Exception:
                    self._help_window = None

            try:
                self._help_window.destroyed.connect(_on_help_destroyed)
            except Exception:
                pass

            # 显示窗口（非模态）
            self._help_window.show()

        except Exception as e:
            # 记录异常并弹出对话框，不影响后台线程
            self.log_output_text(f"无法显示关于窗口: {e}", "error")
            QMessageBox.warning(self, "显示失败", f"无法显示关于窗口: {e}")

    def eventFilter(self, watched, event):
        """拦截 HelpWidget 的 Close/Hide 事件，清理保存的引用以允许再次打开。"""
        try:
            if watched is getattr(self, "_help_window", None):
                # 使用数值来避免某些静态类型检查器对 QEvent 枚举成员的误报
                ev_type = event.type()
                if ev_type in (19, 5):  # 19 = Close, 5 = Hide
                    try:
                        watched.removeEventFilter(self)
                    except Exception:
                        pass
                    self._help_window = None
        except Exception:
            pass

        return super().eventFilter(watched, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = SportsUploaderUI()
    ui.show()
    sys.exit(app.exec())