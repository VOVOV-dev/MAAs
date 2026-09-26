# ============================================================
#  统一游戏日常调度器 - 一键部署脚本
#
#  功能：自动下载并解压
#    1. 绿色便携 Python 3.12（仅调度器用）
#    2. 5 款游戏自动代理工具（MAA / MaaEnd / BetterGI / March7th / OneDragon）
#
#  用法（先 cd 到仓库根目录，例如 d:\MAAs）：
#    powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
#
#  支持断点续传：中断后重跑即可接着下载，已下载部分不会重下。
#  游戏本体（原神/星铁/绝区零/终末地/明日方舟模拟器）需自行安装，本脚本不涉及。
# ============================================================

$ErrorActionPreference = "Stop"

# ---- 代理设置（挂梯子）------------------------------------
# TUN/全局模式：无需设置，直接运行。
# HTTP/SOCKS 系统代理：取消下面两行注释并改成实际端口（Clash 常见 7890/7897）：
# $env:HTTPS_PROXY = "http://127.0.0.1:7890"
# $env:HTTP_PROXY  = "http://127.0.0.1:7890"
# -----------------------------------------------------------

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Tmp  = Join-Path $Root "downloads"

New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

# ---------- 通用函数 ----------
function Download-File {
    param([string]$Url, [string]$Out)
    if (Test-Path $Out) {
        $mb = [math]::Round((Get-Item $Out).Length / 1MB, 1)
        Write-Host "  已存在 $Out（$mb MB），跳过下载" -ForegroundColor Yellow
    } else {
        Write-Host "  下载 $Url" -ForegroundColor Cyan
        curl.exe -L --retry 5 --retry-delay 3 -C - -o $Out $Url
        if ($LASTEXITCODE -ne 0) { throw "下载失败：$Url" }
    }
    $mb = [math]::Round((Get-Item $Out).Length / 1MB, 1)
    Write-Host "  ✔ 就绪 $Out（$mb MB）" -ForegroundColor Green
}

function Expand-Archive2 {
    param([string]$Archive, [string]$Dest, [int]$Strip = 0)
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    $tarArgs = @("-xf", $Archive, "-C", $Dest)
    if ($Strip -gt 0) { $tarArgs += "--strip-components", "$Strip" }
    tar.exe @tarArgs
    if ($LASTEXITCODE -ne 0) { throw "解压失败：$Archive" }
    Write-Host "  ✔ 已解压到 $Dest" -ForegroundColor Green
}

function Test-Installed {
    param([string]$ExePath)
    if (Test-Path $ExePath) {
        Write-Host "  已安装，跳过：$ExePath" -ForegroundColor DarkGreen
        return $true
    }
    return $false
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Magenta
Write-Host "  统一游戏日常调度器 - 一键部署"
Write-Host "=================================================" -ForegroundColor Magenta

# ===================== 1. Python =====================
Write-Host ""
Write-Host "▶ [1/6] 绿色 Python 3.12.10（调度器运行时）" -ForegroundColor White
$pyExe = Join-Path $Root "scheduler\python\python.exe"
if (-not (Test-Installed $pyExe)) {
    $pyZip = Join-Path $Tmp "python-3.12.10-embed-amd64.zip"
    Download-File "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip" $pyZip
    Expand-Archive2 $pyZip (Join-Path $Root "scheduler\python") 0
}

# ===================== 2. MAA（明日方舟） =====================
Write-Host ""
Write-Host "▶ [2/6] 明日方舟 MAA v6.18.0" -ForegroundColor White
$maaExe = Join-Path $Root "MAA-v6.18.0-win-x64\MAA.exe"
if (-not (Test-Installed $maaExe)) {
    $maaZip = Join-Path $Tmp "MAA-v6.18.0-win-x64.zip"
    Download-File "https://github.com/MaaAssistantArknights/MaaAssistantArknights/releases/download/v6.18.0/MAA-v6.18.0-win-x64.zip" $maaZip
    Expand-Archive2 $maaZip $Root 0
}

# ===================== 3. MaaEnd（终末地） =====================
Write-Host ""
Write-Host "▶ [3/6] 终末地 MaaEnd v2.29.0" -ForegroundColor White
$maaendExe = Join-Path $Root "Endfield\MaaEnd.exe"
if (-not (Test-Installed $maaendExe)) {
    $maaendZip = Join-Path $Tmp "MaaEnd-win-x86_64-v2.29.0.zip"
    Download-File "https://github.com/MaaEnd/MaaEnd/releases/download/v2.29.0/MaaEnd-win-x86_64-v2.29.0.zip" $maaendZip
    Expand-Archive2 $maaendZip (Join-Path $Root "Endfield") 0
}

# ===================== 4. BetterGI（原神） =====================
Write-Host ""
Write-Host "▶ [4/6] 原神 BetterGI v0.65.0" -ForegroundColor White
$bettergiExe = Join-Path $Root "Genshin\BetterGI.exe"
if (-not (Test-Installed $bettergiExe)) {
    $bettergi7z = Join-Path $Tmp "BetterGI_v0.65.0.7z"
    Download-File "https://github.com/babalae/better-genshin-impact/releases/download/0.65.0/BetterGI_v0.65.0.7z" $bettergi7z
    Expand-Archive2 $bettergi7z (Join-Path $Root "Genshin") 1
}

# ===================== 5. March7th（星穹铁道） =====================
Write-Host ""
Write-Host "▶ [5/6] 星穹铁道 March7thAssistant v2026.9.25" -ForegroundColor White
$marchExe = Join-Path $Root "StarRail\March7th Assistant.exe"
if (-not (Test-Installed $marchExe)) {
    $march7z = Join-Path $Tmp "March7thAssistant_full.7z"
    Download-File "https://github.com/moesnow/March7thAssistant/releases/download/v2026.9.25/March7thAssistant_full.7z" $march7z
    Expand-Archive2 $march7z (Join-Path $Root "StarRail") 1
}

# ===================== 6. OneDragon（绝区零） =====================
Write-Host ""
Write-Host "▶ [6/6] 绝区零 OneDragon v2.5.2" -ForegroundColor White
$zzzExe = Join-Path $Root "ZZZ\OneDragon-RuntimeLauncher.exe"
if (-not (Test-Installed $zzzExe)) {
    $zzzZip = Join-Path $Tmp "ZenlessZoneZero-OneDragon-v2.5.2-WithRuntime-Full.zip"
    Download-File "https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/releases/download/v2.5.2/ZenlessZoneZero-OneDragon-v2.5.2-WithRuntime-Full.zip" $zzzZip
    Expand-Archive2 $zzzZip (Join-Path $Root "ZZZ") 0
}

# 清理下载的压缩包
Remove-Item $Tmp -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "  ✅ 部署完成！" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
Write-Host "后续步骤（详见 README.md）："
Write-Host "  1. 安装运行时：.NET 8 桌面运行时（BetterGI）、.NET 10 桌面运行时（MAA）"
Write-Host "  2. 安装并登录游戏本体（原神/星铁/绝区零/终末地；明日方舟用 MuMu 模拟器）"
Write-Host "  3. 首次打开各工具完成初始化配置"
Write-Host "  4. 验证：scheduler\python\python.exe scheduler\scheduler.py --discover"
Write-Host "  5. 试跑：scheduler\python\python.exe scheduler\scheduler.py --dry-run"
Write-Host ""
Read-Host "按回车键退出"
