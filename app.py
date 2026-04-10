import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

# Modellerimizi içeren dosyadan gerekli yapıları içe aktarıyoruz.
from models import db, User, Message, Post, Document, Comment, PostLike, DocumentLike

# Flask uygulaması nesnesi (App)
app = Flask(__name__)

# --- YAPILANDIRMA (CONFIG) ---
# Yorum: Uygulama çalışırken oturumları şifrelemek ve güvenlik sağlamak için.
# Canlı ortamda (production) environment variable kullanılacak, yoksa karmaşık bir varsayılan şifre devreye girecek.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'x9!fL2#kP4@vM1$yZ8*wN5^qR7(bJ0)tH3+ecX6&')

# Veritabanı bağlantısı: PythonAnywhere Thread Lock önlemi için check_same_thread parametresi eklendi.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db') + '?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Dosyaların yükleneceği klasör yolları ayarlanıyor (Statik yolların bozulmaması için mutlak yol kullanıyoruz).
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # En fazla 16 MB dosya yüklenebilir (Güvenlik)
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Veritabanını Flask'a dahil ediyoruz (init_app)
db.init_app(app)

# Login yöneticimizi başlatıyoruz (Kullanıcı giriş/çıkış süreçleri)
login_manager = LoginManager()
login_manager.login_view = 'login' # Giriş yapılmamışsa kullanıcıyı yönlendireceği rota adı.
login_manager.login_message = 'Lütfen sayfayı görüntülemek için giriş yapın.'
login_manager.init_app(app)

# Flask-Login'in mevcut kullanıcıyı ID'sinden tanımlayabilmesi için gerekli fonksiyon.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Uygulama ilk başlatıldığında, eğer tablolar yoksa oluşturacak (Engine Start)
with app.app_context():
    # Gerekli boş klasörleri projeye ekleyelim
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'profiles'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'posts'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'docs'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'chat'), exist_ok=True)
    
    # DB Tablolarını models.py'ye bakarak oluştur
    db.create_all()
    
    # Varsayılan Admin Kullanıcısı Yoksa Oluştur
    if not User.query.filter_by(is_admin=True).first():
        admin_user = User(
            username='admin',
            email='admin@gelistirici.com',
            password_hash=generate_password_hash('admin123', method='scrypt'),
            isim='Sistem', soyisim='Yöneticisi', bolum='AdminPanel', sinif='Mezun',
            is_approved=True,
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()

# --- ROTALAR (ROUTES) ---

@app.route('/')
@login_required
def index():
    """
    Kök dizin, aynı zamanda Feed (Akış) sayfası.
    Sadece is_approved=True olan kullanıcıların görmesini isteyebiliriz, ama şimdilik
    giriş yapılmışsa feed gösteriyoruz, veya "onay bekliyor" durumu varsa engelleyebiliriz.
    """
    if not current_user.is_approved:
        return render_template('pending.html') # Ayrı bir bekleme sayfası örneği
    
    # Tüm gönderileri (Post) tarihe göre sondan başa sıralayarak çekiyoruz (SQL: ORDER BY DESC)
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Veritabanında (DB) böyle bir kullanıcı var mı bak.
        user = User.query.filter_by(email=email).first()
        
        # Eğer kullanıcı mevcutsa ve Hash'li şifre doğruysa:
        if user and check_password_hash(user.password_hash, password):
            login_user(user) # Session'a kullanıcıyı yazar
            return redirect(url_for('index'))
        else:
            flash('Giriş başarısız. Lütfen e-posta ve şifrenizi kontrol edin.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        isim = request.form.get('isim')
        soyisim = request.form.get('soyisim')
        bolum = request.form.get('bolum')
        sinif = request.form.get('sinif')
        cinsiyet = request.form.get('cinsiyet')
        
        # Aynı kullanıcı adı veya e-posta kullanımında mı?
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('Kullanıcı adı veya e-posta zaten kullanımda.', 'danger')
            return redirect(url_for('register'))
        
        # Security: Şifreyi açık metin girmek çok tehlikelidir! Algoritmalarla karıştırıyoruz.
        hashed_pw = generate_password_hash(password, method='scrypt')
        
        new_user = User(
            username=username, email=email, password_hash=hashed_pw,
            isim=isim, soyisim=soyisim, bolum=bolum, sinif=sinif, cinsiyet=cinsiyet
        )
        # Admin olmadığımız için is_approved False kalıyor (Default)
        
        db.session.add(new_user)
        db.session.commit() # Değişikliği asıl DB'ye yaz.
        
        flash('Kayıt başarılı! Admin onayının ardından giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user() # Session'dan siler
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    """
    Sohbet arayüzünü dönecek ana sayfa
    """
    if not current_user.is_approved:
        return redirect(url_for('index'))
    return render_template('chat.html')

@app.route('/documents')
@login_required
def documents():
    """
    Dökümanların listelendiği sayfa.
    """
    if not current_user.is_approved:
        return redirect(url_for('index'))
    docs = Document.query.order_by(Document.created_at.desc()).all()
    return render_template('documents.html', documents=docs)

@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content')
    link = request.form.get('link')
    file = request.files.get('file')
    
    image_url = None
    if file and file.filename != '' and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext in {'png', 'jpg', 'jpeg', 'gif'}:
            unique_name = str(uuid.uuid4()) + '.' + ext
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'posts', unique_name))
            image_url = unique_name
            
    if content or image_url:
        new_post = Post(content=content or '', image_url=image_url, link=link, user_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        flash('Gönderiniz paylaşıldı.', 'success')
    return redirect(url_for('index'))

@app.route('/upload_document', methods=['POST'])
@login_required
def upload_document():
    title = request.form.get('title')
    category = request.form.get('category')
    file = request.files.get('file')
    
    if title and category and file and file.filename != '' and allowed_file(file.filename):
        unique_name = str(uuid.uuid4())[:8] + '_' + secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'docs', unique_name))
        
        new_doc = Document(title=title, category=category, file_path=unique_name, uploader_id=current_user.id)
        db.session.add(new_doc)
        db.session.commit()
        flash('Döküman başarıyla yüklendi.', 'success')
    else:
        flash('Eksik bilgi veya geçersiz dosya formatı.', 'danger')
        
    return redirect(url_for('documents'))

