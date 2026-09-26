"""星穹铁道 March7th 适配器。"""
import os
import subprocess

from .base import GameAdapter, GAME_DIRS


class March7thAdapter(GameAdapter):
    name = "march7th"
    display_name = "星穹铁道 March7th"
    process_names = ["March7th Assistant", "March7th Launcher"]
    game_dir = GAME_DIRS["march7th"]
    folder_patterns = [r"March7th", r"StarRail"]
    exe_names = ["March7th Assistant.exe", "March7th Launcher.exe"]
    # 游戏本体（星穹铁道）
    game_folder_patterns = [r"Star Rail", r"StarRail"]
    game_exe_names = ["StarRail.exe"]
    game_client = ""  # 留空，由 resolve_game_client 自动发现

    def start(self):
        if not self.resolve():
            return False
        # 自动发现游戏本体并写回 config.yaml，避免手动维护 game_path
        client = self.resolve_game_client()
        if client:
            self.replace_yaml_fields(
                os.path.join(self.game_dir, "config.yaml"),
                {"game_path": client})
        self.log("启动 {}".format(self.exe_path))
        subprocess.Popen([self.exe_path], cwd=self.game_dir)

    def apply_config(self, config_name):
        self.resolve()
        cfg = self.load_config_file(config_name)
        target = cfg.pop("target", None) or os.path.join(
            self.game_dir, "config.yaml")
        self.replace_yaml_fields(target, cfg)
