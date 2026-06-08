Write-Host "🎭 启动 COSHub 全栈应用..."

Write-Host "`n🚀 启动后端服务..."
Start-Process -FilePath "python" -ArgumentList "main.py" -WorkingDirectory (Get-Location) -NoNewWindow

Start-Sleep -Seconds 3

Write-Host "`n🚀 启动前端服务..."
Set-Location ".\coshub"
Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory (Get-Location) -NoNewWindow

Write-Host "`n✅ 服务启动完成！"
Write-Host "📍 后端 API: http://localhost:8000"
Write-Host "📍 前端页面: http://localhost:5173