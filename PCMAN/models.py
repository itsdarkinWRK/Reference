from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from database import db
from sqlalchemy import Column, Integer, String, Float, JSON, Text, Boolean, ForeignKey, Index, event
from sqlalchemy.orm import relationship
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import Pool
import time

# MySQL kapcsolat újrapróbálkozási logika
@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # Újracsatlakozás a MySQL szerverhez
        connection_proxy._pool.dispose()
        raise OperationalError(
            "MySQL server has gone away",
            "Database connection was lost, trying to reconnect",
            None,
        )
    cursor.close()

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile = db.relationship('UserProfile', uselist=False, back_populates='user')
    configurations = db.relationship('Configuration', back_populates='user', lazy=True)
    forum_topics = db.relationship('ForumTopic', foreign_keys='ForumTopic.user_id', backref='author', lazy=True)
    forum_replies = db.relationship('ForumReply', backref='author', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    full_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    profile_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='profile', cascade="all, delete-orphan", single_parent=True)

    def __repr__(self):
        return f'<UserProfile {self.full_name}>'


class Configuration(db.Model):
    __tablename__ = 'configurations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    components = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='configurations')


class Component(db.Model):
    __tablename__ = 'components'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    attributes = db.Column(db.JSON, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Component {self.name}>"


class ForumCategory(db.Model):
    __tablename__ = 'forum_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    order = db.Column(db.Integer, default=0)
    topics = db.relationship('ForumTopic', backref='category', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ForumCategory {self.name}>'


class ForumTopic(db.Model):
    __tablename__ = 'forum_topics'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'), nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    replies = db.relationship('ForumReply', backref='topic', lazy=True)

    @property
    def replies_count(self):
        """Visszaadja a válaszok számát"""
        return db.session.query(ForumReply).filter_by(topic_id=self.id).count()

    def __repr__(self):
        return f'<ForumTopic {self.title}>'


class ForumReply(db.Model):
    __tablename__ = 'forum_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topics.id'), nullable=False)
    
    # A kapcsolatokat a másik oldalon definiáljuk
    upvotes = db.relationship('ForumUpvote', backref='reply', lazy='joined', cascade='all, delete-orphan')

    def has_user_upvote(self, user_id):
        """Ellenőrzi, hogy a felhasználó upvote-olta-e már ezt a választ"""
        if not user_id:
            return False
        return any(upvote.user_id == user_id for upvote in self.upvotes)

    @property
    def upvotes_count(self):
        """Visszaadja az upvote-ok számát"""
        return len(self.upvotes)

    def __repr__(self):
        return f'<ForumReply {self.id}>'


class ForumUpvote(db.Model):
    __tablename__ = 'forum_upvotes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reply_id = db.Column(db.Integer, db.ForeignKey('forum_replies.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'reply_id', name='unique_user_reply_upvote'),
    )

    def __repr__(self):
        return f'<ForumUpvote {self.id}>'
