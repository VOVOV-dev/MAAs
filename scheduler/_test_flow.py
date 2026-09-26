# 临时测试：逐个游戏完整流程（决策→写配置→启动→检测→关闭），自动运行
import ctypes
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True

from games import ADAPTERS, create
from games.base import ROOT


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate():
    script = os.path.abspath(__file__)
    params = '"{}" {}'.format(script, " ".join(sys.argv[1:]))
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", os.path.abspath(sys.executable), params,
        os.path.dirname(script), 1)


if not is_admin():
    print("[提权] 需要管理员权限，请在弹出的 UAC 点“是”...")
    elevate()
    sys.exit(0)

with open(os.path.join(ROOT, "plan.json"), encoding="utf-8") as f:
    plan = json.load(f)
random_map = {s["adapter"]: s.get("random_config", False) for s in plan["schedule"]}

results = []
for name in ADAPTERS:
    a = create(name)
    print("\n" + "=" * 60)
    print("测试【{}】{}".format(name, a.display_name))
    try:
        assert a.resolve(), "路径解析失败"
        print("  [1] 程序: {}".format(a.exe_path))

        if random_map.get(name):
            pool = a.list_configs()
            if pool:
                chosen = random.choice(pool)
                print("  [2] 随机决策 -> {}".format(chosen))
                a.apply_config(chosen)
            else:
                print("  [2] random_config=true 但无配置单池")
        else:
            print("  [2] 固定配置")

        a.start()
        print("  [3] 已启动，观察 10 秒...")
        time.sleep(10)

        running = a.is_running()
        print("  [4] 运行中: {}".format(running))

        a.stop()
        time.sleep(3)
        still = a.is_running()
        print("  [5] 关闭后运行中: {}".format(still))

        if running and not still:
            results.append((a.display_name, "通过"))
            print("  => 通过")
        elif not running:
            results.append((a.display_name, "启动后未检测到进程"))
            print("  => 启动检测失败")
        else:
            results.append((a.display_name, "关闭失败"))
            print("  => 关闭失败")
    except Exception as e:
        results.append((a.display_name, "异常: {}".format(e)))
        print("  => 异常: {}".format(e))

    print("  等待 5 秒进入下一个游戏...")
    time.sleep(5)

print("\n" + "=" * 60)
print("汇总：")
for n, s in results:
    print("  {:<16} {}".format(n, s))
