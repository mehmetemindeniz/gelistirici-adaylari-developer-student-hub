# Geliştirici Adayları Platformu - Proje Teknik Raporu (Project Summary)

Bu belge, "Geliştirici Adayları" projesinin başlangıçtan bugüne kadarki geliştirme sürecini, mimarisini, veritabanı yapısını, rotaj (routing) sistemini ve frontend detaylarını özetler. Deployment (PythonAnywhere) aşamasında Gemini AI'a teknik bağlam sunması için dikkatlice hazırlanmıştır.

## 1. Proje Genel Özeti
Geliştirici Adayları platformu, yazılım ve teknoloji bölümü öğrencilerinin (ve tutkunlarının) iletişimde kalmasını sağlamak amacıyla geliştirilmiş, **Flask (Python)** ve **TailwindCSS** tabanlı dinamik bir sosyal platformdur. İçerisinde canlı akış (Facebook/Twitter benzeri yapı), döküman (e-kitap, sınav notu) depolaması ve anlık iletişim sağlayan bir **Global Sohbet (Topluluk Sohbeti)** barındırır. 

---

## 2. Kullanılan Teknolojiler & Bağımlılıklar
- **Backend:** Python 3, Flask
- **Veritabanı:** SQLAlchemy ORM, SQLite (`app.db`)
- **Oturum Yönetimi & Güvenlik:** Flask-Login, Werkzeug Security (Şifre Hash'leme ve Dosya Yükleme Güvenliği)
- **Frontend / Arayüz:** Vanilla HTML5, Tailwind CSS (CDN kullanılarak Apple / Notion tarzı karanlık modern tema)
- **Asenkron İletişim:** JavaScript `fetch()` API'si (Sohbet sistemi için setInterval tabanlı long-polling alternatifi).

---

## 3. Veritabanı Şeması (`models.py`)

Kullanılan tablolar SQLAlchemy kalıtımlarıyla inşa edilmiştir:

1. **User (Kullanıcı Tablosu):** Platformun kalbinde yer alır. Oturum açmak için `flask_login.UserMixin` miras alınır. 
   - `id`, `username`, `isim`, `soyisim`, `email`, `telefon`, `bolum`, `sinif`, `cinsiyet`, `password_hash`, `profile_pic`.
   - **Kritik Flag'ler:** `is_approved` (Admin hesabını onaylamadan giriş yapılamaz), `is_admin` (Sistem içi yetki).
2. **Post (Akış Gönderileri):** 
   - `id`, `user_id` (Yazar), `content` (Metin), `image_url` (Opsiyonel Resim), `link` (Opsiyonel URL), `created_at`.
3. **Comment (Yorumlar):** `post_id` ve `user_id` foregn key bağlantıları sayesinde posts tablosunun altında "one-to-many" ilişkisi kurar.
4. **PostLike & DocumentLike (Beğeni / Dislike):** 
   - Gönderi ve dökümanlar için çoktan çoğa ilişki tutan junction tablolar. Kullanıcının bir postu/dökümanı beğenip (`is_like=True`) veya beğenmediğini (`is_like=False`) belirtir.
5. **Document (Dökümanlar):** 
   - `category` (Vize, Sınav, Not vb.), `title`, `file_url`, `uploader_id`, `original_file_name`. 
6. **Message (Sohbet Sistemi):**
   - Topluluğun anlık sohbetindeki mesaj dökümü. `sender_id`, `content`, `timestamp`. Opsiyonel olarak `file_url` ve `file_type` ('image' veya 'document') barındırır.

---

## 4. Uygulama Mantığı ve Rotalar (`app.py`)

- **Kayıt ve Yönetim Akışı:** 
  - `/register`: Kullanıcı cinsel kimliği de dahil tüm zorunlu inputları doldurup kayıt olur. Gönderdiği şifre anında `generate_password_hash()` yardımıyla veri tabanına yazılır. `is_approved` default değere (`False`) sabitlenir.
  - `/login`: Form `check_password_hash` ile denetlenir. Eğer giriş doğruysa, kullanıcının `is_approved` bayrağı taratılır. Bayrak `False` ise, kullanıcı `/pending` rotasına (Bekleme Sayfası) atılır, içeri alınmaz.
  
- **Admin Mekanizması (`/admin`):** 
  - Sistemin tam korunaklı kalesidir (`current_user.is_admin == True` kuralıyla izole edilmiştir). Admin hesabı; kayıt bekleyenleri listeler, `.is_approved = True` yapar, sakıncalı hesapları veritabanından silebilir ve unutulmuş şifreleri tek tuş prompt() uyarısıyla (`reset_password` methodu ile) arka plandan değiştirebilir.
  
- **Gönderiler, Beğeniler ve Belge Depolama (`/`, `/documents`):** 
  - Admin/Kullanıcı yetkisine bakılmaksızın tüm onaylı kullanıcılar kullanabilir.
  - POST metodlarında dosya ismi Werkzeug'in `secure_filename()` ve `uuid.uuid4().hex` kombinasyonuyla güvenlik çemberine alınır, ardından `static/uploads/` (profil, chat, posts rotalarına dağıtılmış klasörlere) depolanır.
  - **Güvenlik Çözümü:** DDoS ataklarından kaçınmak adına `app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024` limitasyonu ile "max 16 MB yükleme" sınırı backend düzeyinde etkinleştirilmiştir.
  - Kullanıcılar admin olmasalar dahi kendi döküman/gönderilerini `delete_post` ve `delete_document` rotalarında kendi (Current ID == Uploader ID) yetkileri çerçevesinde silebilir.
  
- **Chat API Sistemi (`/api/messages`, `/api/send_message`):** 
  - Sayfa yenilenmesine ihtiyaç kalmadan backend ile JSON formatında haberleşen rotalardır. Kullanıcılar metin veya fotoğraf, PDF vb. dosyaları doğrudan `formData` ile bu backend rotalarına paslarlar.

---

## 5. UI Tasarımı & Frontend Şablonları (Templates)

- **`base.html`:** Sayfaların tüm temel yapısını taşır. "Responsive" (Her cihaza ölçeklenen) bir üst navbar barındırır. Telif hakkı ve mobil menü geçişleri bu baz dosyada kontrol edilir.
- **`chat.html` (WhatsApp/Telegram Benzeri Responsive Mimari):** 
  - Tasarımın en zor bölümlerinden biridir. Mobil cihazlardaki URL barlarının yükseklik farklılıklarını (height jitter) ve scroll problemini aşmak amacıyla ana `<body>` yapısında tam ekran CSS flex box mantığı (100dvh ve absolute pozisyonlama vb.) kullanıldı.
  - Scroll, mesaj gönderildiğinde algoritmik olarak JS yardımı ile en alta anında konumlanır; yukarıdaki eski mesajlar okunurken ise asla sekmeyi kapatacak ani sıçrama (jump) yapmaz. 
  - Fotoğrafı olmayan kullanıcılara Cinsiyet modeline göre farklı SVG profil simgeleri atanır. Başlık metni kaldırılarak profesyonel dairesel animasyonlu logo yapılandırılmıştır.
- **`index.html` ve `documents.html`:** İçerikler kart blokları halinde responsive Grid sisteminden (1-2-3 sütunlu esnek mimari) çekilir. Yorum alanları accordion mekanizmasıyla JS marifetiyle açılıp kapanır, UI hiyerarşisi koyu lacivert ve cam izi (backdrop-blur) şeffaflık tonlarıyla tasarlanmıştır.

---

## 6. Deployment (PythonAnywhere) İçin Gemini'a Tavsiyeler & Check-list

Sevgili Gemini; projeyi production (canlı sunucu) ortamına aktarırken şunlara dikkat edilmesi plananlanmaktadır:
1. **Veritabanı Threading:** Şu an projede SQLite kullanıyoruz. Chat rotası (`fetchMessages`) 3 saniyede bir polling (sorgu) işlemi göndermektedir. SQLAlchemy yapılandırmasında WSGI/Gunicorn Worker sınırları zorlanırsa "database locked" uyarısı için timeout threshold'lar eklenebilir veya PostgreSQL gibi async/ölçeklenebilir bir DBMS'e geçişi önerilebilir.
2. **Statik Dosyalar (Whitenoise):** Normalde Geliştirici Adayları projesi `static/` klasöründen sunuyor ancak PythonAnywhere ortamında statik yolların WSGI configuration panelinden "Web sekmesinden" mapping (`/static/ -> /home/username/mysite/static`) yapılması zorunludur.
3. **Zaman Dilimi:** Postların, mesajların saatleri sistem saatiyle alınıyor, bu yüzden PythonAnywhere sunucularında default UTC alındığı için saat ayarlamasında (`TZ='Europe/Istanbul'`) kaymalar engellenebilir. 

Tüm core fonksiyonlar (Kayıt, Onay, Akış, Profil resmi, Canlı Chat ve Rota izinleri) kusursuz olarak implemente edilmiştir. Yayına almaya hazırdır!
