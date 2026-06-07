# Hausport Ürün Arama ve Scraper Sistemi

Bu proje, Akakçe ve Cimri gibi platformlar üzerinden ürünlerin linklerini otomatik olarak bulan bir web uygulamasıdır. Sistem, tekli arama ve Excel dosyası üzerinden toplu arama özelliklerine sahiptir.

## 🛠 Sistem Mimarisi

Sistem iki ana parçadan oluşur: **Backend (Python/FastAPI)** ve **Frontend (React/Vite)**.

---

### 📂 Backend (Arka Plan) Dosyaları

Backend klasörü, arama mantığını ve veri işleme süreçlerini yönetir.

1.  **`main.py`**: Sistemin ana kumanda merkezidir.
    *   **FastAPI Sunucusu**: API uç noktalarını (endpoints) tanımlar.
    *   **`/search`**: Tek bir ürün için anlık arama yapar.
    *   **`/upload`**: Excel dosyalarını kabul eder ve arka planda (`BackgroundTasks`) işleme sürecini başlatır.
    *   **`/status/{job_id}`**: Devam eden Excel işleme sürecinin ilerlemesini (yüzde kaç tamamlandı) takip eder.
    *   **`/download/{fileId}`**: İşlemi biten Excel dosyasının indirilmesini sağlar.

2.  **`scraper.py`**: Web kazıma (scraping) mantığının bulunduğu dosyadır.
    *   **Playwright**: Gerçek bir tarayıcı gibi davranarak Akakçe ve Cimri sitelerine girer.
    *   **Arama Stratejisi**: Ürün adı ve marka kombinasyonlarını kullanarak en doğru sonuçları bulmaya çalışır.
    *   **Hata Yönetimi**: Engellemelere karşı farklı "User-Agent"lar kullanır ve aramalara rastgele gecikmeler ekler.

3.  **`requirements.txt`**: Projenin çalışması için gerekli olan Python kütüphanelerini listeler (FastAPI, Playwright, Pandas, vb.).

4.  **`Dockerfile` & `build.sh`**: Projenin sunucuya (örneğin Render veya DigitalOcean) sorunsuz dağıtılmasını sağlayan yapılandırma dosyalarıdır.

---

### 🎨 Frontend (Arayüz) Dosyaları

Frontend klasörü, kullanıcının sistemle etkileşime girdiği görsel kısımdır.

1.  **`src/App.jsx`**: Uygulamanın tüm mantığını içeren ana React bileşenidir.
    *   **Kullanıcı Arayüzü**: Arama kutusu, dosya yükleme alanı ve ilerleme çubuğu burada tanımlanır.
    *   **API İletişimi**: Tarayıcıdan backend'e istek gönderir ve gelen verileri ekranda gösterir.
    *   **Durum Yönetimi (State)**: Arama sonuçlarını ve işlem durumlarını anlık olarak takip eder.

2.  **`src/index.css`**: Uygulamanın modern ve şık görünmesini sağlayan CSS tasarımlarını içerir.

3.  **`index.html`**: Uygulamanın tarayıcıdaki giriş kapısıdır.

4.  **`vite.config.js`**: Frontend'in hızlı çalışmasını ve derlenmesini sağlayan yapılandırma dosyasıdır.

---

## ⚙️ Sistemin Çalışma Mantığı

Uygulama, toplu işlemlerde "İki Aşamalı" bir strateji izler:

1.  **Veri Okuma**: Kullanıcı Excel yüklediğinde, sistem otomatik olarak "Ürün Adı" ve "Marka" sütunlarını tespit eder.
2.  **1. Aşama (Hızlı Arama)**: Tüm ürünler için orijinal isimleriyle hızlıca arama yapılır.
3.  **Yeniden Düzenleme**: Bulunamayan ürünler listenin en altına taşınır.
4.  **2. Aşama (Esnek Arama)**: Bulunamayan ürünler için daha "yumuşak" bir arama (lenient mode) yapılır. Bu aşamada kelime varyasyonları denenerek başarı oranı artırılır.
5.  **Sonuç**: Tamamlanan liste kullanıcıya indirilebilir bir Excel dosyası olarak sunulur.

---

## 🚀 Kurulum ve Çalıştırma (GitHub'dan İndirenler İçin)

Projeyi bilgisayarınıza indirip çalıştırmak için aşağıdaki adımları sırasıyla uygulayın.

### 1. Gereksinimler
Bilgisayarınızda şunların kurulu olduğundan emin olun:
- **Python** (3.8 veya üzeri)
- **Node.js** (v14 veya üzeri)
- **Git**

### 2. Projeyi İndirin
Terminal veya Komut Satırını açıp projeyi klonlayın ve klasöre girin:
```bash
git clone https://github.com/Ahmet003-cod/uruun_linki_bulma.git
cd uruun_linki_bulma
```

### 3. Kök Dizin Kurulumu
Projeyi aynı anda çalıştırmak için gerekli aracı (`concurrently`) kurun:
```bash
npm install
```

### 4. Backend (Arka Plan) Kurulumu
Python kütüphanelerini ve Playwright tarayıcısını kurun:
```bash
cd backend
pip install -r requirements.txt
# (Alternatif olarak tek satırda kurmak için:)
# pip install fastapi uvicorn pandas openpyxl httpx beautifulsoup4 playwright python-multipart python-dotenv thefuzz python-Levenshtein

playwright install chromium
cd ..
```

### 5. Frontend (Arayüz) Kurulumu
Arayüz için gerekli paketleri kurun:
```bash
cd frontend
npm install
cd ..
```

### 6. Uygulamayı Başlatma
Tüm kurulumlar tamamlandıktan sonra, projenin ana klasöründe (kök dizinde) şu komutu çalıştırarak hem arka planı hem de arayüzü aynı anda başlatabilirsiniz:

```bash
npm run start
```

Tarayıcınızda otomatik olarak (genellikle `http://localhost:3000`) açılacaktır. Eğer açılmazsa terminaldeki adresi tarayıcınıza yapıştırın.
