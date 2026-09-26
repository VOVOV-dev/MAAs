"""原神 BetterGI 适配器。"""
import os
import subprocess

from .base import GameAdapter, GAME_DIRS


class BetterGiAdapter(GameAdapter):
    name = "bettergi"
    display_name = "原神 BetterGI"
    process_names = ["BetterGI"]
    game_dir = GAME_DIRS["bettergi"]
    folder_patterns = [r"BetterGI", r"Genshin"]
    exe_names = ["BetterGI.exe"]
    # 游戏本体（原神）
    game_folder_patterns = [r"Genshin Impact", r"Genshin"]
    game_exe_names = ["YuanShen.exe", "GenshinImpact.exe"]
    game_client = ""  # 留空，由 resolve_game_client 自动发现

    def start(self):
        if not self.resolve():
            return False
        # 命令行启动一条龙：startOneDragon <配置名>，跑完按 CompletionAction 关闭游戏和软件
        self.log("启动 {}（一条龙：默认配置）".format(self.exe_path))
        subprocess.Popen(
            [self.exe_path, "startOneDragon", "默认配置"], cwd=self.game_dir)

    def apply_config(self, config_name):
        self.resolve()
        cfg = self.load_config_file(config_name)
        # 默认写入一条龙配置单（User/OneDragon/默认配置.json）
        target = cfg.pop("target", None) or os.path.join(
            self.game_dir, "User", "OneDragon", "默认配置.json")
        self.merge_json_file(target, cfg)
