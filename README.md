# 游戏日常调度器（米+舟系）

一键编排 5 款游戏的每日自动化，按顺序跑完全部日常后自动停止（或常驻每日定时）。

| 顺序 | 游戏 | 自动代理工具 |
|---|---|---|
| 1 | 原神 | BetterGI |
| 2 | 星穹铁道 | March7thAssistant |
| 3 | 绝区零 | OneDragon (ZZZ) |
| 4 | 明日方舟 | MAA |
| 5 | 终末地 | MaaEnd |

- **绿色便携**：工具与调度器全部集中在仓库目录内，不装系统服务、不写注册表、删目录即卸载。
- **全自动**：调度器自动发现路径、随机套用配置单、按超时强关兜底、游戏间自动清理进程。
- **兜底机制**：任一款游戏超时/卡死会强制关闭并清理干净，再继续下一款。

---

## 一、仓库内容

```
d:\MAAs\
├─ scheduler/          调度器（自研代码，Git 跟踪）
│  ├─ scheduler.py     主入口
│  ├─ plan.json        调度计划（执行顺序/超时/随机配置）
│  ├─ games/           5 个游戏适配器
│  ├─ configs/         配置单仓库
│  ├─ python/          绿色 Python（setup.ps1 下载，不入库）
│  ├─ logs/            运行日志（不入库）
│  └─ state/           路径缓存与配置备份（不入库）
├─ MAA-v6.18.0-win-x64/   明日方舟 MAA（setup.ps1 下载，不入库）
├─ Endfield/              终末地 MaaEnd（同上）
├─ Genshin/               原神 BetterGI（同上）
├─ StarRail/              星铁 March7th（同上）
├─ ZZZ/                   绝区零 OneDragon（同上）
├─ setup.ps1           一键部署（下载 Python + 5 工具 + 解压）
├─ download.ps1        仅下载压缩包（不含解压，备选）
├─ plan.txt            日常需求说明（备忘）
└─ 一图流-*.json       MAA 作业文件示例
```

---

## 二、部署清单（克隆仓库后要做的事）

### 0. 前置要求

- Windows 10 / 11 64 位
- 管理员权限（调度器启动游戏工具时会请求 UAC 提权）
- 可访问 GitHub 的网络（下载工具，可能需要代理）

### 1. 克隆仓库

```powershell
git clone <你的仓库地址> d:\MAAs
cd d:\MAAs
```

> 建议直接克隆到 `d:\MAAs`（适配器默认扫描 `d:\MAAs` 下的工具目录）。若放别处，运行一次 `--discover` 会自动全盘扫描定位。

### 2. 安装运行时

| 运行时 | 用途 | 下载 |
|---|---|---|
| .NET 8 Desktop Runtime x64 | BetterGI（原神） | https://dotnet.microsoft.com/download/dotnet/8.0 |
| .NET 10 Desktop Runtime x64 | MAA（明日方舟） | https://dotnet.microsoft.com/download/dotnet/10.0 |

下载后双击安装即可（选 x64 桌面运行时）。

### 3. 一键部署工具

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

