# راهنمای جامع راه‌اندازی SSL و Nginx در Docker (ویژه دامنه vestelle.ir)

این مستند شامل تنظیمات نهایی و اصلاح شده برای اجرای Nginx به همراه Let's Encrypt SSL در محیط Docker است. این تنظیمات با Cloudflare (حالت Full Strict) و Django کاملاً سازگار شده‌اند.

---

## ۱. ویژگی‌های کلیدی این راهکار
- **حل مشکل مرغ و تخم‌مرغ**: فایل `entrypoint.sh` که در `Dockerfile` به عنوان `ENTRYPOINT` تعریف شده، به صورت خودکار گواهینامه موقت (Dummy) می‌سازد تا Nginx بدون خطا استارت شود. این گواهینامه در مسیر `/etc/letsencrypt/live/vestelle.ir/` قرار می‌گیرد.
- **تولید خودکار DHParam**: فایل امنیت اضافی `ssl-dhparams.pem` در اولین اجرا توسط اسکریپت ورودی ساخته می‌شود.
- **پشتیبانی از www**: هر دو حالت `vestelle.ir` و `www.vestelle.ir` در کانفیگ، گواهینامه و چالش Let's Encrypt لحاظ شده‌اند.
- **جایگزینی متغیرها (envsubst)**: متغیر `${DOMAIN}` به صورت خودکار در زمان استارت کانتینر در فایل‌های کانفیگ جایگزین می‌شود.
- **سازگاری با Cloudflare**: هدر `X-Forwarded-Proto` به صورت صریح روی `https` ست شده است.
- **تمدید خودکار**: کانتینر Certbot هر ۱۲ ساعت تمدید را چک می‌کند و یک Cron Job داخلی در کانتینر Nginx هر روز صبح آن را ری‌لود می‌کند.

---

## ۲. پیش‌نیازها در Django
برای اینکه Django پشت پروکسی Nginx و Cloudflare به درستی کار کند، خط زیر را حتماً در `settings/production.py` اضافه کنید:

```python
# ecommerce_api/settings/production.py

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

---

## ۳. تنظیمات Cloudflare (بسیار مهم)
در زمان راه‌اندازی اولیه (Initial Setup):
1.  به پنل Cloudflare بروید.
2.  بخش **DNS** را باز کنید.
3.  رکورد دامنه خود (`vestelle.ir`) و `www` را موقتاً از حالت **Proxied (ابر نارنجی)** به حالت **DNS Only (ابر خاکستری)** تغییر دهید.
4.  بعد از دریافت موفقیت‌آمیز گواهینامه، می‌توانید دوباره آن‌ها را به حالت نارنجی برگردانید و SSL را روی **Full (Strict)** قرار دهید.

---

## ۴. فایل `docker-compose.yml` نهایی

```yaml
services:
  # --- Nginx Proxy ---
  nginx:
    build:
      context: .
      dockerfile: ./compose/nginx/Dockerfile
    container_name: nginx_proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - static_files:/app/static
      - media_files:/app/media
      - certbot_certs:/etc/letsencrypt
      - certbot_webroot:/var/www/certbot
    environment:
      - DOMAIN=${DOMAIN}
      - EMAIL=${CERTBOT_EMAIL}
    depends_on:
      - web
    restart: unless-stopped

  # --- Certbot ---
  certbot:
    image: certbot/certbot:v2.10.0
    container_name: certbot
    volumes:
      - certbot_certs:/etc/letsencrypt
      - certbot_webroot:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    restart: unless-stopped
```

---

## ۵. مراحل راه‌اندازی (Step-by-Step)

### گام ۱: آماده‌سازی
مطمئن شوید فایل `.env` حاوی مقادیر درست است:
```env
DOMAIN=vestelle.ir
CERTBOT_EMAIL=info@vestelle.ir
```

### گام ۲: اجرای سرویس‌ها
```bash
docker compose up -d --build
```
*در این مرحله Nginx با گواهینامه Dummy بالا می‌آید. می‌توانید با دستور `docker compose logs -f nginx` روند ساخت گواهینامه موقت و DHParam را ببینید.*

### گام ۳: دریافت گواهینامه واقعی
(قبل از این کار مطمئن شوید ابر Cloudflare خاکستری است)
```bash
docker compose run --rm certbot certonly --webroot -w /var/www/certbot \
    --email info@vestelle.ir \
    --agree-tos --no-eff-email \
    -d vestelle.ir -d www.vestelle.ir
```

### گام ۴: تایید و اعمال گواهینامه
```bash
# ری‌لود کردن Nginx برای خواندن گواهینامه جدید
docker compose exec nginx_proxy nginx -s reload

# تست محلی HTTPS (باید خروجی 200 OK بدهد)
docker compose exec nginx_proxy curl -Ik https://localhost
```

### گام ۵: فعال‌سازی نهایی Cloudflare
1.  ابرها را در پنل Cloudflare دوباره **نارنجی** کنید.
2.  بخش SSL/TLS را روی **Full (Strict)** قرار دهید.
