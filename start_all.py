
import os
import sys
import subprocess
import time
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = BASE_DIR
FRONTEND_DIR = os.path.join(BASE_DIR, 'coshub')

BACKEND_CMD = ['uvicorn', 'main:app', '--reload', '--port', '8000']
FRONTEND_CMD = ['npm', 'run', 'dev']

print('='*60)
print('  🚀 COSHub 一键启动脚本')
print('='*60)

# 检查目录是否存在
if not os.path.exists(FRONTEND_DIR):
    print(f'❌ 找不到前端目录 {FRONTEND_DIR}')
    sys.exit(1)

# 检查依赖是否存在
print('\n📦 检查依赖...')

# 后端
backend_ok = False
try:
    import fastapi
    import uvicorn
    backend_ok = True
except ImportError:
    print(f'⚠️  后端依赖未安装，正在尝试安装...')
    try:
        subprocess.run(['pip', 'install', '-r', 'requirements.txt'], cwd=BACKEND_DIR, check=True)
        backend_ok = True
        print('✅ 后端依赖安装成功！')
    except:
        print(f'❌ 后端依赖安装失败，请手动运行 pip install -r requirements.txt')

if not backend_ok:
    print(f'⚠️  后端依赖可能有问题，尝试直接启动...')

# 检查 node_modules (前端)
if not os.path.exists(os.path.join(FRONTEND_DIR, 'node_modules')):
    print(f'⚠️  前端依赖未安装，正在尝试安装...')
    try:
        subprocess.run(['npm', 'install'], cwd=FRONTEND_DIR, check=True)
        print('✅ 前端依赖安装成功！')
    except:
        print(f'⚠️  npm install 失败，请手动在 coshub 目录运行 npm install')

print('\n🚀 正在启动服务...')
print('  - 后端: http://127.0.0.1:8000')
print('  - 前端: http://127.0.0.1:5173')

# Windows 下用 start 命令分开终端（最简单）
if sys.platform == 'win32':
    # 启动后端
    backend_script = os.path.join(BACKEND_DIR, 'start_backend.bat')
    with open(backend_script, 'w', encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('cd /d "' + BACKEND_DIR + '"\n')
        f.write('uvicorn main:app --reload --port 8000\n')
        f.write('pause\n')

    # 启动前端
    frontend_script = os.path.join(BACKEND_DIR, 'start_frontend.bat')
    with open(frontend_script, 'w', encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('cd /d "' + FRONTEND_DIR + '"\n')
        f.write('npm run dev\n')
        f.write('pause\n')

    print(f'\n✅ 正在打开后端终端...')
    os.startfile(backend_script)

    print(f'✅ 正在打开前端终端...')
    time.sleep(2)
    os.startfile(frontend_script)

    print(f'\n✅ 正在打开浏览器访问前端...')
    time.sleep(3)
    webbrowser.open('http://127.0.0.1:5173')

    print('\n'+'='*60)
    print('  ✅ 启动完成！')
    print('  👉 后端: http://127.0.0.1:8000/docs (API文档)')
    print('  👉 前端: http://127.0.0.1:5173')
    print('  💡 关闭终端即可停止服务')
    print('='*60)

else:
    print('\n❌ 本脚本仅支持 Windows 系统！')