脚本会自动下载并解压：
1. 绿色 Python 3.12.10 → `scheduler\python\`
2. MAA v6.18.0 → `MAA-v6.18.0-win-x64\`
3. MaaEnd v2.29.0 → `Endfield\`
4. BetterGI v0.65.0 → `Genshin\`
5. March7thAssistant → `StarRail\`
6. OneDragon v2.5.2 → `ZZZ\`

支持断点续传，中断后重跑即可。

### 4. 安装并登录游戏本体

游戏本体装在**任意盘符**均可，调度器会全盘自动发现（特征目录 + 程序名匹配）。

| 游戏 | 游戏本体程序 | 获取方式 |
|---|---|---|
| 原神（国服） | `YuanShen.exe` | 官网 https://ys.mihoyo.com/ 下载启动器安装 |
| 星穹铁道 | `StarRail.exe` | 官网 https://sr.mihoyo.com/ |
| 绝区零 | `ZenlessZoneZero.exe` | 官网 https://zzz.mihoyo.com/ |
| 终末地 | `Endfield.exe` | 官网 https://endfield.hypergryph.com/ |
| 明日方舟 | 模拟器内运行 | 安装 **MuMu 12 模拟器**，在模拟器内装游戏并登录 |

> 每款游戏至少**手动打开并登录一次**（保持登录态），自动工具才能接管。

### 5. 首次初始化各工具（每个只做一次）

| 工具 | 要做的事 |
|---|---|
| **MAA** | 打开 `MAA.exe` → 设置里连接模拟器（MuMu 12 的 adb 地址通常是 `127.0.0.1:16384`，老版为 `127.0.0.1:7555`）→ 设置好剿灭/日常关卡 → 关闭 |
| **MaaEnd** | 打开 → 控制器选 `win32-Front` → 确认存在「快速日常」实例 → 关闭 |
| **BetterGI** | 打开 → 启动一条龙 → 确认能识别原神窗口 → 关闭 |
| **March7th** | 打开 → 确认 `game_path` 指向 `StarRail.exe` → 按需配置体力/模拟宇宙 → 关闭 |
| **OneDragon** | 打开一次初始化 → 确认能识别绝区零窗口 → 关闭 |

> 首次运行可能还需要在游戏内完成新手引导、绑定账号、设置 60 帧等，确保游戏能正常进入主界面。

### 6. 验证与运行

```powershell
# 扫描发现各游戏路径（确认都找得到）
scheduler\python\python.exe scheduler\scheduler.py --discover

# 预览执行顺序（不真正启动）
scheduler\python\python.exe scheduler\scheduler.py --dry-run

# 执行一轮（跑完 5 款即退出）
scheduler\python\python.exe scheduler\scheduler.py --once

# 只跑某一款（按 name 或 adapter）
scheduler\python\python.exe scheduler\scheduler.py --only zzz

# 常驻模式（立即跑一轮，之后每天 4:00 自动跑）
scheduler\python\python.exe scheduler\scheduler.py
```

---

## 三、调度计划 `scheduler/plan.json`

```json
{
  "run_hour": 4,
  "run_minute": 0,
  "cooldown_sec": 15,
  "schedule": [
    { "name": "原神",   "adapter": "bettergi", "random_config": true,  "timeout_min": 30 },
    { "name": "星穹铁道", "adapter": "march7th", "random_config": true,  "timeout_min": 90 },
    { "name": "绝区零",  "adapter": "zzz",      "random_config": false, "timeout_min": 60 },
    { "name": "明日方舟", "adapter": "maa",      "random_config": false, "timeout_min": 30 },
    { "name": "终末地",  "adapter": "maaend",    "random_config": false, "timeout_min": 30 }
  ]
}
```

字段说明：
- `name` / `adapter`：游戏名与适配器名（对应 `scheduler/games/<adapter>.py`）
- `random_config`：`true` 时从 `configs/<adapter>/` 随机抽一个配置单套用
- `timeout_min`：最长等待分钟数，超时强制关闭并继续下一个
- `cooldown_sec`：每款游戏结束后停几秒再开下一款（等进程清理干净）
- `run_hour` / `run_minute`：常驻模式的每日执行时间

---

## 四、配置单机制

在 `scheduler/configs/<adapter>/` 下预写 JSON 配置单，调度器执行到该游戏时会把配置单**合并进游戏真实配置文件**（改前自动备份到 `scheduler/state/backup/`）。

- `random_config=true` 的游戏每次随机选一个配置单（如原神每天随机刷不同秘境、星铁随机刷不同材料本）。
- 配置单默认写入各适配器约定的目标文件；需要指定时可在配置单里加 `"target": "完整路径"`。

更多细节见 `scheduler/README.md`。

---

## 五、注意事项

- **不要上传**：`scheduler/python/`、`scheduler/logs/`、`scheduler/state/`、5 个工具目录及压缩包（已写入 `.gitignore`）。换机器后重跑 `setup.ps1` 即可。
- 调度器以管理员权限运行，游戏工具会自提权；首次运行时注意放行 UAC 提示。
- 差分宇宙（星铁模拟宇宙）单局约 30~60 分钟，星铁超时给到了 90 分钟；如需关闭模拟宇宙，改 `configs/march7th/` 对应配置单。
- 原神一条龙已配置「合成树脂 → 每日委托 → 秘境清体力 → 领奖 → 关闭游戏」；如需改秘境，改 `configs/bettergi/` 下配置单。
