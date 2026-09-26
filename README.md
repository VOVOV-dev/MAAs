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

