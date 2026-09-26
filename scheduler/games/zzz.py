"""绝区零 ZZZ 适配器（通过 OneDragon 命令行一条龙模式）。"""
import json
import os
import subprocess
import time
import urllib.request

from .base import GameAdapter, GAME_DIRS, process_exists


class ZzzAdapter(GameAdapter):
    name = "zzz"
    display_name = "绝区零 ZZZ"
    process_names = ["OneDragon-RuntimeLauncher"]
    game_dir = GAME_DIRS["zzz"]
    folder_patterns = [r"ZenlessZoneZero", r"ZZZ", r"OneDragon"]
    exe_names = ["OneDragon-RuntimeLauncher.exe"]
    # 游戏本体（绝区零）
    game_folder_patterns = [r"ZenlessZoneZero", r"Zenless"]
    game_exe_names = ["ZenlessZoneZero.exe"]
    game_client = ""  # 留空，由 resolve_game_client 自动发现
    BACKEND = "http://127.0.0.1:23001"

    def _http(self, method, path, timeout=15):
        try:
            req = urllib.request.Request(self.BACKEND + path, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _status(self):
        st = self._http("GET", "/game/status")
        return st if st else {}

    def start(self):
        if not self.resolve():
            return False
        # -o/--onedragon 参数：直接运行一条龙（不需要 GUI/backend）
        subprocess.Popen([self.exe_path, "-o"], cwd=self.game_dir)
        self.log("已通过 -o 参数启动一条龙")
        # 等待 OneDragon 进程出现
        for _ in range(120):
            if any(process_exists(p) for p in self.process_names):
                break
            time.sleep(1)

    def is_running(self):
        state = self._status().get("state")
        if state == "running":
            return True
        if state in ("success", "failed", "stopped"):
            return False
        # backend 不可用，回退进程检测
        return any(process_exists(p) for p in self.process_names)

    def stop(self):
        self._http("POST", "/game/stop")
        super().stop()

    def apply_config(self, config_name):
        cfg = self.load_config_file(config_name)
        target = cfg.pop("target", None)
        if target:
            self.merge_json_file(target, cfg)
        else:
            self.log("ZZZ 配置单需在 JSON 里指定 target（src/zzz_od/config 下文件）")
