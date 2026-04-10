from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Veritabanı nesnemizi oluşturuyoruz. app.py içinde uygulamaya bağlanacak.
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    Sisteme kayıtlı kullanıcıları temsil eden model.
    Mühendislik notu: UserMixin, Flask-Login'in is_authenticated, is_active gibi 
    gerekli olan temel özelliklerini otomatik sağlar.
    """
    id = db.Column(db.Integer, primary_key=True)
    
    # Benzersiz (unique) ve boş bırakılamaz (nullable=False) alanlar
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # Kişisel detaylar
    isim = db.Column(db.String(50), nullable=False)
    soyisim = db.Column(db.String(50), nullable=False)
    bolum = db.Column(db.String(100), nullable=False)
    sinif = db.Column(db.String(10), nullable=False)
    cinsiyet = db.Column(db.String(20), default='Erkek')
    
    # Güvenlik için şifrelerin sadece hash (özeti) tutulur, düz metin tutulmaz!
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Kullanıcı kayıt olduktan sonra admin onaylayana kadar sisteme giremez
    is_approved = db.Column(db.Boolean, default=False)
    
    # Kullanıcının admin (yönetici) yetkisi olup olmadığı
    is_admin = db.Column(db.Boolean, default=False)
    
    # Profil bilgileri
    profile_pic = db.Column(db.String(255), default='default.png')
    bio = db.Column(db.String(500), nullable=True)
    
    # Tablolar arası ilişkiler (Relationships)
    # lazy=True ile bu verilere ihtiyaç duyulduğunda veritabanından çekilmesini sağlıyoruz (Performans)
    messages = db.relationship('Message', backref='sender', lazy=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    documents = db.relationship('Document', backref='uploader', lazy=True)

class Message(db.Model):
    """
    Sohbet kısmındaki mesajları tutan model.
    Genel sohbet odaklı tasarlanmıştır.
    """
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # Mesajın atılma zamanı (Sunucu saati ile utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Mesajı gönderen kullanıcı (Foreign Key ile User tablosuna bağlıyoruz)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Dosya ekleri eklendi
    file_url = db.Column(db.String(255), nullable=True) # Dosya adı
    file_type = db.Column(db.String(50), nullable=True) # 'image' veya 'document'
    original_file_name = db.Column(db.String(255), nullable=True)

class Post(db.Model):
    """
    Ana akışta (Feed) paylaşılan gönderileri tutan model.
    """
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # Opsiyonel resim veya link alanları
    image_url = db.Column(db.String(255), nullable=True)
    link = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Gönderiyi oluşturan kullanıcı (Foreign Key)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # İlişkiler
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan', lazy=True)
    likes = db.relationship('PostLike', backref='post', cascade='all, delete-orphan', lazy=True)

    @property
    def like_count(self):
        return sum(1 for like in self.likes if like.is_like)

    @property
    def dislike_count(self):
        return sum(1 for like in self.likes if not like.is_like)

class Document(db.Model):
    """
    Döküman arşivi için kullanılacak model.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    
    # Dökümanın kategorisi (Örn: Ders Notu, Sınav Sorusu, Proje)
    category = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Dökümanı yükleyen kullanıcı (Foreign Key)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    likes = db.relationship('DocumentLike', backref='document', cascade='all, delete-orphan', lazy=True)
    
    @property
    def like_count(self):
        return sum(1 for like in self.likes if like.is_like)
        
    @property
    def dislike_count(self):
        return sum(1 for like in self.likes if not like.is_like)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    author = db.relationship('User', backref='user_comments')

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    is_like = db.Column(db.Boolean, nullable=False)

class DocumentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    is_like = db.Column(db.Boolean, nullable=False)
