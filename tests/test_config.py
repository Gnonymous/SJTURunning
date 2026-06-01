import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from src import config


class GetConfigPathTests(unittest.TestCase):
    def test_source_mode_uses_project_root(self):
        # 未打包(无 sys.frozen)时,配置应位于项目根目录,保持本地调试行为不变
        with patch.object(config, "_is_frozen", return_value=False):
            path = config.get_config_path()
        expected = config._project_config_path()
        self.assertEqual(path, expected)
        self.assertTrue(path.endswith("config.json"))

    def test_frozen_mode_uses_writable_user_dir_not_program_dir(self):
        # 打包运行时,配置必须落在可写的用户目录,而非只读程序目录/临时解包目录
        with tempfile.TemporaryDirectory() as fake_home:
            user_dir = os.path.join(fake_home, "AppData")
            with patch.object(config, "_is_frozen", return_value=True), \
                 patch.object(config, "_user_config_dir", return_value=user_dir):
                path = config.get_config_path()

            self.assertTrue(os.path.isdir(user_dir))
            self.assertEqual(os.path.dirname(path), user_dir)
            self.assertTrue(path.endswith("config.json"))
            # 可写性验证:能在该目录真实写入文件
            with open(path, "w", encoding="utf-8") as f:
                f.write("{}")
            self.assertTrue(os.path.exists(path))

    def test_frozen_mode_migrates_legacy_config_next_to_executable(self):
        # 首次启动时,迁移可执行文件同级目录里已有的旧 config.json
        with tempfile.TemporaryDirectory() as exe_dir, \
             tempfile.TemporaryDirectory() as fake_home:
            legacy_path = os.path.join(exe_dir, "config.json")
            with open(legacy_path, "w", encoding="utf-8") as f:
                f.write('{"跑步天数": 99}')

            fake_exe = os.path.join(exe_dir, "SJTURunning")
            user_dir = os.path.join(fake_home, "cfg")

            with patch.object(config, "_is_frozen", return_value=True), \
                 patch.object(config, "_user_config_dir", return_value=user_dir), \
                 patch.object(sys, "executable", fake_exe):
                path = config.get_config_path()

            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                self.assertIn("跑步天数", f.read())


if __name__ == "__main__":
    unittest.main()
