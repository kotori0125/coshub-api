from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    password = Column(String)
    bio = Column(String, default="")
    city = Column(String, default="")
    role = Column(String, default="user")
    verified = Column(Boolean, default=False)
    verified_label = Column(String, default="")  # 认证后缀
    points = Column(Integer, default=0)
    avatar = Column(String, default="")
    created_at = Column(DateTime, default=datetime.now)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text, default="")
    type = Column(String, default="post")
    image = Column(Text, default="")
    price = Column(Float, nullable=True)
    original_price = Column(Float, nullable=True)
    condition = Column(String, default="")
    role_name = Column(String, default="")
    role_from = Column(String, default="")
    likes = Column(Integer, default=0)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    author_name = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=datetime.now)
    post = relationship("Post", back_populates="comments")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    buyer = Column(String)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    total = Column(Float)
    status = Column(String, default="待发货")
    remark = Column(String, default="")
    pay_method = Column(String, default="")
    created_at = Column(DateTime, default=datetime.now)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String)
    receiver = Column(String)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class PostLike(Base):
    __tablename__ = "post_likes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=datetime.now)

class Follow(Base):
    __tablename__ = "follows"
    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"))
    following_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)

class PointLog(Base):
    __tablename__ = "point_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    action = Column(String)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer)
    user_id = Column(Integer)
    reason = Column(String)
    detail = Column(String)
    handled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
