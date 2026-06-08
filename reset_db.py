
import os
import time

DB_PATH = 'coshub.db'

if not os.path.exists(DB_PATH):
    print(f'⚠️  没有找到旧数据库')
else:
    retries = 3
    success = False
    for i in range(retries):
        try:
            os.remove(DB_PATH)
            print(f'✅ 删除了旧数据库 {DB_PATH}')
            success = True
            break
        except PermissionError:
            if i < retries - 1:
                print(f'⚠️  文件被占用，正在等待（第 {i+1}/{retries} 次重试）...')
                time.sleep(2)
            else:
                print('❌ 删除失败，请先按 Ctrl+C 停止后端后再运行本脚本！')

if success:
    print('✅ 数据库已重置，现在启动后端即可自动创建新表！')

