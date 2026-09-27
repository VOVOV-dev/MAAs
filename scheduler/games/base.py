"""统一调度器 - 游戏适配器基类。

每个游戏实现一个 GameAdapter 子类，统一暴露三个能力：
  1. start()            —— 启动游戏（各自接管方式）
  2. is_running()       —— 检测运行状况
  3. apply_config()     —— 把配置单替换进游戏配置

调度器只依赖这套统一接口，不关心具体游戏细节。
"""
import json
import os
import re
import shutil
import subprocess
import time
from abc import ABC, abstractmethod

from .paths import discover, find_exe, PathStore

# 调度器根目录（d:\MAAs\scheduler）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(ROOT, "logs")
STATE_DIR = os.path.join(ROOT, "state")
CONFIGS_DIR = os.path.join(ROOT, "configs")

# 各游戏安装目录（绿色便携，全部集中在 d:\MAAs）
GAME_DIRS = {
    "maa": r"d:\MAAs\MAA-v6.18.0-win-x64",
    "maaend": r"d:\MAAs\Endfield",
    "bettergi": r"d:\MAAs\Genshin",
    "march7th": r"d:\MAAs\StarRail",
    "zzz": r"d:\MAAs\ZZZ",
}


def process_exists(proc_name):
    """检测进程名是否存活（Windows，无第三方依赖）。

    使用 tasklist /FO CSV 输出，避免默认表格格式把长进程名
    （如 OneDragon-RuntimeLauncher.exe 28 字符）截断导致误判。
    """
    if not proc_name.lower().endswith(".exe"):
        proc_name += ".exe"
    try:
        r = subprocess.run(
            ["tasklist", "/FO", "CSV",
             "/FI", "IMAGENAME eq {}".format(proc_name), "/NH"],
            capture_output=True, text=True, timeout=10,
        )
        return proc_name.lower() in r.stdout.lower()
    except Exception:
        return False


def kill_process(pname):
    """结束指定进程名的进程（含子进程树）。"""
    exe = pname if pname.lower().endswith(".exe") else pname + ".exe"
    try:
        subprocess.run(["taskkill", "/IM", exe, "/F", "/T"],
                       capture_output=True, timeout=15)
    except Exception:
        pass


def deep_merge(base, override):
    """递归合并 dict。override 覆盖 base，嵌套 dict 逐层合并。"""
    if isinstance(base, dict) and isinstance(override, dict):
        result = dict(base)
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = deep_merge(result[k], v)
            else:
                result[k] = v
        return result
    return override


