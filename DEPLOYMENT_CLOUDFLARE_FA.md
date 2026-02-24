# راهنمای استقرار و پیکربندی SSL (Cloudflare & Certbot)

این راهنما برای راه‌اندازی بخش Production پروژه Hypex و رفع مشکلات متداول در تنظیمات SSL و Cloudflare تهیه شده است.

## ۱. تنظیمات Cloudflare

برای اینکه گواهی Let's Encrypt به درستی صادر شود و امنیت سایت برقرار باشد، مراحل زیر را دنبال کنید:

1.  **رکورد‌های DNS:**
    *   ابتدا رکورد‌های `A` (مثلاً برای `api.yourdomain.com`) را در پنل Cloudflare اضافه کنید.
    *   **مهم:** در اولین بار که می‌خواهید گواهی SSL بگیرید، وضعیت Proxy را روی **"DNS Only"** (ابر خاکستری) قرار دهید. این کار اجازه می‌دهد چالش‌های ACME مستقیماً به سرور شما برسند.
2.  **تنظیمات SSL/TLS:**
    *   پس از دریافت موفقیت‌آمیز گواهی، وضعیت Proxy را می‌توانید به **"Proxied"** (ابر نارنجی) تغییر دهید.
    *   در بخش SSL/TLS، حالت را روی **"Full (Strict)"** قرار دهید. این حالت تضمین می‌کند که ارتباط بین Cloudflare و سرور شما نیز با گواهی معتبر رمزنگاری شده است.

## ۲. مراحل استقرار اولیه (Docker)

۱. فایل `.env` را از روی نمونه بسازید:
```bash
cp .env.example .env
```
۲. متغیرهای حیاتی را مقداردهی کنید:
*   `DOMAIN`: دامنه دقیق خود را وارد کنید (بدون http/https).
*   `CERTBOT_EMAIL`: ایمیل خود را برای اعلان‌های انقضا وارد کنید.
*   `CERTBOT_ENABLED`: روی `true` تنظیم شود.
*   `SMS_IR_OTP_TEMPLATE_ID`: حتماً یک عدد معتبر باشد (خالی نگذارید).

۳. سرویس‌ها را بالا بیاورید:
```bash
sudo docker compose up --build -d
```

## ۳. عیب‌یابی: مشکل عدم هم‌خوانی مسیر گواهی (SSL Path Mismatch)

در برخی موارد، ممکن است Nginx همچنان گواهی موقت (Dummy) سرو کند یا با خطای پیدا نشدن گواهی مواجه شود، در حالی که Certbot گواهی را دریافت کرده است.

### مشکل: پسوند `-0001` در نام پوشه
اگر قبلاً تلاشی برای دریافت گواهی انجام شده باشد یا پوشه‌ای با نام دامنه در مسیر `/etc/letsencrypt/live/` وجود داشته باشد، Certbot گواهی جدید را در پوشه‌ای با پسوند عددی می‌سازد (مثلاً `yourdomain.ir-0001`). اما Nginx طبق تنظیمات به دنبال پوشه بدون پسوند می‌گردد.

### علائم:
*   سایت بالا می‌آید اما مرورگر خطای امنیتی می‌دهد.
*   مشاهده Issuer گواهی نشان می‌دهد که همچنان از نوع Self-signed یا Dummy است.
*   در لاگ‌های Nginx خطای عدم دسترسی به `fullchain.pem` دیده می‌شود.

### راه‌حل سریع (Symlink):
بهترین راه برای حل این مشکل بدون تغییر در کدهای اصلی پروژه، ایجاد یک لینک نمادین (Symlink) است:

۱. وارد کانتینر Nginx شوید یا از طریق Volumeهای مشترک روی میزبان اقدام کنید:
```bash
# رفتن به مسیر گواهی‌ها (روی هاست اگر Volume دارید)
cd /var/lib/docker/volumes/django-ecommerce-api_certbot_certs/_data/live/

# ایجاد لینک برای هدایت مسیر اصلی به نسخه جدید
ln -s yourdomain.ir-0001 yourdomain.ir
```

۲. بازنشانی Nginx:
```bash
sudo docker compose exec nginx nginx -s reload
```

۳. بررسی نهایی:
با استفاده از دستور زیر مطمئن شوید که Issuer گواهی به **Let's Encrypt** تغییر یافته است:
```bash
openssl s_client -connect yourdomain.ir:443 | grep "issuer"
```

## ۴. دستورات مفید

*   **ساخت Superuser:**
    به دلیل استفاده از مدل کاربر سفارشی، فیلدهای خاصی اجباری هستند:
    ```bash
    sudo docker compose exec web python manage.py createsuperuser --phone_number 09123456789 --username admin --first_name Name --last_name Family
    ```
*   **مشاهده لاگ‌ها:**
    ```bash
    sudo docker compose logs -f nginx
    sudo docker compose logs -f web
    ```
