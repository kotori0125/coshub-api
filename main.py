from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

import models, auth
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="COSHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schemas ──────────────────────────────────────────
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
        "created_at": str(post.created_at),
        "comments_count": len(post.comments),
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
        role="admin" if data.phone == "admin" else "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
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
    return user_to_dict(user)

@app.get("/api/users")
def get_users(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    return [user_to_dict(u) for u in db.query(models.User).all()]

# ── 帖子接口 ──────────────────────────────────────────
@app.get("/api/posts")
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).order_by(models.Post.created_at.desc()).all()
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
def like_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    post.likes += 1
    db.commit()
    return {"likes": post.likes}

# ── 评论接口 ──────────────────────────────────────────
@app.get("/api/posts/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(models.Comment).filter(models.Comment.post_id == post_id).all()
    return [{"id": c.id, "text": c.text, "author": c.author_name, "time": str(c.created_at)} for c in comments]

@app.post("/api/comments")
def create_comment(data: CommentIn, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    comment = models.Comment(
        text=data.text,
        post_id=data.post_id,
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
        total=data.total,
        remark=data.remark,
        pay_method=data.pay_method,
    )
    db.add(order)
    db.commit()
    return {"success": True, "order_id": order.id}

@app.get("/api/orders")
def get_orders(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.buyer == current_user.username).all()
    return [{"id": o.id, "total": o.total, "status": o.status, "created_at": str(o.created_at)} for o in orders]

# ── 消息接口 ──────────────────────────────────────────
@app.post("/api/messages")
def send_message(data: MessageIn, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    msg = models.Message(sender=current_user.username, receiver=data.receiver, text=data.text)
    db.add(msg)
    db.commit()
    return {"success": True}

@app.get("/api/messages/{other_user}")
def get_messages(other_user: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    msgs = db.query(models.Message).filter(
        ((models.Message.sender == current_user.username) & (models.Message.receiver == other_user)) |
        ((models.Message.sender == other_user) & (models.Message.receiver == current_user.username))
    ).order_by(models.Message.created_at).all()
    return [{"id": m.id, "sender": m.sender, "text": m.text, "time": str(m.created_at)} for m in msgs]

@app.get("/")
def root():
    return {"message": "COSHub API 运行正常 🎭"}
