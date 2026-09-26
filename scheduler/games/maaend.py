"""终末地 MaaEnd 适配器。"""
import ctypes
import os
import subprocess
import time
from ctypes import wintypes

from .base import GameAdapter, GAME_DIRS

_WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32 = ctypes.windll.user32
_user32.EnumWindows.argtypes = [_WNDENUMPROC, wintypes.LPARAM]
_user32.EnumWindows.restype = wintypes.BOOL
_user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetClassNameW.restype = ctypes.c_int
_user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_user32.GetWindowTextLengthW.restype = ctypes.c_int
_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetWindowTextW.restype = ctypes.c_int


def _find_endfield_window():
    """查找类名 UnityWndClass 且标题含 Endfield 的窗口，返回句柄（找不到返回 0）。"""
    found = []

    @_WNDENUMPROC
    def _cb(hwnd, _lparam):
        cls = ctypes.create_unicode_buffer(256)
        _user32.GetClassNameW(hwnd, cls, 256)
        if cls.value == "UnityWndClass":
            length = _user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                _user32.GetWindowTextW(hwnd, buf, length + 1)
                if "Endfield" in buf.value:
                    found.append(int(hwnd))
        return True

    _user32.EnumWindows(_cb, 0)
    return found[0] if found else 0


def _wait_game_window(timeout=300, interval=2, stable=30):
    """等待终末地游戏窗口出现并稳定（同一句柄连续存在 stable 秒）。

    游戏加载过程中窗口会经历“出现→消失→重建”，MaaEnd 只搜索一次，
    搜不到就判定任务启动失败，因此必须等窗口稳定后再启动 MaaEnd。
    """
    deadline = time.time() + timeout
    hwnd = 0
    stable_since = 0.0
    while time.time() < deadline:
        cur = _find_endfield_window()
        now = time.time()
        if cur:
            if cur == hwnd:
                if now - stable_since >= stable:
                    return True
            else:
                # 窗口首次出现或句柄变化（重建），重新计时
                hwnd = cur
                stable_since = now
        else:
            hwnd = 0
            stable_since = 0.0
        time.sleep(interval)
    return False


class MaaEndAdapter(GameAdapter):
    name = "maaend"
    display_name = "终末地 MaaEnd"
    process_names = ["MaaEnd", "MaaPiCli"]
    game_dir = GAME_DIRS["maaend"]
    folder_patterns = [r"Endfield", r"MaaEnd"]
    exe_names = ["MaaEnd.exe"]
    # 游戏本体（MaaEnd 的快速日常没有"打开游戏"任务，需先启动游戏）
    game_folder_patterns = [r"Arknights Endfield", r"Endfield"]
    game_exe_names = ["Endfield.exe"]
    game_client = ""  # 留空，由 resolve_game_client 自动发现

    def start(self):
        if not self.resolve():
            return False
        game_client = self.resolve_game_client()
        # 先启动游戏客户端
        if game_client:
            subprocess.Popen(
                [game_client], cwd=os.path.dirname(game_client))
            self.log("已启动游戏客户端 {}".format(game_client))
        else:
            self.log("警告：未找到游戏客户端，仅启动 MaaEnd")
        # 等待游戏窗口出现（MaaEnd 必须搜索到游戏窗口才能启动任务）
        self.log("等待游戏窗口出现...")
        if _wait_game_window():
            self.log("游戏窗口已就绪")
        else:
            self.log("警告：等待游戏窗口超时，仍尝试启动 MaaEnd")
        # 命令行参数：自动执行"快速日常"实例，完成后自动退出
        subprocess.Popen(
            [self.exe_path, "--autostart", "-i", "快速日常", "--quit-after-run"],
            cwd=self.game_dir)
        self.log("启动 MaaEnd（自动执行快速日常，完成后退出）")

    def apply_config(self, config_name):
        self.resolve()
        cfg = self.load_config_file(config_name)
        target = cfg.pop("target", None) or os.path.join(
            self.game_dir, "config", "config.json")
        self.merge_json_file(target, cfg)
