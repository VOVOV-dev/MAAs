"""明日方舟 MAA 适配器。"""
import os
import subprocess

from .base import GameAdapter, GAME_DIRS


class MaaAdapter(GameAdapter):
    name = "maa"
    display_name = "明日方舟 MAA"
    process_names = ["MAA"]
    game_dir = GAME_DIRS["maa"]
    folder_patterns = [r"MAA-v", r"MaaAssistantArknights"]
    exe_names = ["MAA.exe"]

    def start(self):
        if not self.resolve():
            return False
        self.log("启动 {}".format(self.exe_path))
        subprocess.Popen([self.exe_path], cwd=self.game_dir)

    def apply_config(self, config_name):
        self.resolve()
        cfg = self.load_config_file(config_name)
        target = cfg.pop("target", None) or os.path.join(
            self.game_dir, "config", "gui.json")
        self.merge_json_file(target, cfg)
