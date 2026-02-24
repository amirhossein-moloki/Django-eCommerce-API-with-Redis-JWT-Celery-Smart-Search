# راهنمای دیپلوی و تنظیمات SSL با Cloudflare

این راهنما مراحل لازم برای راه‌اندازی گواهینامه SSL در اولین دیپلوی پروژه را توضیح می‌دهد.

## ۱. تنظیمات Cloudflare

قبل از شروع، در پنل Cloudflare:

1.  **DNS Records:** رکوردهای A برای دامنه اصلی (`@`) و `www` ایجاد کنید که به IP سرور اشاره کنند.
2.  **Proxy Status:** در ابتدا، وضعیت ابر (Proxy) را برای هر دو رکورد روی **DNS Only (خاکستری)** قرار دهید. این کار برای تایید مالکیت دامنه توسط Let's Encrypt ضروری است.
3.  **SSL/TLS Mode:** بعد از اتمام مراحل، این بخش را روی **Full (Strict)** قرار دهید.

## ۲. مراحل اجرا روی سرور

### گام ۱: اجرای اولیه سرویس‌ها
با این دستور، Nginx با یک گواهینامه موقت (Dummy) بالا می‌آید تا از خطای اولیه جلوگیری شود:
```bash
docker compose up -d --build
```

### گام ۲: دریافت گواهینامه واقعی
دستور زیر را با جایگزینی ایمیل و دامنه خود اجرا کنید:
```bash
docker compose run --rm certbot certonly --webroot -w /var/www/certbot \
    --email info@yourdomain.com \
    --agree-tos --no-eff-email \
    -d yourdomain.com -d www.yourdomain.com
```

### گام ۳: اعمال گواهینامه
پس از دریافت موفقیت‌آمیز، Nginx را ری‌لود کنید:
```bash
docker compose exec nginx_proxy nginx -s reload
```

## ۳. نهایی‌سازی در Cloudflare

پس از اطمینان از صحت کارکرد HTTPS:
1.  وضعیت ابرها را در Cloudflare به **Proxied (نارنجی)** تغییر دهید.
2.  مطمئن شوید حالت SSL روی **Full (Strict)** است.

---
*نکته: سیستم به صورت خودکار هر ۱۲ ساعت تمدید گواهینامه را بررسی می‌کند.*