@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    content = request.form.get('content')
    if content and content.strip():
        comment = Comment(content=content.strip(), user_id=current_user.id, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        flash('Yorum eklendi.', 'success')
    return redirect(url_for('index'))

@app.route('/post/<int:post_id>/vote', methods=['POST'])
@login_required
def vote_post(post_id):
    is_like = request.form.get('is_like') == 'true'
    existing = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing:
        if existing.is_like == is_like:
            db.session.delete(existing)
        else:
            existing.is_like = is_like
    else:
        new_vote = PostLike(user_id=current_user.id, post_id=post_id, is_like=is_like)
        db.session.add(new_vote)
        
    db.session.commit()
    post = Post.query.get(post_id)
    return jsonify({'likes': post.like_count, 'dislikes': post.dislike_count})

@app.route('/document/<int:doc_id>/vote', methods=['POST'])
@login_required
def vote_document(doc_id):
    is_like = request.form.get('is_like') == 'true'
    existing = DocumentLike.query.filter_by(user_id=current_user.id, document_id=doc_id).first()
    
    if existing:
        if existing.is_like == is_like:
            db.session.delete(existing)
        else:
            existing.is_like = is_like
    else:
        new_vote = DocumentLike(user_id=current_user.id, document_id=doc_id, is_like=is_like)
        db.session.add(new_vote)
        
    db.session.commit()
    doc = Document.query.get(doc_id)
    return jsonify({'likes': doc.like_count, 'dislikes': doc.dislike_count})

@app.route('/profile')
@login_required
def profile():
    """
    Kullanıcı profili ve düzenleme sayfası.
    """
    if not current_user.is_approved:
        return redirect(url_for('index'))
        
    post_count = Post.query.filter_by(user_id=current_user.id).count()
    doc_count = Document.query.filter_by(uploader_id=current_user.id).count()
    
    liked_post_count = PostLike.query.filter_by(user_id=current_user.id, is_like=True).count()
    liked_doc_count = DocumentLike.query.filter_by(user_id=current_user.id, is_like=True).count()
    total_likes = liked_post_count + liked_doc_count
        
    return render_template('profile.html', post_count=post_count, doc_count=doc_count, total_likes=total_likes)

@app.route('/upload_profile_pic', methods=['POST'])
@login_required
def upload_profile_pic():
    file = request.files.get('file')
    if file and file.filename != '' and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext in {'png', 'jpg', 'jpeg', 'gif'}:
            unique_name = f"profile_{current_user.id}_{str(uuid.uuid4())[:8]}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', unique_name))
            current_user.profile_pic = unique_name
            db.session.commit()
            flash('Profil fotoğrafınız güncellendi.', 'success')
    else:
        flash('Lütfen geçerli bir dosya seçin.', 'danger')
    return redirect(url_for('profile'))

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if not current_user.is_admin and current_user.id != post.user_id:
        flash('Yetkisiz işlem.', 'danger')
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    flash('Gönderi silindi.', 'info')
    return redirect(url_for('index'))

@app.route('/delete_document/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if not current_user.is_admin and current_user.id != doc.uploader_id:
        flash('Yetkisiz işlem.', 'danger')
        return redirect(url_for('documents'))
    db.session.delete(doc)
    db.session.commit()
    flash('Döküman silindi.', 'info')
    return redirect(url_for('documents'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Yetkisiz erişim.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')
        
        user_to_mod = User.query.get(int(user_id))
        if user_to_mod and not user_to_mod.is_admin: # Admin kendini silemez/değiştiremez
            if action == 'approve':
                user_to_mod.is_approved = True
                flash(f"{user_to_mod.username} adlı kullanıcı onaylandı.", 'success')
            elif action == 'delete':
                db.session.delete(user_to_mod)
                flash(f"{user_to_mod.username} silindi.", 'success')
            elif action == 'reset_password':
                new_pw = request.form.get('new_password')
                if new_pw:
                    user_to_mod.password_hash = generate_password_hash(new_pw)
                    flash(f"{user_to_mod.username} adlı kullanıcının şifresi yenilendi.", 'success')
            db.session.commit()
            return redirect(url_for('admin_panel'))
            
    pending_users = User.query.filter_by(is_approved=False).all()
    approved_users = User.query.filter_by(is_approved=True).all()
    return render_template('admin.html', pending_users=pending_users, approved_users=approved_users)

# --- API UÇ NOKTALARI (API ENDPOINTS FOR FETCH) ---

@app.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    """
    Vanilla JS fetch ile belirli saniyelerde (setInterval) buraya istek atılıp,
    yeni mesajların JSON tipinde dönmesi sağlanacak (Polling).
    Mühendislik notu: Çok fazla kullanıcıda Socket IO daha iyi olsa da
    küçük çaplı/öğrenci projelerinde Polling (Fetch+setInterval) basit ve hızlı bir çözümdür.
    """ # En sondan 50 mesajı gönderelim (Fazlası performansı düşürür).
    messages = Message.query.order_by(Message.timestamp.desc()).limit(50).all()
    
    # İstemci sırayla gösterebilmek için yeniden eskiye sıralamayı tersine çeviriyoruz
    messages_list = []
    for m in reversed(messages):
        messages_list.append({
            'id': m.id,
            'sender': m.sender.isim,
            'is_me': m.sender_id == current_user.id,
            'content': m.content,
            'timestamp': m.timestamp.strftime('%H:%M'),
            'cinsiyet': m.sender.cinsiyet,
            'profile_pic': m.sender.profile_pic,
            'file_url': m.file_url,
            'file_type': m.file_type,
            'original_file_name': m.original_file_name
        })
    return jsonify(messages_list)

@app.route('/api/messages', methods=['POST'])
@login_required
def send_message():
    content = request.form.get('content', '')
    file = request.files.get('file')
    
    file_url = None
    file_type = None
    original_file_name = None
    
    if file and file.filename != '':
        if allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            original_file_name = secure_filename(file.filename)
            unique_name = str(uuid.uuid4()) + '.' + ext
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'chat', unique_name))
            file_url = unique_name
            file_type = 'image' if ext in {'png', 'jpg', 'jpeg', 'gif'} else 'document'
            
    if content.strip() == '' and not file_url:
        return jsonify({'status': 'error', 'message': 'Boş mesaj gönderilemez.'}), 400
        
    new_msg = Message(
        content=content.strip(), 
        sender_id=current_user.id, 
        file_url=file_url, 
        file_type=file_type, 
        original_file_name=original_file_name
    )
    db.session.add(new_msg)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Mesaj gönderildi.'})

@app.route('/api/messages/<int:msg_id>', methods=['DELETE'])
@login_required
def delete_message(msg_id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Yetkisiz işlem'}), 403
    msg = Message.query.get(msg_id)
    if msg:
        db.session.delete(msg)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Mesaj bulunamadı'}), 404

# -- Ana akış fonksiyonu
if __name__ == '__main__':
    # debug=True: Kod değiştiğinde sunucu kendini yeniden başlatır. (SADECE GELİŞTİRME - DEV ORTAMINDA!)
    app.run(debug=True, port=5000)
