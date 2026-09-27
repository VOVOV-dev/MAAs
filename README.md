# 游戏日常调度器（米+舟系）

5 款游戏每日自动化，按顺序依次执行：**原神 → 星穹铁道 → 绝区零 → 明日方舟 → 终末地**。

## 项目结构

```
d:\MAAs\
├─ setup.ps1             一键部署：下载 Python + 5 款工具并解压
├─ download.ps1          仅下载压缩包（备选）
├─ plan.txt              日常需求备忘
├─ 一图流-243-一天两换-MAA.json   MAA 作业文件
├─ scheduler/
│  ├─ scheduler.py       主入口
│  ├─ plan.json          调度计划（顺序 / 超时 / 随机配置）
│  ├─ games/             5 个游戏适配器
│  ├─ configs/           配置单（原神秘境、星铁材料本等）
│  ├─ python/            Python 运行时（setup.ps1 生成）
│  ├─ logs/              运行日志（自动生成）
│  └─ state/             路径缓存 / 配置备份（自动生成）
├─ MAA-v6.18.0-win-x64/  明日方舟 MAA（setup.ps1 生成）
├─ Endfield/             终末地 MaaEnd（setup.ps1 生成）
├─ Genshin/              原神 BetterGI（setup.ps1 生成）
├─ StarRail/             星铁 March7th（setup.ps1 生成）
└─ ZZZ/                  绝区零 OneDragon（setup.ps1 生成）
```

## 克隆后操作

**1. 装运行时（两个都要）**

- .NET 8 桌面运行时 x64：https://dotnet.microsoft.com/download/dotnet/8.0
- .NET 10 桌面运行时 x64：https://dotnet.microsoft.com/download/dotnet/10.0

**2. 部署工具**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

自动下载并解压 Python + 5 款工具，支持断点续传，中断重跑即可。

**3. 装游戏本体并登录**

装哪个盘都行，调度器会自动发现。

| 游戏 | 程序 | 获取 |
|---|---|---|
| 原神 | `YuanShen.exe` | ys.mihoyo.com |
| 星穹铁道 | `StarRail.exe` | sr.mihoyo.com |
| 绝区零 | `ZenlessZoneZero.exe` | zzz.mihoyo.com |
| 终末地 | `Endfield.exe` | endfield.hypergryph.com |
| 明日方舟 | MuMu 12 模拟器内 | 装 MuMu 12 模拟器 + 游戏 |

每款游戏**手动打开登录一次**，保持登录态。

**4. 各工具首次配置（每个只做一次）**

- **MAA**：连接模拟器（MuMu 12 adb 地址 `127.0.0.1:16384`，老版 `127.0.0.1:7555`），设好关卡
- **MaaEnd**：控制器选 `win32-Front`，确认有「快速日常」
- **BetterGI / March7th / OneDragon**：各打开一次，确认能识别游戏窗口

**5. 验证运行**

```powershell
scheduler\python\python.exe scheduler\scheduler.py --discover   # 确认路径都找到
scheduler\python\python.exe scheduler\scheduler.py --dry-run    # 预览，不启动
scheduler\python\python.exe scheduler\scheduler.py --once       # 跑一轮
scheduler\python\python.exe scheduler\scheduler.py              # 常驻，每天 4:00 跑
```

## 注意事项

- 建议克隆到 `d:\MAAs`；放别处也能用，跑一次 `--discover` 会全盘自动定位。
- 调度器需要管理员权限，首次运行请在 UAC 弹窗点「是」。
- 下载工具需访问 GitHub，连不上就在 `setup.ps1` 开头配置代理（`$env:HTTPS_PROXY`）。
- 游戏必须保持登录态、能正常进主界面，否则自动工具无法接管。
- 星铁差分宇宙单局约 30~60 分钟，超时已设 90 分钟。
- 换机器只需重跑 `setup.ps1`；`python/`、`logs/`、`state/` 及 5 个工具目录不提交到 Git。

## 运行配置说明

### 调度计划（`scheduler/plan.json`）

- 每天 **4:00** 自动执行一轮（常驻模式）
- 时间段：**4:00–18:00** 跑全部 5 款；**18:00–4:00** 只跑明日方舟 MAA
- 顺序：原神 → 星穹铁道 → 绝区零 → 明日方舟 → 终末地
- 星铁超时 90 分钟（差分宇宙耗时），其余 30–60 分钟

### 各游戏关键配置

| 游戏 | 配置要点 |
|---|---|
| 原神 BetterGI | 一条龙：合成树脂 → 自动秘境 → 领取每日奖励；`random_config` 随机刷秘境 |
| 星铁 March7th | 模拟宇宙每周打 1 局（`universe_count: 1`）；随机刷材料本；跑完自动退出（`after_finish: Exit`） |
| 绝区零 OneDragon | 6 项日常（刮刮卡/录像店/咖啡/体力/迷失之地/枯萎之都）；空洞每周打一次 |
| 明日方舟 MAA | 全天可跑（夜间只跑它）；连 MuMu 模拟器 |
| 终末地 MaaEnd | 快速日常；控制器 `win32-Front` |

## 常见问题排查

1. **星铁跑完停在「按回车」** —— 配置文件被重置了。改 `StarRail/config.yaml`：`pause_after_success: false`、`after_finish: Exit`。

2. **星铁 `config.yaml` 解析失败 / 提示已用默认配置** —— March7th 会把 `power_plan` 保存成多行格式，调度器写配置时残留旧值所致（已修复）。若再遇到：删除 `config.yaml`（March7th 会自动重建），或从 `scheduler/state/backup/march7th/` 恢复，再重跑一次调度器。

3. **绝区零启动几秒就被关闭** —— 进程名检测 bug（长进程名被截断），已修复。若复现，确认 `scheduler/games/base.py` 的 `process_exists` 用的是 `tasklist /FO CSV`。

4. **星铁模拟宇宙一次要打很多局** —— `universe_count` 控制每次打几局：`1` = 每周打 1 局；想刷满周常积分改回 `34`。

5. **绝区零空洞每天重复刷** —— 改 `ZZZ/config/01/one_dragon/lost_void.yml` 和 `withered_domain.yml`，`weekly_plan_times: 1` = 每周 1 次。

6. **某游戏提示「未找到游戏目录」** —— 游戏本体没装或没登录过。装好登录后跑 `--discover` 重新扫描；路径缓存可删 `scheduler/state/paths.json` 后重扫。

7. **排查入口** —— 调度器日志 `scheduler/logs/<游戏名>.log`；OneDragon 日志 `ZZZ/.log/log.txt`；March7th 日志 `StarRail/logs/`。

8. **换机器后配置丢失** —— `python/`、`logs/`、`state/` 及 5 个工具目录不入库。重跑 `setup.ps1` 后，游戏内配置（星铁 `config.yaml`、绝区零空洞、原神一条龙等）需按上表重设一次。

