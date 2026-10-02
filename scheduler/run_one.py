"""补跑脚本：单独运行某个游戏的助手（查漏补缺用）。

某天调度器跑完发现某个游戏没做完，用它单独补跑，不影响其他游戏。

用法（用绿色 Python 运行，需要管理员时自动请求提权）：
  scheduler\\python\\python.exe run_one.py                  # 交互式：列出计划让你选
  scheduler\\python\\python.exe run_one.py --list           # 只看列表
  scheduler\\python\\python.exe run_one.py 终末地            # 按游戏名补跑
  scheduler\\python\\python.exe run_one.py maaend           # 按适配器名补跑
  scheduler\\python\\python.exe run_one.py 2                # 按序号补跑
  scheduler\\python\\python.exe run_one.py 1,3              # 多个（逗号分隔）
  scheduler\\python\\python.exe run_one.py all              # 全部
  scheduler\\python\\python.exe run_one.py maaend --config 快速日常   # 指定配置单
  scheduler\\python\\python.exe run_one.py maaend --kill    # 先清理残留进程再跑
  scheduler\\python\\python.exe run_one.py maaend --timeout 60  # 覆盖超时（分钟）
"""
import argparse
import ctypes
import json
import os
import random
import re
import sys
import time

# 让 embeddable Python 能 import 同目录的 games 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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


def print_plan(steps):
    """打印编号的调度计划。"""
    print("可补跑的游戏：")
    for i, s in enumerate(steps, 1):
        print("  [{0}] {1}  (adapter={2}, timeout={3}min)".format(
            i, s.get("name"), s.get("adapter"), s.get("timeout_min", 60)))
    print("  输入 all 补跑全部，q 退出")


def parse_selection(steps, text):
    """把用户输入解析成 step 下标列表。

    支持：数字序号、逗号/空格/中文逗号分隔、游戏名（包含匹配）、适配器名（精确匹配）、all。
    """
    selected = []
    for tok in re.split(r"[,，\s]+", text.strip()):
        if not tok:
            continue
        if tok.lower() == "all":
            for i in range(len(steps)):
                if i not in selected:
                    selected.append(i)
            continue
        if tok.isdigit():
            i = int(tok) - 1
            if 0 <= i < len(steps):
                if i not in selected:
                    selected.append(i)
            else:
                print("  [无效] 序号 {} 超出范围（1-{}）".format(tok, len(steps)))
            continue
        hits = [i for i, s in enumerate(steps)
                if tok in s.get("name", "") or tok == s.get("adapter", "")]
        if len(hits) == 1:
            i = hits[0]
            if i not in selected:
                selected.append(i)
        elif len(hits) > 1:
            print("  [歧义] \"{}\" 匹配到多项：{}，请用更完整的名字或序号".format(
                tok, "、".join(steps[i].get("name") for i in hits)))
        else:
            print("  [无效] 找不到 \"{}\"（可用名称或适配器：{}）".format(
                tok, "、".join(s.get("name") for s in steps)))
    return sorted(selected)


def interactive_select(steps):
    """交互式选择要补跑的游戏。"""
    while True:
        print_plan(steps)
        text = input("请选择要补跑的游戏（如 1、1,3、终末地、all，q 退出）: ").strip()
        if not text:
            continue
        if text.lower() in ("q", "quit", "exit", "0"):
            return []
        selected = parse_selection(steps, text)
        if selected:
            return selected
        print()


def resolve_config(adapter, step, config_arg, interactive):
    """决定本次使用的配置单。

    优先级：--config 参数 > 计划里的 random_config 随机 > 无（默认配置）。
    """
    pool = adapter.list_configs()
    if config_arg:
        if config_arg not in pool:
            print("  [错误] 配置单 \"{}\" 不存在，可选：{}".format(
                config_arg, "、".join(pool) if pool else "（无配置单）"))
            return None
        print("  [配置] 使用指定配置单: {}".format(config_arg))
        return config_arg
    if step.get("random_config"):
        if pool:
            pick = random.choice(pool)
            print("  [配置] 随机选择配置单: {}".format(pick))
            return pick
        print("  [警告] random_config=true 但 configs/{}/ 无可用配置单".format(
            adapter.name))
    return None


