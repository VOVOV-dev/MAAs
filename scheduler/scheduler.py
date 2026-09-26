"""统一调度器主入口（常驻自主运行）。

用法（用绿色 Python 运行，会自动请求管理员提权）：
  scheduler\\python\\python.exe scheduler.py --list       # 列出调度计划
  scheduler\\python\\python.exe scheduler.py --dry-run    # 预览一轮（不启动）
  scheduler\\python\\python.exe scheduler.py --once       # 只执行一轮
  scheduler\\python\\python.exe scheduler.py              # 常驻：启动即跑一轮，之后每天定时循环
  scheduler\\python\\python.exe scheduler.py --only march7th
"""
import argparse
import ctypes
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta

# 让 embeddable Python 能 import 同目录的 games 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 不生成 __pycache__ 字节码缓存，保持目录干净
sys.dont_write_bytecode = True

from games import create, ADAPTERS
from games.base import ROOT


def is_admin():
    """是否以管理员权限运行。"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate():
    """以管理员权限重新启动本脚本（弹一次 UAC）。"""
    script = os.path.abspath(__file__)
    params = '"{}" {}'.format(script, " ".join(sys.argv[1:]))
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", os.path.abspath(sys.executable), params,
        os.path.dirname(script), 1)


def load_plan():
    plan_path = os.path.join(ROOT, "plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _in_window(s, now=None):
    """判断当前时间是否在该游戏的可运行窗口内。

    plan.json 的 schedule 项可选 "window": ["HH:MM", "HH:MM"]；
    未配置 window 视为全天可跑。支持跨天窗口（如 ["18:00", "04:00"]）。
    """
    window = s.get("window")
    if not window:
        return True
    start, end = window[0], window[1]
    now = now or datetime.now().strftime("%H:%M")
    if start <= end:
        return start <= now < end
    # 跨天窗口：如 18:00-04:00
    return now >= start or now < end


def run_once(only=None, dry_run=False):
    """执行一轮：每个游戏 随机决策→写配置→启动→检测→关闭。"""
    plan = load_plan()
    only = set(x.strip() for x in only.split(",")) if only else None

    for s in plan.get("schedule", []):
        if only and s.get("name") not in only and s.get("adapter") not in only:
            continue
        # 时间窗口过滤：--only 显式指定时强制运行，忽略窗口
        if not only and not _in_window(s):
            print("  [跳过] {} 不在运行窗口（window={}，当前 {}）".format(
                s.get("name"), s.get("window"),
                datetime.now().strftime("%H:%M")))
            continue
        try:
            adapter = create(s["adapter"])
        except ValueError as e:
            print("跳过: {}".format(e))
            continue

        print("\n========== {} ==========".format(adapter.display_name))

        config_name = None
        if s.get("random_config"):
            pool = adapter.list_configs()
            if pool:
                config_name = random.choice(pool)
                print("  [随机决策] 今日配置单: {}".format(config_name))
            else:
                print("  [警告] random_config=true 但 configs/{}/ 无可用配置单".format(
                    adapter.name))

        if dry_run:
            print("  [dry-run] 将套用配置单: {}".format(config_name))
            continue

        ok = adapter.run(
            config_name=config_name,
            timeout_min=s.get("timeout_min", 60),
            poll_sec=s.get("poll_sec", 10),
            cooldown_sec=plan.get("cooldown_sec", 15),
        )
        print("  结果: {}".format("正常完成" if ok else "失败/超时"))
        if not ok and s.get("stop_on_fail"):
            print("  配置了 stop_on_fail，停止后续任务")
            break

    print("\n本轮调度结束。")


def sleep_until(hour, minute):
    """sleep 到下一个 hour:minute（每日执行时间）。"""
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    seconds = (target - now).total_seconds()
    print("\n[调度器] 下次执行: {}（{} 秒后），持续运行中...".format(
        target.strftime("%Y-%m-%d %H:%M:%S"), int(seconds)))
    time.sleep(seconds)


def daemon():
    """常驻：立即执行一轮，之后每天定时循环。"""
    plan = load_plan()
    run_hour = plan.get("run_hour", 4)
    run_minute = plan.get("run_minute", 0)
    print("[调度器] 常驻运行，每日 {}:{:02d} 自动执行一轮".format(run_hour, run_minute))
    while True:
        run_once()
        sleep_until(run_hour, run_minute)


def main():
    parser = argparse.ArgumentParser(description="统一游戏调度器")
    parser.add_argument("--list", action="store_true", help="列出调度计划")
    parser.add_argument("--discover", action="store_true", help="扫描磁盘发现各游戏路径并缓存")
    parser.add_argument("--once", action="store_true", help="只执行一轮（不常驻）")
    parser.add_argument("--dry-run", action="store_true", help="只预览一轮，不实际启动")
    parser.add_argument("--only", help="只运行指定游戏（逗号分隔，可用 name 或 adapter）")
    args = parser.parse_args()

    # 只有真正执行游戏（--once 或常驻）才需要管理员；list/discover/dry-run 无需提权
    need_admin = not (args.list or args.discover or args.dry_run)
    if need_admin and not is_admin():
        print("需要管理员权限，正在请求提权（请在弹出的 UAC 点“是”）...")
        elevate()
        return

    plan = load_plan()
    steps = plan.get("schedule", [])

    if args.discover:
        print("扫描磁盘，发现游戏路径...")
        for adapter_name in ADAPTERS:
            adapter = create(adapter_name)
            if adapter.resolve():
                print("  [{}] {} -> {}".format(
                    adapter.name, adapter.display_name, adapter.exe_path))
            else:
                print("  [{}] {} -> 未找到".format(adapter.name, adapter.display_name))
        return

    if args.list:
        print("调度计划（每天 {}:{:02d} 执行）：".format(
            plan.get("run_hour", 4), plan.get("run_minute", 0)))
        for i, s in enumerate(steps, 1):
            win = "window={}".format("~".join(s["window"])) if s.get("window") else "window=全天"
            print("  [{0}] {1}  (adapter={2}, random_config={3}, timeout={4}min, {5})".format(
                i, s.get("name"), s.get("adapter"),
                s.get("random_config", False), s.get("timeout_min", 60), win))
        return

    if args.once or args.dry_run:
        run_once(only=args.only, dry_run=args.dry_run)
    else:
        # 默认常驻：立即跑一轮，之后每天定时循环
        daemon()


if __name__ == "__main__":
    main()