class GameAdapter(ABC):
    """游戏适配器基类。"""

    name = ""              # 适配器名（与目录/配置单目录对应）
    display_name = ""      # 显示名
    process_names = []     # 用于进程检测的进程名列表
    game_dir = ""          # 游戏安装目录（默认值，作为扫描失败时的兜底）
    folder_patterns = []   # 文件夹名正则特征（用于磁盘扫描）
    exe_names = []         # 可执行文件名特征（用于磁盘扫描识别程序）
    game_folder_patterns = []  # 游戏本体文件夹名特征（用于磁盘扫描）
    game_exe_names = []        # 游戏本体可执行文件名（用于磁盘扫描）
    game_client = ""           # 游戏本体路径（可留空，由 resolve_game_client 自动发现）

    def __init__(self):
        self.log_path = os.path.join(LOGS_DIR, "{}.log".format(self.name))
        self._backup_dir = os.path.join(STATE_DIR, "backup", self.name)
        self.exe_path = None   # 解析后的程序路径（resolve() 填充）
        os.makedirs(self._backup_dir, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)

    # ---------- 路径发现 ----------
    def resolve(self):
        """解析游戏路径：缓存 → 全盘扫描 → 默认路径。返回是否找到。"""
        store = PathStore()
        cached = store.get_valid(self.name)
        if cached:
            self.game_dir, self.exe_path = cached
            return True
        found = discover(self.folder_patterns, self.exe_names)
        if found[0]:
            self.game_dir, self.exe_path = found
            store.set(self.name, self.game_dir, self.exe_path)
            self.log("已发现游戏目录 -> {}".format(self.game_dir))
            return True
        if self.game_dir and os.path.isdir(self.game_dir):
            exe = find_exe(self.game_dir, self.exe_names)
            if exe:
                self.exe_path = exe
                store.set(self.name, self.game_dir, exe)
                self.log("使用默认目录 -> {}".format(self.game_dir))
                return True
        self.log("未找到游戏目录（特征目录 {} / 程序 {}）".format(
            self.folder_patterns, self.exe_names))
        return False

    def resolve_game_client(self):
        """自动发现游戏本体路径：已有路径 → 缓存 → 全盘扫描 → 兜底。

        返回游戏本体可执行文件路径，找不到返回 None。
        """
        # 已配置且存在的路径直接使用
        if self.game_client and os.path.exists(self.game_client):
            return self.game_client
        if not self.game_exe_names:
            return self.game_client or None
        store = PathStore()
        cache_key = "game_client_" + self.name
        cached = store.get_valid(cache_key)
        if cached:
            _cached_dir, cached_exe = cached
            self.game_client = cached_exe
            self.log("游戏本体路径（缓存）-> {}".format(cached_exe))
            return cached_exe
        found = discover(self.game_folder_patterns, self.game_exe_names)
        if found[0]:
            game_dir, exe = found
            store.set(cache_key, game_dir, exe)
            self.game_client = exe
            self.log("已发现游戏本体 -> {}".format(exe))
            return exe
        if self.game_client:
            self.log("未找到游戏本体，沿用配置路径 {}".format(self.game_client))
            return self.game_client
        self.log("未找到游戏本体（特征目录 {} / 程序 {}）".format(
            self.game_folder_patterns, self.game_exe_names))
        return None

    # ---------- 日志 ----------
    def log(self, msg):
        line = "[{}] [{}] {}".format(
            time.strftime("%Y-%m-%d %H:%M:%S"), self.display_name, msg)
        print(line)
        try:
            if not os.path.exists(self.log_path):
                # 首次创建写 UTF-8 BOM，Windows 记事本/PowerShell 可正常显示中文
                with open(self.log_path, "w", encoding="utf-8-sig") as f:
                    f.write(line + "\n")
                return
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    # ---------- 统一入口（调度器调用） ----------
    def run(self, config_name=None, timeout_min=60, poll_sec=10, cooldown_sec=15):
        """启动（可选套用配置单）→ 检测 → 超时兜底 → 确保清理干净 → 冷却。

        返回是否正常完成。无论正常结束、超时还是启动失败，
        都会强制清理进程并等待确认退出，避免影响下一个游戏。
        执行详情记录在 self.last_result（status / detail / elapsed 秒）。
        """
        t0 = time.time()
        self.last_result = {"status": "success", "detail": "", "elapsed": 0}
        if config_name:
            try:
                self.apply_config(config_name)
            except Exception as e:
                self.log("应用配置失败: {}".format(e))
                self.last_result.update({
                    "status": "failed", "detail": "应用配置失败",
                    "elapsed": time.time() - t0})
                return False
        try:
            self.start()
        except Exception as e:
            self.log("启动失败: {}".format(e))
            self._cleanup()
            self.last_result.update({
                "status": "failed", "detail": "启动失败",
                "elapsed": time.time() - t0})
            return False
        self.log("已启动")
        ok = self.wait_finish(timeout_min, poll_sec)
        elapsed = time.time() - t0
        if ok:
            self.log("运行结束")
            self.last_result.update(
                {"status": "success", "detail": "", "elapsed": elapsed})
        else:
            self.log("超时未完成（{} 分钟），强制关闭".format(timeout_min))
            self.last_result.update({
                "status": "timeout",
                "detail": "超时（{} 分钟）".format(timeout_min),
                "elapsed": elapsed})
        self._cleanup()
        time.sleep(cooldown_sec)
        return ok

    def _cleanup(self):
        """强制清理进程并等待确认退出（工具进程 + 游戏本体）。"""
        self.stop()
        if not self.wait_stopped(30):
            self.log("警告：进程清理不彻底，二次强制关闭")
            self.stop()
            self.wait_stopped(15)

    @abstractmethod
    def start(self):
        """启动游戏。"""

    @abstractmethod
    def apply_config(self, config_name):
        """把配置单应用到游戏配置文件。"""

    # ---------- 检测 ----------
    def is_running(self):
        """默认按进程名检测。子类可覆盖（如 HTTP 健康检查）。"""
        return any(process_exists(p) for p in self.process_names)

    def wait_finish(self, timeout_min=60, poll_sec=10):
        """轮询等待进程退出 / 完成。"""
        deadline = time.time() + timeout_min * 60
        while time.time() < deadline:
            if not self.is_running():
                return True
            time.sleep(poll_sec)
        return False

    def _client_exe_name(self):
        """返回游戏本体可执行文件名（无则返回 None）。"""
        client = self.game_client
        if not client and self.game_exe_names:
            try:
                client = self.resolve_game_client()
            except Exception:
                client = None
        return os.path.basename(client) if client else None

    def stop(self):
        """主动关闭游戏进程（超时/需要强制结束时的兜底）。"""
        for pname in self.process_names:
            kill_process(pname)
        # 兜底：也关闭游戏本体（避免超时强杀工具后游戏进程残留）
        client = self._client_exe_name()
        if client:
            kill_process(client)

    def wait_stopped(self, timeout_sec=30):
        """停止后等待进程真正退出（工具进程 + 游戏本体），返回是否已全部退出。"""
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            running = any(process_exists(p) for p in self.process_names)
            client = self._client_exe_name()
            if client and process_exists(client):
                running = True
            if not running:
                return True
            time.sleep(1)
        return False

    # ---------- 配置单 ----------
    def list_configs(self):
        """列出该游戏所有可用配置单名（不含 .json 后缀，排除 _ 开头）。"""
        d = os.path.join(CONFIGS_DIR, self.name)
        if not os.path.isdir(d):
            return []
        return sorted(
            f[:-5] for f in os.listdir(d)
            if f.endswith(".json") and not f.startswith("_")
        )

    # ---------- 配置单工具 ----------
    def config_path(self, config_name):
        return os.path.join(CONFIGS_DIR, self.name, config_name + ".json")

    def load_config_file(self, config_name):
        with open(self.config_path(config_name), "r", encoding="utf-8") as f:
            return json.load(f)

    def backup_file(self, target):
        """备份目标文件到 state/backup/<name>/，返回备份路径。"""
        if os.path.exists(target):
            ts = time.strftime("%Y%m%d_%H%M%S")
            dst = os.path.join(self._backup_dir, "{}_{}".format(ts, os.path.basename(target)))
            shutil.copy2(target, dst)
            self.log("已备份原配置 -> {}".format(dst))
            return dst
        return None

    # ---------- JSON 配置文件字段合并 ----------
    def merge_json_file(self, target, overrides):
        """把 overrides 合并进 JSON 配置文件（先备份）。"""
        self.backup_file(target)
        data = {}
        if os.path.exists(target):
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
        merged = deep_merge(data, overrides)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        self.log("已合并配置 -> {}".format(target))

    # ---------- YAML 顶层字段替换（用于 March7th 的 config.yaml） ----------
    def replace_yaml_fields(self, target, fields):
        """替换 YAML 文件顶层字段（key: value 形式）。

        fields: {key: value}，value 用 JSON 序列化（JSON 是合法 YAML）。
        逐行定位顶格 key 行，替换为单行值，并删除后续多行旧值
        （包括 block 列表项），避免 March7th 保存的多行格式残留导致损坏。
        """
        self.backup_file(target)
        with open(target, "r", encoding="utf-8") as f:
            lines = f.read().splitlines(keepends=True)
        for key, value in fields.items():
            yaml_val = json.dumps(value, ensure_ascii=False)
            # 只匹配顶格 key，[ \t]* 不跨行（避免吞掉换行）
            key_re = re.compile(r"^({}[ \t]*:[ \t]*)".format(re.escape(key)))
            replaced = False
            for i, line in enumerate(lines):
                m = key_re.match(line)
                if not m:
                    continue
                lines[i] = "{}: {}\n".format(key, yaml_val)
                # 删除后续多行旧值：缩进行 + 顶格 block 列表项
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    stripped = nxt.strip()
                    if stripped == "" or stripped.startswith("#"):
                        break  # 空行/注释，停止
                    if not (nxt.startswith(" ") or nxt.startswith("\t") or nxt.startswith("-")):
                        break  # 顶格非列表项 = 下一个键，停止
                    j += 1
                del lines[i + 1:j]
                replaced = True
                break
            if not replaced:
                lines.append("{}: {}\n".format(key, yaml_val))
        with open(target, "w", encoding="utf-8") as f:
            f.writelines(lines)
        self.log("已替换字段 {} -> {}".format(list(fields.keys()), target))
