"""游戏安装路径自动发现与缓存。

策略：缓存优先 → 全盘浅层扫描 → 默认路径兜底。
发现结果缓存到 state/paths.json，之后直接读缓存，不再重复扫描。
"""
import json
import os
import re
import string

# 与 base.py 保持一致的根目录与状态目录
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(ROOT, "state")

# 扫描时跳过的无关目录（加速 + 避免误匹配）
SKIP_DIRS = {
    "windows", "program files", "program files (x86)", "programdata",
    "$recycle.bin", "system volume information", "recovery", "perflogs",
    "node_modules", "appdata", "python", "site-packages", ".git",
    "__pycache__", "winnt", "boot", "users", "documents and settings",
}

# 盘根只往下扫这几层，避免全盘递归过慢
MAX_DEPTH = 3


def list_drives():
    """返回存在的盘符根目录列表（C:\\, D:\\ ...）。"""
    return ["{}:\\".format(c) for c in string.ascii_uppercase
            if os.path.exists("{}:\\".format(c))]


def find_exe(dirpath, exe_names):
    """在目录直接层查找可执行文件（大小写不敏感），返回路径或 None。"""
    targets = {e.lower() for e in exe_names}
    try:
        for entry in os.scandir(dirpath):
            if entry.is_file() and entry.name.lower() in targets:
                return entry.path
    except OSError:
        pass
    return None


def _match_dir(name, patterns):
    return any(re.search(p, name, re.IGNORECASE) for p in patterns)


def _search_dir(dirpath, folder_patterns, exe_names, depth):
    """递归搜索单个目录树。找到返回 (game_dir, exe)，否则 None。"""
    if depth > MAX_DEPTH:
        return None
    base = os.path.basename(dirpath.rstrip(os.sep))

    # 目录名匹配特征 → 优先在该目录里找 exe
    if depth > 0 and _match_dir(base, folder_patterns):
        exe = find_exe(dirpath, exe_names)
        if exe:
            return dirpath, exe
    # 直接在当前目录找 exe
    exe = find_exe(dirpath, exe_names)
    if exe:
        return dirpath, exe
    # 递归子目录
    try:
        subdirs = [e.path for e in os.scandir(dirpath) if e.is_dir()]
    except OSError:
        subdirs = []
    for sd in subdirs:
        if os.path.basename(sd).lower() in SKIP_DIRS:
            continue
        found = _search_dir(sd, folder_patterns, exe_names, depth + 1)
        if found:
            return found
    return None


def discover(folder_patterns, exe_names):
    """从所有磁盘根目录搜索游戏，返回 (game_dir, exe) 或 (None, None)。"""
    for drive in list_drives():
        found = _search_dir(drive, folder_patterns, exe_names, depth=0)
        if found:
            return found
    return None, None


class PathStore:
    """已发现路径的持久化缓存。"""

    def __init__(self):
        self.path = os.path.join(STATE_DIR, "paths.json")
        self.data = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def get_valid(self, name):
        """返回缓存里仍有效的 (game_dir, exe)，否则 None。"""
        entry = self.data.get(name)
        if entry:
            exe = entry.get("exe")
            if exe and os.path.exists(exe):
                return entry.get("game_dir"), exe
        return None

    def set(self, name, game_dir, exe):
        self.data[name] = {"game_dir": game_dir, "exe": exe}
        self._save()

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
