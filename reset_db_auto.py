
import os
import sys
import time
import subprocess

DB_PATH = 'coshub.db'

if sys.platform == 'win32':
    print('🔍 正在查找占用 coshub.db 的进程...')
    
    # 方法1: 用 wmic 查找所有 python.exe
    print('🔍 查找所有 Python 进程...')
    try:
        result = subprocess.run(
            ['wmic', 'process', 'where', 'name="python.exe"', 'get', 'ProcessId', '/format:csv'],
            capture_output=True, text=True, encoding='gbk', errors='ignore', timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            pids = []
            for line in lines:
                if line.strip() and 'ProcessId' not in line:
                    parts = [p.strip() for p in line.split(',') if p.strip()]
                    if len(parts)>=2:
                        try:
                            pid = int(parts[1])
                            pids.append(pid)
                        except:
                            pass
            if pids:
                print(f'⚠️  找到 {len(pids)} 个 Python 进程：{pids}')
                print('⚠️  正在强制停止它们...')
                for pid in pids:
                    try:
                        subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                     capture_output=True, timeout=2)
                        print(f'✅ 已停止 PID {pid}')
                    except Exception as e:
                        pass
    except Exception as e:
        print(f'⚠️  查找进程失败: {e}')
    
    print('⏳ 等待 2 秒让系统释放...')
    time.sleep(2)
    
    # 方法2: 尝试重命名（如果还不行）
    if os.path.exists(DB_PATH):
        for attempt in range(3):
            try:
                os.remove(DB_PATH)
                print(f'✅ 成功删除数据库！')
                break
            except Exception as e:
                if attempt < 2:
                    print(f'⚠️  还在被占用，重试 {attempt+1}/3...')
                    time.sleep(1)
                else:
                    print('⚠️  无法删除，尝试重命名...')
                    try:
                        backup_name = f'coshub_old_{int(time.time())}.db'
                        os.rename(DB_PATH, backup_name)
                        print(f'✅ 已将旧数据库重命名为 {backup_name}')
                    except Exception as e2:
                        print(f'❌ 失败，错误: {e2}')
                        print('❌ 请手动关闭所有终端后再试！')
                        sys.exit(1)

else:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f'✅ 删除了旧数据库 {DB_PATH}')

print('\n🎉 完成！现在可以启动后端了！')

