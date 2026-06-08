
import os
import sys
import time

DB_PATH = 'coshub.db'

if sys.platform == 'win32':
    import ctypes
    import subprocess
    import re

    print('🔍 正在查找占用 coshub.db 的进程...')
    
    # 使用 handle.exe 或者直接通过 tasklist
    # 先尝试用 tasklist 找 python 进程
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'], 
                         capture_output=True, text=True, encoding='gbk', errors='ignore')
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        pids = []
        for line in lines:
            if line.strip():
                parts = line.split(',')
                if len(parts)>=2:
                    try:
                        pid = int(parts[1].strip('"'))
                        pids.append(pid)
                    except:
                        pass
        if pids:
            print(f'⚠️  找到 {len(pids)} 个 python 进程：{pids}')
            print('⚠️  请先在对应的终端按 Ctrl+C 停止后端！')
            time.sleep(3)

    print('🔄 现在尝试删除数据库...')
    
    # 尝试重命名旧数据库而不是删除（作为备选方案）
    if os.path.exists(DB_PATH):
        try:
            backup_name = f'coshub_old_{int(time.time())}.db'
            os.rename(DB_PATH, backup_name)
            print(f'✅ 已将旧数据库重命名为 {backup_name}，现在可以启动后端了！')
        except Exception as e:
            print(f'❌ 操作失败，错误: {e}')
            print('❌ 请手动按 Ctrl+C 停止正在运行的后端终端后再运行脚本！')
            sys.exit(1)
    else:
        print(f'✅ 没有找到旧数据库，直接启动后端即可！')

else:
    # 非 Windows，直接尝试删除
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print(f'✅ 删除了旧数据库 {DB_PATH}')
        except Exception as e:
            print(f'❌ 删除失败，错误: {e}')
    else:
        print(f'✅ 没有找到旧数据库')

print('\n✅ 完成！现在可以启动后端了！')

