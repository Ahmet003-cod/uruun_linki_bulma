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

## 🚀 Çalıştırma

Projenin kök dizininde aşağıdaki komutu kullanarak hem backend'i hem de frontend'i aynı anda başlatabilirsiniz:

```bash
npm start
```
