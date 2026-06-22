# Car Rental Backend API

TeklifimGelsin backend developer task icin Flask, PostgreSQL ve SQLAlchemy ile hazirlanmis basit arac kiralama REST API projesidir.

## Özellikler

- Kullanici kaydi ve Basic Auth ile giris
- `merchant` ve `user` rolleri
- Merchant icin arac ekleme, guncelleme ve silme
- Kullanici icin arac listeleme ve filtreleme
- Kullanici icin arac kiralama, kiralamayi uzatma, araci iade etme ve kiralama gecmisi
- Iade sirasinda gunluk fiyata gore toplam ucret hesaplama

## Kurulum

PostgreSQL'i Docker ile baslatin:

```bash
docker compose up -d
```

Python paketlerini kurun:

```bash
pip install -r requirements.txt
```

Uygulamayi calistirin:

```bash
python app.py
```

Varsayilan adres:

```text
http://127.0.0.1:5000
```

Not: Bu proje bir REST API'dir, web arayuzu yoktur. Bu nedenle tarayicida
`http://127.0.0.1:5000` adresi 404 donebilir. Test icin `/health`, `/cars`
ve diger API endpointleri kullanilmalidir.

`/register` ve `/login` endpointleri tarayicida adres cubugundan acilmaz,
cunku bu endpointler `POST` istegi bekler. Tarayici adres cubuguna yazildiginda
`GET` istegi gonderdigi icin `/login` icin 405 Method Not Allowed gorulebilir.
Bu endpointler Postman, curl veya benzeri bir API client ile test edilmelidir.

## Kurulum

1. Docker Desktop'i baslatin.

2. Proje klasorunde PostgreSQL servisini baslatin:

```bash
docker compose up -d
```

3. Python paketlerini kurun:

```bash
pip install -r requirements.txt
```

4. Flask uygulamasini baslatin:

```bash
python app.py
```

5. API'nin calistigini kontrol edin:

```bash
curl http://127.0.0.1:5000/health
```

Beklenen cevap:

```json
{"status":"ok"}
```

6. Postman ile test etmek icin `postman_collection.json` dosyasini import edin.
Collection icinde register, login, car management ve rental endpointleri icin
ornek istekler bulunur.

### Ornek Manuel Test Akisi

Merchant kullanicisi olusturun:

```bash
curl -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"merchant1\",\"password\":\"123456\",\"role\":\"merchant\"}"
```

Customer kullanicisi olusturun:

```bash
curl -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"user1\",\"password\":\"123456\",\"role\":\"user\"}"
```

Merchant olarak arac ekleyin:

```bash
curl -X POST http://127.0.0.1:5000/cars \
  -u merchant1:123456 \
  -H "Content-Type: application/json" \
  -d "{\"brand\":\"Toyota\",\"model\":\"Corolla\",\"year\":2022,\"color\":\"white\",\"daily_price\":750}"
```

Araclari listeleyin:

```bash
curl http://127.0.0.1:5000/cars
```

Customer olarak arac kiralayin:

```bash
curl -X POST http://127.0.0.1:5000/rentals \
  -u user1:123456 \
  -H "Content-Type: application/json" \
  -d "{\"car_id\":1,\"end_date\":\"2026-06-25T10:00:00Z\"}"
```

Kiralama gecmisini goruntuleyin:

```bash
curl -u user1:123456 http://127.0.0.1:5000/rentals/history
```

## Ortam Değişkeni

Varsayilan database URL:

```text
postgresql://root:rootpassword@localhost:5432/car_rental_db
```

Farkli bir database kullanmak icin:

```bash
set DATABASE_URL=postgresql://user:password@localhost:5432/db_name
```

## Endpointler

| Method | Endpoint | Auth | Aciklama |
| --- | --- | --- | --- |
| GET | `/health` | Yok | Uygulama saglik kontrolu |
| POST | `/register` | Yok | Kullanici olusturur |
| POST | `/login` | Basic Auth | Giris kontrolu yapar |
| GET | `/cars` | Yok | Araclari listeler ve filtreler |
| GET | `/cars/<id>` | Yok | Tek arac detayini getirir |
| POST | `/cars` | Merchant | Arac ekler |
| PATCH | `/cars/<id>` | Merchant | Kendi aracini gunceller |
| DELETE | `/cars/<id>` | Merchant | Kendi aracini siler |
| POST | `/rentals` | User | Arac kiralar |
| PATCH | `/rentals/<id>/extend` | User | Aktif kiralamayi uzatir |
| PATCH | `/rentals/<id>/return` | User | Araci iade eder ve ucreti hesaplar |
| GET | `/rentals/history` | User | Kullanici kiralama gecmisini getirir |

## Örnek Akış

Merchant kaydi:

```json
{
  "username": "merchant1",
  "password": "123456",
  "role": "merchant"
}
```

User kaydi:

```json
{
  "username": "user1",
  "password": "123456",
  "role": "user"
}
```

Arac ekleme:

```json
{
  "brand": "Toyota",
  "model": "Corolla",
  "year": 2022,
  "color": "white",
  "daily_price": 750
}
```

Kiralama:

```json
{
  "car_id": 1,
  "end_date": "2026-06-25T10:00:00Z"
}
```

## Postman

`postman_collection.json` dosyasini Postman'e import ederek tum endpointleri deneyebilirsiniz.
