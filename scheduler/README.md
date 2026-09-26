# 统一游戏调度器

自包含的绿色调度器，集中编排 5 款游戏的日常自动化。**不装系统、不写注册表、删目录即卸载。**

## 目录结构

```
scheduler/
├─ python/           绿色便携 Python（仅调度器用，已内嵌）
├─ scheduler.py      主调度器
├─ plan.json         调度计划（编排启动顺序）
├─ games/            5 个游戏适配器
│  ├─ base.py        适配器基类（启动/检测/换配置的统一接口）
│  ├─ maa.py         明日方舟
│  ├─ maaend.py      终末地
│  ├─ bettergi.py    原神
│  ├─ march7th.py    星铁
│  └─ zzz.py         绝区零
├─ configs/          配置单仓库（预写的日常计划）
├─ logs/             运行日志（可删）
└─ state/            状态 + 配置备份（可删）
```

## 使用

```bat
:: 查看调度计划
scheduler\python\python.exe scheduler\scheduler.py --list

:: 预览（不实际启动）
scheduler\python\python.exe scheduler\scheduler.py --dry-run

:: 完整执行
scheduler\python\python.exe scheduler\scheduler.py

:: 只跑某个游戏（按 name 或 adapter）
scheduler\python\python.exe scheduler\scheduler.py --only march7th
```

## 调度计划 plan.json

按数组顺序依次执行，`random_config` 为 true 时从 `configs/<adapter>/` 随机抽配置单：

```json
{
  "schedule": [
    { "name": "星穹铁道", "adapter": "march7th", "random_config": true, "timeout_min": 90 },
    { "name": "原神", "adapter": "bettergi", "random_config": false, "timeout_min": 60 }
  ]
}
```

字段说明：
- `name` / `adapter`：游戏名与适配器名（adapter 对应 games/ 下的 py 文件名）
- `random_config`：为 true 时随机套用 `configs/<adapter>/` 下某个配置单；false 则不改配置
- `timeout_min`：最长等待分钟数，超时强制关闭并继续下一个
- `stop_on_fail`（可选）：为 true 时，该步失败则停止后续任务

## 配置单机制（核心）

1. 在 `configs/<adapter>/` 下预写配置单（JSON）。
2. 调度器执行到该游戏时，先把配置单**合并/替换进游戏的真实配置文件**（改前自动备份到 `state/backup/`）。
3. 然后启动游戏，游戏按新配置执行。

### 示例：星铁每日清体力计划

预写 `configs/march7th/power_plan_sunday.json`：

```json
{
  "power_enable": true,
  "power_plan": [["历战余响", "毁灭的开端", 3], ["侵蚀隧洞", "睿治之径", 6]],
  "instance_type": "侵蚀隧洞"
}
```

把 `plan.json` 里星铁那步设为 `"random_config": true`，调度器每次会从 `configs/march7th/` 下随机抽一个配置单（如 `power_plan_sunday`），然后：
备份 `config.yaml` → 替换其中 `power_plan`/`power_enable`/`instance_type` 字段 → 启动星铁按新计划清体力。

> 其他游戏配置单同理：JSON 配置文件的游戏（MAA/BetterGI 等）做字段合并；需要指定目标文件时，配置单里加 `"target": "完整路径"`。
> `random_config` 为 false 时不套用配置单，游戏按自身当前配置运行。

## 环境干净说明

- 调度器所有文件都在本目录内，无系统安装、无注册表、无环境变量改动。
- `logs/`、`state/` 是运行时产物，随时可删。
- 删除整个 `scheduler/` 即完全卸载。
