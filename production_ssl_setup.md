# راهنمای راه‌اندازی SSL و Nginx در Docker برای دامنه vestelle.ir

این مستند شامل تنظیمات کامل برای اجرای Nginx به همراه Let's Encrypt SSL در محیط Docker است، به طوری که با Cloudflare (حالت Full Strict) کاملاً سازگار باشد.

## معماری نهایی
1.  **Nginx Container**: مسئول مدیریت ترافیک HTTP/HTTPS و Proxy به Django.
2.  **Certbot Container**: مسئول دریافت و تمدید خودکار گواهینامه SSL.
3.  **Shared Volumes**: برای اشتراک‌گذاری فایل‌های گواهینامه بین دو کانتینر.
4.  **Dummy Cert Flow**: برای حل مشکل مرغ و تخم‌مرغ (Nginx برای شروع نیاز به فایل گواهینامه دارد، و Certbot برای دریافت گواهینامه نیاز دارد Nginx بالا باشد).

---

## ۱. فایل `docker-compose.yml` نهایی

این فایل شامل تمامی سرویس‌های مورد نیاز است. دقت کنید که کانتینر `certbot` به صورت خودکار هر ۱۲ ساعت یکبار چک می‌کند که آیا نیاز به تمدید هست یا خیر.

```yaml
services:
  # --- Django Application ---
  web:
    build:
      context: .
      dockerfile: ./compose/django/Dockerfile
    container_name: django_web
    command: /start.sh
    volumes:
      - static_files:/app/static
      - media_files:/app/media
    env_file:
      - .env
    environment:
      - DJANGO_SETTINGS_MODULE=ecommerce_api.settings.production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # --- Nginx Reverse Proxy ---
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

  # --- Certbot (Let's Encrypt) ---
  certbot:
    image: certbot/certbot:v2.10.0
    container_name: certbot
    volumes:
      - certbot_certs:/etc/letsencrypt
      - certbot_webroot:/var/www/certbot
    # بررسی برای تمدید هر ۱۲ ساعت
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    restart: unless-stopped

  # سایر سرویس‌ها (db, redis, celery) مشابه قبل در اینجا قرار می‌گیرند...
  db:
    image: postgres:15-alpine
    container_name: postgres_db
    # ... (تنظیمات قبلی)

  redis:
    image: redis:7-alpine
    container_name: redis_cache
    # ... (تنظیمات قبلی)

volumes:
  postgres_data:
  static_files:
  media_files:
  certbot_certs:
  certbot_webroot:
```

---

## ۲. تنظیمات Nginx

### فایل `compose/nginx/conf.d/http.conf.template`
این فایل مسئول مدیریت چالش Let's Encrypt و Redirect به HTTPS است.

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
        default_type "text/plain";
        try_files $uri =404;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```

### فایل `compose/nginx/conf.d/https.conf.template`
تنظیمات کامل SSL و امنیت.

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN};

    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # Proxy به Django
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ { alias /app/static/; }
    location /media/ { alias /app/media/; }
}
```

---

## ۳. مراحل اجرایی (گام به گام)

### گام ۱: تنظیم فایل `.env`
مطمئن شوید مقادیر زیر به درستی ست شده‌اند:
```env
DOMAIN=vestelle.ir
CERTBOT_EMAIL=your-email@example.com
```

### گام ۲: اجرای اسکریپت راه‌اندازی اولیه (Initial Setup)
برای اینکه برای اولین بار گواهینامه واقعی را دریافت کنید، دستور زیر را اجرا کنید (این دستور یک کانتینر موقت certbot برای دریافت گواهینامه اجرا می‌کند):

```bash
# ابتدا کانتینرها را بالا بیاورید (nginx با گواهینامه موقت/Dummy بالا می‌آید)
docker compose up -d nginx

# حالا درخواست گواهینامه واقعی از Let's Encrypt
docker compose run --rm certbot certonly --webroot -w /var/www/certbot \
    --email your-email@example.com \
    --agree-tos --no-eff-email \
    -d vestelle.ir
```

### گام ۳: ری‌لود کردن Nginx
بعد از اینکه گواهینامه با موفقیت دریافت شد، Nginx را ری‌لود کنید تا فایل‌های جدید را بخواند:
```bash
docker compose exec nginx_proxy nginx -s reload
```

---

## ۴. حل مشکل Cloudflare 521
بعد از انجام مراحل بالا:
1.  در پنل Cloudflare به بخش **SSL/TLS** بروید.
2.  مد را روی **Full (Strict)** قرار دهید.
3.  چون الان سرور شما دارای یک گواهینامه معتبر Let's Encrypt است، Cloudflare دیگر خطای ۵۲۱ نمی‌دهد.

## ۵. اسکریپت تمدید خودکار (Auto-Renewal)
در این معماری، تمدید به صورت زیر انجام می‌شود:
1.  کانتینر `certbot` هر ۱۲ ساعت دستور `certbot renew` را اجرا می‌کند.
2.  اگر گواهینامه‌ای تمدید شود، فایل‌های داخل Volume مشترک آپدیت می‌شوند.
3.  کانتینر `nginx` طبق Cron Job داخلی که در `entrypoint.sh` تعریف کردیم، هر روز ساعت ۴ صبح یکبار `reload` می‌شود تا فایل‌های جدید را لود کند.

---
**نکته امنیتی:** حتماً پورت‌های ۸۰ و ۴۴۳ روی فایروال سرور (مانند ufw) باز باشند.
