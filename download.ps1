# ============================================================
#  5 款游戏自动代理工具 绿色便携包 下载脚本（仅下载压缩包，不解压）
#  如需自动解压，请改用 setup.ps1（一键部署：下载 + 解压 + Python）
#  正确运行方式（避免窗口闪退）：
#    cd d:\MAAs
#    powershell -NoProfile -ExecutionPolicy Bypass -File .\download.ps1
#  支持断点续传，中断后重跑即可接着下
# ============================================================

# ---- 代理设置（挂梯子）------------------------------------
# TUN/全局模式：无需设置，直接运行。
# HTTP/SOCKS 系统代理：取消下面两行注释并改成实际端口：
# $env:HTTPS_PROXY = "http://127.0.0.1:7890"
# $env:HTTP_PROXY  = "http://127.0.0.1:7890"
# （Clash 常见 HTTP 端口 7890 / 7897）
# -----------------------------------------------------------

function Download-File {
    param([string]$Title, [string]$Url, [string]$Out)
    Write-Host ""
    Write-Host "-------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "▶ $Title" -ForegroundColor White
    Write-Host "  目标: $Out" -ForegroundColor DarkGray
    if (Test-Path $Out) {
        $mb = [math]::Round((Get-Item $Out).Length / 1MB, 1)
        Write-Host "  已存在 $mb MB，断点续传..." -ForegroundColor Yellow
    } else {
        Write-Host "  开始下载，请稍候..." -ForegroundColor Cyan
    }
    curl.exe -L --retry 5 --retry-delay 3 -C - -o $Out $Url
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✘ 失败（退出码 $LASTEXITCODE）。重跑脚本即可续传。" -ForegroundColor Red
        return $false
    }
    $mb = [math]::Round((Get-Item $Out).Length / 1MB, 1)
    Write-Host "  ✔ 完成，$mb MB" -ForegroundColor Green
    return $true
}

Write-Host ""
Write-Host "开始下载 5 款游戏自动代理工具..." -ForegroundColor Magenta

$ok = $true
$ok = (Download-File -Title "[1/5] 明日方舟 MAA (v6.18.0)" -Out "d:\MAAs\MAA-v6.18.0-win-x64.zip" -Url "https://github.com/MaaAssistantArknights/MaaAssistantArknights/releases/download/v6.18.0/MAA-v6.18.0-win-x64.zip") -and $ok
$ok = (Download-File -Title "[2/5] 终末地 MaaEnd (v2.29.0)" -Out "d:\MAAs\Endfield\MaaEnd-win-x86_64-v2.29.0.zip" -Url "https://github.com/MaaEnd/MaaEnd/releases/download/v2.29.0/MaaEnd-win-x86_64-v2.29.0.zip") -and $ok
$ok = (Download-File -Title "[3/5] 原神 BetterGI (0.65.0)" -Out "d:\MAAs\Genshin\BetterGI_v0.65.0.7z" -Url "https://github.com/babalae/better-genshin-impact/releases/download/0.65.0/BetterGI_v0.65.0.7z") -and $ok
$ok = (Download-File -Title "[4/5] 星穹铁道 March7thAssistant (v2026.9.25)" -Out "d:\MAAs\StarRail\March7thAssistant_full.7z" -Url "https://github.com/moesnow/March7thAssistant/releases/download/v2026.9.25/March7thAssistant_full.7z") -and $ok
$ok = (Download-File -Title "[5/5] 绝区零 ZZZ-OneDragon (v2.5.2)" -Out "d:\MAAs\ZZZ\ZenlessZoneZero-OneDragon-v2.5.2-WithRuntime-Full.zip" -Url "https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/releases/download/v2.5.2/ZenlessZoneZero-OneDragon-v2.5.2-WithRuntime-Full.zip") -and $ok

Write-Host ""
if ($ok) {
    Write-Host "✅ 全部下载完成！请运行 setup.ps1 解压（或手动解压到对应目录）。" -ForegroundColor Green
} else {
    Write-Host "⚠️ 有失败项，直接重跑脚本即可断点续传（已下载部分不会重下）。" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "提醒：BetterGI 运行还需 .NET 8 运行时；MAA 需要 .NET 10 运行时。" -ForegroundColor Yellow
Write-Host "      详见根目录 README.md 部署清单。" -ForegroundColor Yellow
Write-Host ""
Read-Host "按回车键退出"