def run_one(steps, selected, args):
    """依次补跑选中的游戏。"""
    if len(selected) > 1 and args.config:
        print("[错误] --config 只能用于单个游戏（当前选了 {} 个）".format(len(selected)))
        return 1
    results = []
    for idx in selected:
        step = steps[idx]
        name = step.get("name")
        ad_name = step.get("adapter")
        try:
            adapter = create(ad_name)
        except ValueError as e:
            print("跳过: {}".format(e))
            results.append({"name": name, "status": "跳过", "elapsed": None,
                            "detail": str(e)})
            continue

        print("\n========== {} ==========".format(adapter.display_name))

        # 残留进程检查：先关闭再补跑，避免工具已在运行导致启动失败
        if adapter.is_running():
            kill = args.kill
            if not args.kill and args.interactive:
                ans = input(
                    "  检测到 {} 进程仍在运行（可能是上午没跑完的残留）。\n"
                    "  是否先强制清理再重新补跑？[y/N] ".format(adapter.display_name)
                ).strip().lower()
                kill = ans in ("y", "yes")
            if not kill:
                print("  [跳过] 工具进程仍在运行，请手动关闭后重试，"
                      "或加 --kill 参数强制清理")
                results.append({"name": name, "status": "跳过",
                                "elapsed": None, "detail": "进程残留未清理"})
                continue
            print("  [清理] 强制关闭残留进程...")
            adapter.stop()
            adapter.wait_stopped(30)

        cfg = resolve_config(adapter, step, args.config, args.interactive)
        if cfg is None and args.config:
            # resolve_config 已打印错误
            results.append({"name": name, "status": "跳过", "elapsed": None,
                            "detail": "配置单不存在"})
            continue

        if args.dry_run:
            print("  [dry-run] 将补跑 {}（配置单: {}，超时 {} 分钟）".format(
                name, cfg or "默认", args.timeout or step.get("timeout_min", 60)))
            results.append({"name": name, "status": "预览", "elapsed": None,
                            "detail": "未实际执行"})
            continue

        ok = adapter.run(
            config_name=cfg,
            timeout_min=args.timeout or step.get("timeout_min", 60),
            poll_sec=step.get("poll_sec", 10),
            cooldown_sec=plan_cooldown(),
        )
        res = getattr(adapter, "last_result", None) or {}
        elapsed = res.get("elapsed")
        detail = res.get("detail", "")
        if ok:
            status = "成功"
        elif res.get("status") == "timeout":
            status = "超时"
        else:
            status = "失败"
        time_str = "{:.1f} 分钟".format(elapsed / 60.0) if elapsed is not None else "-"
        print("  结果: {}（耗时 {}）{}".format(
            status, time_str, "（{}）".format(detail) if detail else ""))
        results.append({"name": name, "status": status, "elapsed": elapsed,
                        "detail": detail})

    print_summary(results)
    return 0 if all(r["status"] in ("成功", "预览", "跳过") for r in results) else 1


def plan_cooldown():
    """冷却秒数（沿用 plan.json 配置）。"""
    try:
        return load_plan().get("cooldown_sec", 15)
    except Exception:
        return 15


def print_summary(results):
    """补跑结果汇总。"""
    if not results:
        return
    print("\n" + "=" * 62)
    print("  补跑结果汇总")
    print("=" * 62)
    success = failed = skipped = 0
    for i, r in enumerate(results, 1):
        elapsed = r.get("elapsed")
        time_str = "{:.1f} 分钟".format(elapsed / 60.0) if elapsed is not None else "-"
        line = "  [{0}] {1} | {2} | 耗时 {3}".format(i, r["name"], r["status"], time_str)
        if r.get("detail"):
            line += " | {}".format(r["detail"])
        print(line)
        if r["status"] == "成功":
            success += 1
        elif r["status"] in ("失败", "超时"):
            failed += 1
        else:
            skipped += 1
    print("-" * 62)
    print("  合计 {} 项：成功 {}，失败/超时 {}，跳过 {}".format(
        len(results), success, failed, skipped))
    print("=" * 62)


def main():
    parser = argparse.ArgumentParser(description="补跑单个游戏助手（查漏补缺）")
    parser.add_argument("selection", nargs="*",
                        help="游戏（序号 / 名称 / 适配器名，可多个逗号分隔；all=全部）")
    parser.add_argument("--list", action="store_true", help="列出可补跑的游戏")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不实际启动")
    parser.add_argument("--kill", action="store_true",
                        help="补跑前强制清理残留进程（无需确认）")
    parser.add_argument("--config", help="指定配置单名（仅单个游戏时可用）")
    parser.add_argument("--timeout", type=int, help="覆盖超时时间（分钟）")
    args = parser.parse_args()

    # 只有真正执行才需要管理员；list/dry-run 无需提权
    need_admin = not (args.list or args.dry_run)
    if need_admin and not is_admin():
        print("需要管理员权限，正在请求提权（请在弹出的 UAC 点“是”）...")
        elevate()
        return

    plan = load_plan()
    steps = plan.get("schedule", [])

    if args.list:
        print_plan(steps)
        return

    # 决定选中哪些游戏
    if args.selection:
        text = " ".join(args.selection)
        selected = parse_selection(steps, text)
        args.interactive = False
    else:
        args.interactive = True
        selected = interactive_select(steps)
    if not selected:
        print("未选择任何游戏，退出。")
        return

    sys.exit(run_one(steps, selected, args))


if __name__ == "__main__":
    main()
