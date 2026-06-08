from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime
import traceback
import os
import uuid

import models, auth
from database import engine, get_db

app = FastAPI(title="COSHub API")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 先创建所有表
models.Base.metadata.create_all(bind=engine)
print("[OK] 数据库表初始化完成")

# 创建上传目录
os.makedirs("uploads", exist_ok=True)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 自动迁移旧数据库
def migrate_database():
    import sqlite3
    from sqlalchemy import inspect
    conn = sqlite3.connect("coshub.db")
    cursor = conn.cursor()
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    
    # 检查 users.points
    if 'users' in tables:
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        if 'points' not in users_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
                conn.commit()
                print("[OK] 添加 users.points 列")
            except:
                pass
        # 检查 users.avatar
        if 'avatar' not in users_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT ''")
                conn.commit()
                print("[OK] 添加 users.avatar 列")
            except:
                pass
        # 检查 users.verified_label
        if 'verified_label' not in users_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN verified_label TEXT DEFAULT ''")
                conn.commit()
                print("[OK] 添加 users.verified_label 列")
            except:
                pass
    
    # 检查 comments.author_id
    if 'comments' in tables:
        comments_columns = [col['name'] for col in inspector.get_columns('comments')]
        if 'author_id' not in comments_columns:
            try:
                cursor.execute("ALTER TABLE comments ADD COLUMN author_id INTEGER")
                conn.commit()
                print("[OK] 添加 comments.author_id 列")
            except:
                pass
    
    # 建 follows 表
    if 'follows' not in tables:
        cursor.execute("""
            CREATE TABLE follows (
                id INTEGER PRIMARY KEY,
                follower_id INTEGER,
                following_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("[OK] 创建 follows 表")
    
    # 建 point_logs 表
    if 'point_logs' not in tables:
        cursor.execute("""
            CREATE TABLE point_logs (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                action TEXT,
                points INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("[OK] 创建 point_logs 表")
    
    conn.close()

migrate_database()

# ── Schemas ──────────────────────────────────────────
from pydantic import BaseModel

class RegisterIn(BaseModel):
    username: str
    phone: str
    password: str
    role: str = "user"

class LoginIn(BaseModel):
    phone: str
    password: str

class PostIn(BaseModel):
    title: str
    content: str = ""
    type: str = "post"
    image: str = ""
    price: Optional[float] = None
    original_price: Optional[float] = None
    condition: str = ""
    role_name: str = ""
    role_from: str = ""

class CommentIn(BaseModel):
    text: str
    post_id: int

class MessageIn(BaseModel):
    receiver: str
    text: str

class OrderIn(BaseModel):
    total: float
    remark: str = ""
    pay_method: str = ""
    items: list = []

# ── 工具函数 ──────────────────────────────────────────
def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.split(" ")[1]
    phone = auth.decode_token(token)
    if not phone:
        raise HTTPException(status_code=401, detail="Token无效")
    user = db.query(models.User).filter(models.User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user

def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "phone": user.phone,
        "bio": user.bio,
        "city": user.city,
        "role": user.role,
        "verified": user.verified,
        "verified_label": user.verified_label or "",
        "points": user.points,
        "avatar": user.avatar or "",
        "created_at": str(user.created_at),
    }

def post_to_dict(post):
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "type": post.type,
        "image": post.image,
        "price": post.price,
        "original_price": post.original_price,
        "condition": post.condition,
        "role_name": post.role_name,
        "role_from": post.role_from,
        "likes": post.likes,
        "author": post.author.username if post.author else "",
        "author_id": post.author_id,
        "author_avatar": post.author.avatar if post.author else "",
        "created_at": str(post.created_at),
        "comments_count": len(post.comments),
    }

def comment_to_dict(comment):
    return {
        "id": comment.id,
        "text": comment.text,
        "author_name": comment.author_name,
        "author_id": comment.author_id,
        "post_id": comment.post_id,
        "created_at": str(comment.created_at),
    }

def message_to_dict(msg):
    return {
        "id": msg.id,
        "sender": msg.sender,
        "receiver": msg.receiver,
        "text": msg.text,
        "created_at": str(msg.created_at),
    }

def order_to_dict(order):
    return {
        "id": order.id,
        "buyer": order.buyer,
        "buyer_id": order.buyer_id,
        "total": order.total,
        "status": order.status,
        "remark": order.remark,
        "pay_method": order.pay_method,
        "created_at": str(order.created_at),
    }

# ── 用户接口 ──────────────────────────────────────────
@app.post("/api/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.phone == data.phone).first():
        raise HTTPException(status_code=400, detail="手机号已注册")
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = models.User(
        username=data.username,
        phone=data.phone,
        password=auth.get_password_hash(data.password),
        role=data.role if data.role in ["admin", "user"] else "user",
        points=10,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 自动关注所有管理员
    admins = db.query(models.User).filter(models.User.role == "admin").all()
    for admin in admins:
        if admin.id != user.id:
            follow = models.Follow(follower_id=user.id, following_id=admin.id)
            db.add(follow)
    
    # 注册送积分日志
    point_log = models.PointLog(user_id=user.id, action="注册", points=10)
    db.add(point_log)
    db.commit()
    
    token = auth.create_access_token({"sub": user.phone})
    return {"token": token, "user": user_to_dict(user)}

@app.post("/api/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.phone == data.phone).first()
    if not user or not auth.verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="账号或密码错误")
    token = auth.create_access_token({"sub": user.phone})
    return {"token": token, "user": user_to_dict(user)}

@app.get("/api/me")
def get_me(current_user=Depends(get_current_user)):
    return user_to_dict(current_user)

@app.put("/api/me")
def update_me(data: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if "username" in data: user.username = data["username"]
    if "bio" in data: user.bio = data["bio"]
    if "city" in data: user.city = data["city"]
    db.commit()
    db.refresh(user)
    return user_to_dict(user)

@app.post("/api/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...), 
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 保存文件
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    if file_ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        raise HTTPException(status_code=400, detail="只支持 jpg/png/gif/webp 格式")
    
    filename = f"{uuid.uuid4().hex}.{file_ext}"
    file_path = os.path.join("uploads", filename)
    
    # 保存到本地
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 更新用户头像
    avatar_url = f"/uploads/{filename}"
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    user.avatar = avatar_url
    db.commit()
    db.refresh(user)
    
    return {"avatar": avatar_url, "user": user_to_dict(user)}

@app.get("/api/users")
def get_users(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    return [user_to_dict(u) for u in db.query(models.User).all()]

@app.put("/api/users/{user_id}")
def update_user(
    user_id: int,
    data: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if "verified" in data:
        user.verified = data["verified"]
    if "verified_label" in data:
        user.verified_label = data["verified_label"]
    if "role" in data:
        user.role = data["role"]
    db.commit()
    db.refresh(user)
    return user_to_dict(user)

# ── 帖子接口 ──────────────────────────────────────────
@app.get("/api/posts")
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).options(joinedload(models.Post.comments)).order_by(models.Post.created_at.desc()).all()
    return [post_to_dict(p) for p in posts]

@app.post("/api/posts")
def create_post(data: PostIn, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    post = models.Post(
        title=data.title,
        content=data.content,
        type=data.type,
        image=data.image,
        price=data.price,
        original_price=data.original_price,
        condition=data.condition,
        role_name=data.role_name,
        role_from=data.role_from,
        author_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post_to_dict(post)

@app.get("/api/posts/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return post_to_dict(post)

@app.post("/api/posts/{post_id}/like")
def like_post(post_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    existing_like = db.query(models.PostLike).filter(
        models.PostLike.post_id == post_id,
        models.PostLike.user_id == current_user.id
    ).first()
    if existing_like:
        raise HTTPException(status_code=400, detail="已点赞")
    like = models.PostLike(user_id=current_user.id, post_id=post_id)
    db.add(like)
    post.likes += 1
    db.commit()
    return {"likes": post.likes}

@app.delete("/api/posts/{post_id}")
def delete_post(post_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    db.delete(post)
    db.commit()
    return {"message": "删除成功"}

@app.post("/api/reports")
def create_report(data: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    post_id = data.get("post_id")
    reason = data.get("reason", "")
    detail = data.get("detail", "")
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    report = models.Report(
        post_id=post_id,
        user_id=current_user.id,
        reason=reason,
        detail=detail,
    )
    db.add(report)
    db.commit()
    return {"message": "举报已提交"}

@app.get("/api/reports")
def get_reports(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    reports = db.query(models.Report).order_by(models.Report.created_at.desc()).all()
    result = []
    for r in reports:
        post = db.query(models.Post).filter(models.Post.id == r.post_id).first()
        user = db.query(models.User).filter(models.User.id == r.user_id).first()
        result.append({
            "id": r.id,
            "post_id": r.post_id,
            "post_title": post.title if post else "已删除",
            "reason": r.reason,
            "detail": r.detail,
            "user_id": r.user_id,
            "user_name": user.username if user else "",
            "created_at": str(r.created_at),
            "handled": r.handled,
        })
    return result

@app.put("/api/reports/{report_id}")
def handle_report(report_id: int, data: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="举报不存在")
    report.handled = data.get("handled", True)
    db.commit()
    return {"message": "处理成功"}

@app.get("/api/posts/following")
def get_following_posts(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    following_ids = [f.following_id for f in db.query(models.Follow).filter(models.Follow.user_id == current_user.id).all()]
    following_ids.append(current_user.id)
    posts = db.query(models.Post).filter(models.Post.author_id.in_(following_ids)).order_by(models.Post.created_at.desc()).all()
    return format_posts(posts, db)

# ── 评论接口 ──────────────────────────────────────────
@app.get("/api/posts/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(models.Comment).filter(models.Comment.post_id == post_id).order_by(models.Comment.created_at.desc()).all()
    return [comment_to_dict(c) for c in comments]

@app.post("/api/comments")
def create_comment(data: CommentIn, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == data.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    comment = models.Comment(
        text=data.text,
        post_id=data.post_id,
        author_id=current_user.id,
        author_name=current_user.username,
    )
    db.add(comment)
    db.commit()
    return {"success": True}

# ── 订单接口 ──────────────────────────────────────────
@app.post("/api/orders")
def create_order(data: OrderIn, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    order = models.Order(
        buyer=current_user.username,
        buyer_id=current_user.id,
        total=data.total,
        remark=data.remark,
        pay_method=data.pay_method,
    )
    db.add(order)
    db.commit()
    return {"success": True, "order_id": order.id}

@app.get("/api/orders")
def get_orders(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.buyer_id == current_user.id).order_by(models.Order.created_at.desc()).all()
    return [order_to_dict(o) for o in orders]

# ── 消息接口 ──────────────────────────────────────────
@app.post("/api/messages")
def send_message(data: MessageIn, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    msg = models.Message(
        sender=current_user.username,
        receiver=data.receiver,
        text=data.text
    )
    db.add(msg)
    db.commit()
    return {"success": True}

@app.get("/api/messages/{other_user}")
def get_messages(other_user: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    msgs = db.query(models.Message).filter(
        ((models.Message.sender == current_user.username) & (models.Message.receiver == other_user)) |
        ((models.Message.sender == other_user) & (models.Message.receiver == current_user.username))
    ).order_by(models.Message.created_at).all()
    return [message_to_dict(m) for m in msgs]

# ── 关注接口 ──────────────────────────────────────────
@app.get("/api/follows")
def get_follows(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    following = db.query(models.Follow).filter(models.Follow.follower_id == current_user.id).all()
    followers = db.query(models.Follow).filter(models.Follow.following_id == current_user.id).all()
    return {
        "following": [f.following_id for f in following],
        "followers": [f.follower_id for f in followers],
    }

@app.post("/api/follow/{user_id}")
def follow_user(user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能关注自己")
    existing = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user.id,
        models.Follow.following_id == user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已关注")
    follow = models.Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    db.commit()
    return {"message": "关注成功"}

@app.delete("/api/follow/{user_id}")
def unfollow_user(user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    follow = db.query(models.Follow).filter(
        models.Follow.follower_id == current_user.id,
        models.Follow.following_id == user_id
    ).first()
    if not follow:
        raise HTTPException(status_code=400, detail="未关注")
    db.delete(follow)
    db.commit()
    return {"message": "取消关注成功"}

@app.get("/api/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user_to_dict(user)

# ── 积分接口 ──────────────────────────────────────────
@app.get("/api/points/logs")
def get_point_logs(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    logs = db.query(models.PointLog).filter(models.PointLog.user_id == current_user.id).order_by(models.PointLog.created_at.desc()).all()
    return [{"id": l.id, "action": l.action, "points": l.points, "created_at": str(l.created_at)} for l in logs]

@app.post("/api/points/earn")
def earn_points(action: str, points: int = 10, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    user.points += points
    log = models.PointLog(user_id=user.id, action=action, points=points)
    db.add(log)
    db.commit()
    return {"points": user.points}

@app.get("/")
def root():
    return {"message": "COSHub API 运行正常 🎭"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
