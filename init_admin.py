
from database import SessionLocal, engine
import models, auth
from datetime import datetime

# 创建表
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()

# 检查是否已有 admin
admin = db.query(models.User).filter(models.User.phone == "admin").first()
if not admin:
    # 创建 admin
    admin = models.User(
        username="coshub_admin",
        phone="admin",
        password=auth.get_password_hash("admin123"),
        role="admin",
        verified=True,
        points=100
    )
    db.add(admin)
    db.commit()
    print("✅ Admin created:")
    print("   账号: admin")
    print("   密码: admin123")
else:
    print("ℹ️ Admin already exists")

db.close()
