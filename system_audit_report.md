# ممیزی فنی جامع سیستم فروشگاهی

این گزارش یک تحلیل عمیق از پایگاه کد پروژه ارائه می‌دهد و حوزه‌های کلیدی مانند معماری سیستم، صحت منطق دامنه، امنیت، پایداری داده، عملکرد و قابلیت اطمینان را پوشش می‌دهد.

---

## الف) خلاصه اجرایی (Executive Summary)

**وضعیت کلی سیستم: نیازمند اصلاحات حیاتی**

معماری سیستم بر پایه اصول مدرن و ابزارهای قابل اعتمادی مانند Django، Celery و Redis بنا شده است. با این حال، چندین نقص حیاتی در منطق اصلی کسب‌وکار (Domain Logic) شناسایی شده که ریسک‌های جدی مالی و مربوط به یکپارچگی داده را به همراه دارد. زیرساخت فنی قوی است، اما پیاده‌سازی فعلی نیازمند اصلاحات فوری برای تبدیل شدن به یک سیستم قابل اتکا است.

**۳ ریسک حیاتی اول:**

1.  **ریسک مالی/داده (P0):** عدم ذخیره قیمت نهایی (`snapshotting`) در آیتم‌های سفارش، منجر به محاسبه نادرست سوابق مالی با هر بار تغییر قیمت محصول می‌شود.
2.  **ریسک مالی/تجربه کاربری (P0):** وجود منطق کاهش موجودی تکراری پس از پرداخت، باعث رد شدن سفارش‌های پرداخت‌شده در شرایط رقابتی (Race Condition) و از دست رفتن پول مشتری (بدون بازگشت وجه خودکار) می‌گردد.
3.  **ریسک یکپارچگی داده (P1):** فرآیند فعلی، داده‌های تاریخی سفارش‌ها را غیرقابل اتکا می‌سازد و تحلیل سود، مدیریت بازگشت کالا و گزارش‌گیری را مختل می‌کند.

**۳ پیشنهاد فوری:**

1.  **اصلاح مدل `OrderItem`:** یک فیلد `price` به این مدل اضافه شود تا قیمت واحد محصول در لحظه خرید به صورت ثابت در آن ذخیره گردد.
2.  **حذف منطق تکراری موجودی:** منطق بررسی و کاهش موجودی از فرآیند تأیید پرداخت (`verify_payment`) به طور کامل حذف شود، زیرا این کار قبلاً به درستی در زمان ایجاد سفارش انجام شده است.
3.  **افزودن تست یکپارچه:** یک تست کامل برای سناریوی خرید (از سبد تا پرداخت) نوشته شود تا از بازگشت این مشکلات جلوگیری کند.

---

## ب) نقشه سیستم (System Map)

### Tech Stack & Entry Points

*   **فریم‌ورک:** Django
*   **ORM/DB Driver:** Django ORM / psycopg2 (از طریق `django.contrib.postgres`)
*   **صف (Queue):** Celery (با Broker نامشخص، احتمالاً Redis یا RabbitMQ)
*   **کش (Cache):** Redis (`django_redis`)
*   **Payment SDK:** یک کلاس `ZibalGateway` به صورت داخلی پیاده‌سازی شده است (`payment/gateways.py`).
*   **Shipping SDK:** یک کلاس `PostexGateway` به صورت داخلی پیاده‌سازی شده است (`shipping/gateways.py`).

**نقطه ورود درخواست‌ها (Routes):**

*   `ecommerce_api/urls.py` نقطه ورود اصلی است.
*   `/api/v1/`: پیشوند اصلی برای APIهای کسب‌وکار که شامل URLهای ماژول‌های زیر است:
    *   `shop.urls`
    *   `orders.urls`
    *   `cart.urls`
    *   `coupons.urls`
    *   `chat.urls`
*   `/auth/`: مسیرهای احراز هویت و مدیریت کاربر (`account.urls`).
*   `/payment/`: مسیرهای پردازش و تأیید پرداخت (`payment.urls`).
*   `/shipping/`: مسیرهای مربوط به ارسال (`shipping.urls`).
*   `/admin/`: پنل ادمین جنگو.

**Middlewares کلیدی:**

*   `django_prometheus.middleware.*`: برای جمع‌آوری متریک‌ها.
*   `corsheaders.middleware.CorsMiddleware`: مدیریت CORS.
*   `cart.middleware.CartSessionMiddleware`: مدیریت سبد خرید در سشن کاربر.
*   `django.contrib.auth.middleware.AuthenticationMiddleware`: مدیریت احراز هویت.

### Domain Modules شناسایی‌شده

*   **محصولات/واریانت/SKU:**
    *   **مسیر:** `shop/`
    *   **فایل‌های کلیدی:** `models.py` (مدل `Product`), `serializers.py`, `views.py` (کلاس `ProductViewSet`).
*   **موجودی/انبار:**
    *   **مسیر:** `shop/`
    *   **منطق کلیدی:** فیلد `stock` در مدل `shop.Product`. منطق اصلی کاهش موجودی در `orders.serializers.OrderCreateSerializer` قرار دارد.
*   **سبد خرید:**
    *   **مسیر:** `cart/`
    *   **فایل‌های کلیدی:** `cart.py` (کلاس `Cart` برای مدیریت منطق سبد)، `views.py` (کلاس `CartViewSet`).
*   **سفارش‌ها:**
    *   **مسیر:** `orders/`
    *   **فایل‌های کلیدی:** `models.py` (مدل‌های `Order`, `OrderItem`), `serializers.py` (کلاس `OrderCreateSerializer` با منطق اصلی ساخت سفارش), `views.py` (کلاس `OrderViewSet`).
*   **پرداخت:**
    *   **مسیر:** `payment/`
    *   **فایل‌های کلیدی:** `views.py` (کلاس `PaymentWebhookAPIView`), `services.py` (توابع `process_payment`, `verify_payment`), `gateways.py` (کلاس `ZibalGateway`).
*   **ارسال:**
    *   **مسیر:** `shipping/`
    *   **فایل‌های کلیدی:** `services.py` (تابع `create_shipment`), `gateways.py` (کلاس `PostexGateway`).
*   **تخفیف/کوپن:**
    *   **مسیر:** `coupons/`
    *   **فایل‌های کلیدی:** `models.py` (مدل `Coupon`), `views.py` (کلاس `CouponViewSet`).
*   **مرجوعی/ریفاند:**
    *   **وضعیت:** NOT FOUND IN CODE. هیچ منطقی برای مدیریت بازگشت کالا یا بازگشت وجه در کد مشاهده نشد.
*   **کیف پول/اعتبار:**
    *   **وضعیت:** NOT FOUND IN CODE.

---

## ج) ممیزی صحت دامنه (Domain Correctness Audit)

### Pricing

*   **منبع قیمت و جلوگیری از دستکاری:** **OK**
    *   **دلیل:** قیمت محصول از مدل `Product` خوانده می‌شود. در `orders.serializers.OrderCreateSerializer`، قیمت آیتم موجود در سبد خرید (`item['price']`) به صراحت با قیمت محصول در پایگاه داده (`product.price`) در لحظه خرید مقایسه می‌شود و در صورت عدم تطابق، تراکنش متوقف می‌گردد.
*   **محاسبه تخفیف‌ها و گرد کردن:** **OK**
    *   **دلیل:** منطق محاسبه تخفیف در متدهای مدل `Order` (`get_discount`) و همچنین در مدل `Cart` پیاده‌سازی شده و از `Decimal` برای محاسبات مالی استفاده شده که از خطاهای ممیز شناور جلوگیری می‌کند.
*   **مالیات/ارسال:** **PARTIAL**
    *   **دلیل:** مقادیر مالیات و هزینه ارسال به صورت ثابت (`hardcoded`) در `orders.serializers.OrderCreateSerializer` تنظیم شده‌اند (`Decimal('15.00')` و `Decimal('0.09')`). این مقادیر باید از یک سرویس یا تنظیمات داینامیک خوانده شوند.

### Inventory & Oversell Prevention

*   **قفل/رزرو موجودی:** **OK**
    *   **دلیل:** در `orders.serializers.OrderCreateSerializer`، از `transaction.atomic()` به همراه `Product.objects.select_for_update()` برای قفل کردن ردیف‌های محصول در پایگاه داده قبل از کاهش موجودی استفاده شده است. این روش یک پیاده‌سازی صحیح برای جلوگیری از فروش مازاد است.
*   **رفتار در رقابت همزمان:** **BROKEN**
    *   **دلیل:** منطق کاهش موجودی به اشتباه **دو بار** پیاده‌سازی شده است: یک بار به درستی در `OrderCreateSerializer` و بار دوم به اشتباه در `payment.services.verify_payment`. این موضوع منجر به یک شرایط رقابتی (Race Condition) خطرناک می‌شود که در بخش "یافته‌ها" به تفصیل توضیح داده شده است.
*   **Rollback در خطای پرداخت:** **BROKEN**
    *   **دلیل:** اگر پرداخت موفق باشد اما در تابع `verify_payment` به دلیل کمبود موجودی (ناشی از شرایط رقابتی) خطا رخ دهد، وضعیت سفارش `FAILED` می‌شود اما هیچ منطقی برای بازگشت وجه (Refund) به مشتری وجود ندارد.
*   **سیاست Stock Reservation Expiry:** **NOT FOUND IN CODE**
    *   **دلیل:** موجودی تنها پس از ایجاد سفارش کم می‌شود. هیچ سیستمی برای رزرو موقت موجودی (مثلاً برای ۱۵ دقیقه) و آزادسازی آن در صورت عدم پرداخت وجود ندارد. سفارش‌های پرداخت‌نشده (`pending`) موجودی را کاهش نمی‌دهند.

### Cart → Order Integrity

*   **تبدیل سبد به سفارش (Snapshotting):** **BROKEN**
    *   **دلیل:** مدل `orders.models.OrderItem` قیمت محصول را در خود ذخیره نمی‌کند. متد `price` آن، قیمت را به صورت پویا از مدل `Product` می‌خواند. این باعث می‌شود سوابق سفارش‌های قدیمی با تغییر قیمت محصول، تغییر کنند.
*   **جلوگیری از Stale Cart:** **OK**
    *   **دلیل:** قیمت و موجودی محصولات در لحظه نهایی شدن خرید در `OrderCreateSerializer` مجدداً اعتبارسنجی می‌شوند.
*   **Validation نهایی قبل از ساخت Order:** **OK**
    *   **دلیل:** `OrderCreateSerializer` اعتبارسنجی‌های لازم برای آدرس، کوپن، و موجودی را قبل از ایجاد آبجکت `Order` انجام می‌دهد.

### Order State Machine

*   **State های رسمی و انتقال‌های مجاز:** **PARTIAL**
    *   **دلیل:** وضعیت‌های سفارش و پرداخت در مدل `Order` به خوبی با `TextChoices` تعریف شده‌اند (`Status` و `PaymentStatus`). اما هیچ مکانیزم صریحی (مانند یک کتابخانه State Machine) برای کنترل انتقال‌های مجاز بین وضعیت‌ها وجود ندارد. برای مثال، یک سفارش `DELIVERED` می‌تواند مستقیماً به `PAID` تغییر وضعیت دهد.
*   **Audit Trail تغییر وضعیت:** **PARTIAL**
    *   **دلیل:** کتابخانه `django-simple-history` در پروژه نصب شده است اما به نظر نمی‌رسد روی مدل `Order` فعال شده باشد. این کتابخانه می‌توانست تاریخچه تغییرات هر سفارش را ثبت کند.
*   **Idempotency روی عملیات‌های حساس:** **PARTIAL**
    *   **دلیل:** در `payment.services.process_payment`، چک می‌شود که سفارش قبلاً پرداخت نشده باشد. اما عملیات‌های دیگر مانند `cancel` یا `ship` فاقد چنین بررسی‌هایی برای جلوگیری از اجرای تکراری هستند.

### Payment Integration

*   **وجود Webhook Handler و اعتبارسنجی:** **OK**
    *   **دلیل:** در `payment.views.PaymentWebhookAPIView`، وب‌هوک ورودی با استفاده از `hmac.compare_digest` و لیست سفید IP اعتبارسنجی می‌شود که یک پیاده‌سازی امن و صحیح است.
*   **جلوگیری از پرداخت تکراری:** **OK**
    *   **دلیل:** قبل از ایجاد درخواست پرداخت، چک می‌شود که وضعیت پرداخت سفارش `SUCCESS` نباشد.
*   **Mapping دقیق Payment Status → Order Status:** **OK**
    *   **دلیل:** پس از تأیید پرداخت موفق در `verify_payment`، وضعیت `payment_status` به `SUCCESS` و وضعیت `status` سفارش به `PAID` تغییر می‌کند.
*   **Handling تایم‌اوت/Partial Failure:** **NOT FOUND IN CODE**
    *   **دلیل:** هیچ منطقی برای مدیریت سناریوهایی که وب‌هوک از درگاه پرداخت هرگز دریافت نمی‌شود یا خطایی در حین پردازش آن رخ می‌دهد، وجود ندارد. (مثلاً یک صف `retry` یا یک `dead-letter queue`).
*   **Refund کامل/جزئی:** **NOT FOUND IN CODE**
    *   **دلیل:** هیچ API یا منطقی برای بازگشت وجه در کد مشاهده نشد.

---

## د) ممیزی امنیتی (P0 محور)

### AuthN/AuthZ

*   **روش احراز هویت:** **OK**
    *   **شرح:** سیستم از `rest_framework_simplejwt` برای احراز هویت مبتنی بر توکن JWT استفاده می‌کند. `djoser` نیز برای مدیریت اندپوینت‌های ثبت‌نام، فعال‌سازی و بازیابی رمز عبور به کار رفته است. این یک روش استاندارد و امن است.
*   **کنترل دسترسی روی منابع:** **OK**
    *   **شرح:** از `Permission`های جنگو رست (`IsAuthenticated`, `IsAdminUser`) و یک permission سفارشی (`IsAdminOrOwner` در `orders/permissions.py`) برای کنترل دسترسی به منابع استفاده شده است.
*   **IDOR Check:** **OK**
    *   **شرح:** در `orders.services.get_user_orders`، کوئری سفارش‌ها به درستی فیلتر می‌شود تا هر کاربر عادی (`is_staff=False`) فقط به سفارش‌های خودش دسترسی داشته باشد (`Order.objects.filter(user=user)`). این از آسیب‌پذیری IDOR جلوگیری می‌کند.

### Input Validation

*   **Schema Validation:** **OK**
    *   **شرح:** `Django REST Framework Serializers` (مانند `OrderCreateSerializer`) به طور گسترده برای اعتبارسنجی داده‌های ورودی استفاده شده‌اند. این سریالایزرها به طور خودکار اعتبارسنجی نوع داده و الزامی بودن فیلدها را انجام می‌دهند.
*   **File Upload Validation:** **NOT DETERMINABLE FROM CODE**
    *   **شرح:** در کد بررسی‌شده، هیچ بخشی که مربوط به آپلود فایل توسط کاربر باشد، مشاهده نشد.
*   **منع Mass Assignment:** **OK**
    *   **شرح:** با استفاده از سریالایزرها و تعریف صریح فیلدها (`fields = (...)`)، تنها فیلدهایی که مجاز به تغییر توسط کاربر هستند، در دسترس قرار می‌گیرند و از آسیب‌پذیری Mass Assignment جلوگیری می‌شود.

### Injection & SSRF

*   **SQL/NoSQL Injection:** **OK**
    *   **شرح:** تمام کوئری‌های پایگاه داده از طریق Django ORM اجرا می‌شوند که به طور خودکار از پارامترها برای جلوگیری از SQL Injection استفاده می‌کند. هیچ کوئری خامی (`raw query`) مشاهده نشد.
*   **SSRF (Server-Side Request Forgery):** **NOT FOUND IN CODE**
    *   **شرح:** هیچ بخشی از کد وجود نداشت که یک URL را از ورودی کاربر دریافت کرده و به آن درخواست HTTP ارسال کند.
*   **Command Injection:** **NOT FOUND IN CODE**
    *   **شرح:** هیچ استفاده‌ای از `os.system` یا `subprocess` با ورودی کاربر مشاهده نشد.

### Secrets & Crypto

*   **نگهداری Secrets:** **OK**
    *   **شرح:** کد از کتابخانه `django-environ` برای خواندن متغیرهای حساس (مانند کلیدهای API و رمزهای عبور) از فایل `.env` استفاده می‌کند. این یک رویه استاندارد و امن است.
*   **رمزنگاری درست (Password Hashing):** **OK**
    *   **شرح:** جنگو به طور پیش‌فرض از الگوریتم‌های هشینگ قوی و مدرن (مانند PBKDF2) برای ذخیره‌سازی رمزهای عبور استفاده می‌کند.
*   **Token Rotation/Expiry:** **OK**
    *   **شرح:** تنظیمات `SIMPLE_JWT` به درستی برای `ROTATE_REFRESH_TOKENS` و `BLACKLIST_AFTER_ROTATION` پیکربندی شده است که امنیت توکن‌ها را افزایش می‌دهد.

### Rate Limiting / Abuse

*   **جلوگیری Brute-force Login/OTP:** **PARTIAL**
    *   **شرح:** `Django REST Framework` دارای یک سیستم Rate Limiting سراسری است که در `settings/base.py` برای کاربران ناشناس و احرازهویت‌شده (`'anon': '400/day'`, `'user': '1000/day'`) فعال شده است. اما هیچ مکانیزم خاصی برای اندپوینت‌های حساس مانند لاگین یا درخواست OTP (اگر وجود داشت) پیاده‌سازی نشده است.
*   **Rate limit روی Checkout/Payment:** **PARTIAL**
    *   **شرح:** همان Rate Limiting سراسری برای این اندپوینت‌ها نیز اعمال می‌شود، اما بهتر است برای اندپوینت‌های پرداخت، محدودیت‌های سخت‌گیرانه‌تری در نظر گرفته شود.
*   **Captcha/Lockout Policy:** **NOT FOUND IN CODE**
    *   **شرح:** هیچ مکانیزمی برای قفل کردن حساب کاربری پس از چند تلاش ناموفق یا استفاده از کپچا مشاهده نشد.

---

## ه) لایه داده و پایداری (Data Layer & Consistency)

*   **Schema Constraints:** **OK**
    *   **شرح:** از `ForeignKey` به طور گسترده برای حفظ یکپارچگی ارجاعی (referential integrity) بین مدل‌ها استفاده شده است.
*   **ایندکس‌ها روی Queryهای پرتکرار:** **OK**
    *   **شرح:** در مدل `Order` و `OrderItem` (`orders/models.py`)، ایندکس‌هایی به درستی روی فیلدهایی که احتمالاً در کوئری‌های `WHERE` یا `ORDER BY` استفاده می‌شوند (مانند `user` و `order_date`) تعریف شده است. این به بهبود عملکرد کوئری‌ها کمک می‌کند.
*   **Transaction Boundaries و Atomicity:** **OK**
    *   **شرح:** فرآیند حساس و چندمرحله‌ای ایجاد سفارش به درستی درون یک `transaction.atomic` قرار داده شده است (`orders.serializers.OrderCreateSerializer`). این تضمین می‌کند که تمام عملیات یا با هم موفق می‌شوند یا با هم شکست می‌خورند و به حالت اولیه بازمی‌گردند.
*   **N+1 و Pagination درست:** **OK**
    *   **شرح:** در `orders.services.get_user_orders`، از `prefetch_related` برای واکشی آیتم‌های سفارش و سایر آبجکت‌های مرتبط استفاده شده است که از مشکل N+1 جلوگیری می‌کند. همچنین، یک کلاس `CustomPageNumberPagination` برای صفحه‌بندی در سطح پروژه تعریف شده است.
*   **Soft Delete vs Hard Delete:** **OK**
    *   **شرح:** سیستم از Hard Delete استفاده می‌کند (رفتار پیش‌فرض جنگو). برای آبجکت‌های حساسی مانند `Order`، در صورت حذف کاربر، فیلد `user` به `NULL` تنظیم می‌شود (`on_delete=models.SET_NULL`) که از حذف خود سفارش جلوگیری می‌کند و سوابق را حفظ می‌نماید. این یک رویکرد قابل قبول است.

---

## و) قابلیت اطمینان / رصدپذیری (Reliability / Observability)

*   **Error Handling استاندارد:** **OK**
    *   **شرح:** یک `custom_exception_handler` در مسیر `ecommerce_api/core/exceptions.py` تعریف شده که به نظر می‌رسد برای استانداردسازی پاسخ‌های خطا به کار رفته است. همچنین، فرمت پاسخ API توسط یک `ApiResponseRenderer` سفارشی یکپارچه شده است.
*   **Logging ساخت‌یافته:** **OK**
    *   **شرح:** در بخش‌های حساس مانند وب‌هوک پرداخت (`payment/views.py`)، از `logging` برای ثبت رویدادهای مهم (موفقیت، هشدار، خطا) استفاده شده است.
*   **Tracing/Metrics:** **OK**
    *   **شرح:** پروژه به ابزارهای رصدپذیری مدرن مجهز است:
        *   `django-prometheus` برای ارائه متریک‌های کلیدی برنامه (مانند تعداد درخواست‌ها و زمان پاسخ).
        *   `OpenTelemetry` برای Tracing توزیع‌شده که به شناسایی گلوگاه‌ها در یک معماری پیچیده کمک شایانی می‌کند.
*   **Retries/Timeouts/Circuit Breaker:** **NOT FOUND IN CODE**
    *   **شرح:** در تعامل با سرویس‌های خارجی (درگاه پرداخت زیبال و ارسال پُستِکس)، هیچ مکانیزمی برای تلاش مجدد (Retry) در صورت بروز خطاهای موقتی، تنظیم Timeout یا پیاده‌سازی الگوی Circuit Breaker مشاهده نشد. این می‌تواند پایداری سیستم را در مقابل خطاهای شبکه یا سرویس‌های ثالث کاهش دهد.

---

## ز) عملکرد و مقیاس‌پذیری (Performance & Scalability)

*   **Caching Strategy (Redis):** **OK**
    *   **شرح:** پروژه از `django-redis` برای کشینگ استفاده می‌کند. هرچند در کدهای بررسی‌شده (مانند لیست محصولات یا جزئیات سفارش) استفاده صریحی از API کش مشاهده نشد، اما زیرساخت آن برای بهینه‌سازی‌های آینده فراهم است.
*   **Queue/Background Jobs (Celery):** **OK**
    *   **شرح:** از Celery به درستی برای اجرای کارهای زمان‌بر یا غیرهمزمان استفاده شده است:
        *   `process_successful_payment` در `payment/tasks.py` برای پردازش وب‌هوک پرداخت.
        *   `send_order_confirmation_email` در `orders/tasks.py` برای ارسال ایمیل.
        *   `create_postex_shipment_task` در `shipping/tasks.py` برای ثبت مرسوله در سرویس خارجی.
    این الگو از مسدود شدن چرخه پاسخ‌دهی به کاربر جلوگیری کرده و مقیاس‌پذیری سیستم را افزایش می‌دهد.
*   **Hot Paths و Bottlenecks احتمالی:**
    *   **مسیر ایجاد سفارش (`OrderCreateSerializer.save`):** این مسیر به دلیل استفاده از `select_for_update`، یک گلوگاه (Bottleneck) بالقوه تحت بار بسیار سنگین است. قفل بدبینانه، پایداری داده را تضمین می‌کند اما توان عملیاتی (throughput) را کاهش می‌دهد. برای فروشگاه‌های بسیار پرترافیک، شاید نیاز به بررسی الگوهای قفل خوشبینانه (Optimistic Locking) باشد.
    *   **مسیر لیست محصولات:** اگر لیست محصولات بسیار بزرگ شود و کشینگ مناسبی روی آن اعمال نگردد، می‌تواند به یک کوئری سنگین تبدیل شود.

---

## ح) قابلیت تست و پوشش کد (Testability & Coverage)

*   **تست‌های واحد/یکپارچه:** **PARTIAL**
    *   **شرح:** ساختار پروژه برای نوشتن تست آماده است و فایل `pytest.ini` وجود دارد. با این حال، در ماژول‌های حیاتی بررسی‌شده، پوشش تست کافی به نظر نمی‌رسد. به طور خاص، هیچ تستی برای سناریوهای زیر مشاهده نشد:
        *   منطق قیمت‌گذاری و جلوگیری از دستکاری قیمت.
        *   شرایط رقابتی (Race Condition) در کاهش موجودی.
        *   پردازش صحیح وب‌هوک پرداخت.
        *   جلوگیری از دسترسی غیرمجاز به سفارش دیگران (IDOR).
*   **تست برای Race-Condition و Idempotency:** **NOT FOUND IN CODE**
    *   **شرح:** تست‌هایی که بتوانند شرایط رقابتی را شبیه‌سازی کنند (مثلاً با استفاده از multi-threading) وجود ندارند. این تست‌ها برای اطمینان از صحت الگوریتم قفل موجودی ضروری هستند.
*   **تست‌های امنیتی ساده:** **NOT FOUND IN CODE**
    *   **شرح:** هیچ تستی برای بررسی مرزهای دسترسی (Authorization Boundaries) وجود ندارد. برای مثال، تستی که بررسی کند یک کاربر عادی نمی‌تواند به اندپوینت‌های ادمین دسترسی پیدا کند.

**نکته:** فایل `test_coverage_report.md` در ریشه پروژه وجود دارد که نشان می‌دهد تیم از اهمیت پوشش کد آگاه است، اما محتوای آن نشان‌دهنده کمبود تست‌های پیاده‌سازی‌شده است.

---

## قالب گزارش مشکلات (Actionable Findings)

در ادامه، یافته‌های کلیدی این ممیزی با جزئیات فنی برای اقدام تیم توسعه ارائه می‌شود.

### [Severity: P0] عدم ثبت قیمت نهایی محصول (Price Snapshotting) منجر به سوابق مالی نادرست می‌شود

*   **Evidence:** `orders/models.py` → `OrderItem`
    *   **توضیح:** مدل `OrderItem` فاقد یک فیلد برای ذخیره قیمت واحد محصول در زمان خرید است. متد `@property def price(self)` قیمت را به صورت دینامیک و با ارجاع مستقیم به `self.product.price` محاسبه می‌کند.
*   **Impact:** **مالی / داده.** این باگ باعث می‌شود که با هر بار تغییر قیمت یک محصول در دیتابیس، قیمت تمام سفارش‌های گذشته که شامل آن محصول بوده‌اند نیز تغییر کند. این امر گزارش‌گیری مالی، محاسبه سود، مدیریت بازگشت کالا و نمایش سوابق به مشتری را کاملاً غیرقابل اتکا می‌سازد.
*   **Exploit/Repro:**
    1.  یک محصول با قیمت ۱۰۰ تومان بخرید و سفارش را نهایی کنید.
    2.  قیمت همان محصول را در پنل ادمین به ۱۵۰ تومان تغییر دهید.
    3.  جزئیات سفارش قبلی را مشاهده کنید. قیمت آیتم به جای ۱۰۰ تومان، ۱۵۰ تومان نمایش داده می‌شود.
*   **Fix:**
    1.  یک فیلد `DecimalField` به نام `price` به مدل `OrderItem` اضافه کنید.
    2.  در `orders.serializers.OrderCreateSerializer`، هنگام ساخت `OrderItem`، مقدار `product.price` را در فیلد جدید (`OrderItem.price`) ذخیره کنید.
    ```python
    # in orders/models.py
    class OrderItem(models.Model):
        # ... existing fields
        price = models.DecimalField(max_digits=10, decimal_places=2) # Add this field

    # in orders/serializers.py
    # ... inside OrderCreateSerializer.save, when creating items
    items_to_create.append(
        OrderItem(
            order=order,
            product=product,
            quantity=item['quantity'],
            price=product.price  # Store the price at the time of purchase
        )
    )
    ```
*   **Regression Tests:**
    *   یک تست بنویسید که یک سفارش ایجاد کند، سپس قیمت محصول را تغییر دهد و در نهایت تأیید کند که قیمت ذخیره‌شده در `OrderItem` بدون تغییر باقی مانده است.

---

### [Severity: P0] منطق تکراری موجودی منجر به رد شدن پرداخت‌های موفق و از دست رفتن پول مشتری می‌شود

*   **Evidence:** `payment/services.py` → `verify_payment`
    *   **توضیح:** این تابع که پس از پرداخت موفق توسط وب‌هوک فراخوانی می‌شود، مجدداً موجودی انبار را چک کرده و آن را کاهش می‌دهد (`item.product.stock -= item.quantity`). این منطق قبلاً یک بار به صورت اتمیک در `orders.serializers.OrderCreateSerializer` اجرا شده است.
*   **Impact:** **مالی / تجربه کاربری (UX).** این باگ یک شرایط رقابتی (Race Condition) خطرناک ایجاد می‌کند. اگر بین لحظه ثبت سفارش و لحظه پرداخت، موجودی محصول توسط یک خرید دیگر به اتمام برسد، این تابع پرداخت را ناموفق (`FAILED`) ثبت می‌کند، در حالی که پول از حساب مشتری کسر شده است. هیچ فرآیند بازگشت وجه خودکاری در کد وجود ندارد و این منجر به نارضایتی شدید مشتری و از دست رفتن پول او می‌شود.
*   **Exploit/Repro:**
    1.  یک محصول با موجودی ۱ عدد را به سبد خرید اضافه کنید.
    2.  سفارش را ثبت کنید (موجودی در دیتابیس صفر می‌شود) و به صفحه پرداخت بروید اما پرداخت نکنید.
    3.  با یک کاربر دیگر، همان محصول را بخرید (با فرض اینکه هنوز در لیست محصولات نمایش داده می‌شود یا با دستکاری API). این خرید به دلیل نبود موجودی شکست می‌خورد. (سناریوی بهتر: یک محصول با موجودی ۲ تا. کاربر اول سفارش ثبت می‌کند، موجودی ۱ می‌شود. کاربر دوم سفارش ثبت می‌کند، موجودی صفر می‌شود. حالا کاربر اول پرداخت می‌کند).
    4.  کاربر اول پرداخت خود را با موفقیت انجام می‌دهد.
    5.  وب‌هوک دریافت شده و تابع `verify_payment` اجرا می‌شود. به دلیل اینکه موجودی صفر است، شرط `item.product.stock < item.quantity` برقرار شده و وضعیت پرداخت `FAILED` ثبت می‌شود.
*   **Fix:**
    *   منطق مربوط به بررسی و کاهش موجودی را به طور کامل از تابع `verify_payment` حذف کنید. مسئولیت مدیریت موجودی فقط و فقط بر عهده `OrderCreateSerializer` در زمان ایجاد سفارش است.
    ```python
    # in payment/services.py
    def verify_payment(track_id):
        # ... (get order and verify with gateway)

        if response.get('result') == 100:
            # === REMOVE ALL OF THIS BLOCK ===
            # for item in order.items.all():
            #     if item.product.stock < item.quantity:
            #         ...
            # for item in order.items.all():
            #     item.product.stock -= item.quantity
            #     item.product.save()
            # ===============================

            order.payment_status = Order.PaymentStatus.SUCCESS
            order.status = Order.Status.PAID
            # ... (rest of the logic)
            order.save()
            return "Payment verified."
        # ...
    ```
*   **Regression Tests:**
    *   یک تست یکپارچه بنویسید که فرآیند پرداخت را شبیه‌سازی کند (`mock` کردن درگاه پرداخت). این تست باید تأیید کند که پس از اجرای `verify_payment`، موجودی محصول **تغییری نمی‌کند** (چون قبلاً کم شده است).

---

### [Severity: P2] عدم وجود ماشین وضعیت (State Machine) امکان انتقال‌های نامعتبر در وضعیت سفارش را فراهم می‌کند

*   **Evidence:** `orders/models.py` → `Order`
    *   **توضیح:** وضعیت‌های سفارش (`Status`) به صورت `TextChoices` تعریف شده‌اند، اما هیچ منطقی برای کنترل انتقال بین این وضعیت‌ها وجود ندارد. هر بخشی از کد که به آبجکت `Order` دسترسی داشته باشد، می‌تواند وضعیت آن را به هر مقدار دیگری تغییر دهد.
*   **Impact:** **یکپارچگی داده.** این ضعف می‌تواند منجر به وضعیت‌های متناقض و نامعتبر شود. برای مثال، یک سفارش با وضعیت `SHIPPED` می‌تواند به اشتباه به `PENDING` بازگردانده شود که باعث سردرگمی در فرآیندهای لجستیک و گزارش‌گیری می‌شود.
*   **Exploit/Repro:**
    1.  یک سفارش را تا مرحله `DELIVERED` پیش ببرید.
    2.  در یک `management command` یا از طریق `django shell`، به این آبجکت سفارش دسترسی پیدا کرده و وضعیت آن را مستقیماً به `PAID` تغییر دهید (`order.status = Order.Status.PAID; order.save()`).
    3.  سیستم بدون هیچ خطایی این تغییر نامعتبر را می‌پذیرد.
*   **Fix:**
    *   از یک کتابخانه مدیریت وضعیت مانند `django-fsm` یا `django-transitions` استفاده کنید. این کتابخانه‌ها اجازه می‌دهند تا انتقال‌های مجاز بین وضعیت‌ها را به صورت صریح تعریف کرده و از تغییرات نامعتبر جلوگیری کنید.
    ```python
    # Example using django-fsm
    from django_fsm import FSMField, transition

    class Order(models.Model):
        # ...
        status = FSMField(max_length=20, choices=Status.choices, default=Status.PENDING)

        @transition(field=status, source=Status.PENDING, target=Status.PAID)
        def pay(self):
            # Logic for payment
            pass

        @transition(field=status, source=Status.PAID, target=Status.PROCESSING)
        def process(self):
            # Logic for processing
            pass
    ```
*   **Regression Tests:**
    *   یک تست بنویسید که تلاش کند یک انتقال وضعیت نامعتبر انجام دهد (مثلاً از `SHIPPED` به `PENDING`) و تأیید کند که سیستم یک خطای `TransitionNotAllowed` ایجاد می‌کند.

---

### [Severity: P2] ثابت بودن هزینه‌های ارسال و مالیات (Hardcoded) انعطاف‌پذیری سیستم را از بین می‌برد

*   **Evidence:** `orders/serializers.py` → `OrderCreateSerializer.save`
    *   **توضیح:** مقادیر هزینه ارسال (`shipping_cost`) و مالیات (`tax_amount`) به صورت مقادیر ثابت (`Decimal('15.00')` و `Decimal('0.09')`) در کد تعریف شده‌اند.
*   **Impact:** **عملیاتی/کسب‌وکار.** با این پیاده‌سازی، هرگونه تغییر در سیاست‌های قیمت‌گذاری ارسال یا نرخ مالیات، نیازمend به تغییر کد و استقرار مجدد (redeployment) کل برنامه دارد. این کار زمان‌بر و مستعد خطا است و سیستم را در مقابل تغییرات کسب‌وکار شکننده می‌کند.
*   **Exploit/Repro:**
    1.  مدیر کسب‌وکار تصمیم می‌گیرد هزینه ارسال را به ۲۰ تومان افزایش دهد.
    2.  تیم فنی مجبور است کد را تغییر داده، آن را تست کرده و یک فرآیند استقرار کامل را طی کند.
    3.  این فرآیند ساده کسب‌وکاری، به یک چرخه توسعه نرم‌افزار تبدیل می‌شود.
*   **Fix:**
    *   این مقادیر را به تنظیمات جنگو (`settings.py`) یا یک مدل جدید در پایگاه داده (مثلاً `ShippingRule` یا `TaxRate`) منتقل کنید. این کار به مدیران سیستم اجازه می‌دهد تا این مقادیر را بدون نیاز به تغییر کد، از طریق پنل ادمین یا فایل تنظیمات تغییر دهند.
    ```python
    # Example using settings
    # in settings/base.py
    SHIPPING_COST = env.decimal('SHIPPING_COST', default='15.00')
    TAX_RATE_PERCENT = env.decimal('TAX_RATE_PERCENT', default='0.09')

    # in orders/serializers.py
    from django.conf import settings

    # ... inside OrderCreateSerializer.save
    order.shipping_cost = settings.SHIPPING_COST
    order.tax_amount = order.get_total_cost_before_discount() * settings.TAX_RATE_PERCENT
    ```
*   **Regression Tests:**
    *   یک تست بنویسید که با استفاده از `override_settings` جنگو، مقادیر هزینه ارسال و مالیات را تغییر داده و تأیید کند که سفارش جدید با مقادیر به‌روز شده ایجاد می‌شود.

---

### [Severity: P2] عدم وجود مکانیزم تلاش مجدد (Retry) سیستم را در برابر خطاهای موقتی سرویس‌های خارجی شکننده می‌کند

*   **Evidence:** `shipping/gateways.py` و `payment/gateways.py`
    *   **توضیح:** ارتباط با APIهای خارجی (زیبال و پُستِکس) از طریق کتابخانه `requests` انجام می‌شود، اما هیچ مکانیزم تلاش مجدد یا `Timeout` مشخصی برای درخواست‌ها تنظیم نشده است.
*   **Impact:** **قابلیت اطمینان (Reliability).** خطاهای موقتی شبکه یا پاسخ‌های `5xx` از سمت سرویس‌های خارجی باعث شکست دائمی عملیات (مانند ایجاد مرسوله پستی) می‌شود، در حالی که این خطاها ممکن بود با یک یا دو بار تلاش مجدد برطرف شوند. این امر منجر به فرآیندهای ناقص و نیاز به مداخله دستی می‌گردد.
*   **Exploit/Repro:**
    1.  سرویس پُستِکس برای چند ثانیه دچار اختلال شده و به درخواست ایجاد مرسوله با کد `503 Service Unavailable` پاسخ می‌دهد.
    2.  وظیفه Celery (`create_postex_shipment_task`) بلافاصله شکست می‌خورد.
    3.  سفارش مشتری پرداخت شده اما فرآیند ارسال آن آغاز نمی‌شود و باید به صورت دستی پیگیری گردد.
*   **Fix:**
    *   برای وظایف Celery که با سرویس‌های خارجی ارتباط برقرار می‌کنند، از قابلیت تلاش مجدد خودکار Celery استفاده کنید. این کار اجازه می‌دهد تا در صورت بروز خطاهای مشخص (مانند خطاهای شبکه)، وظیفه پس از یک تأخیر کوتاه مجدداً اجرا شود.
    ```python
    # in shipping/tasks.py
    from celery import shared_task
    from requests.exceptions import RequestException

    @shared_task(bind=True, max_retries=3, default_retry_delay=60) # Retry 3 times, with a 60s delay
    def create_postex_shipment_task(self, order_id):
        try:
            # ... logic to create shipment
            pass
        except RequestException as e:
            # If a network error occurs, retry the task
            raise self.retry(exc=e)
    ```
*   **Regression Tests:**
    *   یک تست بنویسید که API خارجی را `mock` کرده تا یک خطای `503` برگرداند. سپس تأیید کنید که وظیفه Celery شکست نخورده و برای تلاش مجدد زمان‌بندی شده است.

---

### [Severity: P2] عدم وجود سیاست انقضای رزرو موجودی، کالاها را در سفارش‌های پرداخت‌نشده قفل می‌کند

*   **Evidence:** `orders/serializers.py` → `OrderCreateSerializer.save`
    *   **توضیح:** در پیاده‌سازی فعلی، موجودی کالا تنها زمانی کم می‌شود که سفارش با موفقیت ثبت شود. اما اگر بخواهیم برای جلوگیری از تجربه کاربری بد (رفتن به صفحه پرداخت و سپس مواجه شدن با اتمام موجودی)، موجودی را در زمان ایجاد سفارش رزرو کنیم، هیچ مکانیزمی برای آزادسازی آن در صورت عدم پرداخت کاربر وجود ندارد.
*   **Impact:** **کسب‌وکار/موجودی.** اگر سیستم به سمت رزرو موجودی قبل از پرداخت تغییر کند (یک سناریوی رایج)، کالاهای با تعداد محدود ممکن است توسط کاربرانی که قصد خرید ندارند، در سفارش‌های `pending` برای مدت نامحدودی قفل شوند و از دسترس خریداران واقعی خارج گردند.
*   **Exploit/Repro:**
    1.  یک محصول محبوب با موجودی ۱ عدد را به سبد خرید اضافه کرده و سفارش را ثبت کنید (موجودی رزرو و صفر می‌شود).
    2.  از پرداخت هزینه انصراف دهید.
    3.  هیچ کاربر دیگری نمی‌تواند آن محصول را بخرد زیرا موجودی آن صفر است و هرگز به صورت خودکار آزاد نمی‌شود.
*   **Fix:**
    *   یک وظیفه دوره‌ای (periodic task) با استفاده از Celery Beat ایجاد کنید. این وظیفه باید هر چند دقیقه یک بار اجرا شده و سفارش‌هایی که در وضعیت `pending` هستند و از زمان ایجاد آن‌ها مدت مشخصی (مثلاً ۱۵ دقیقه) گذشته است را پیدا کرده، آن‌ها را به وضعیت `canceled` تغییر داده و موجودی محصولات آن‌ها را به انبار بازگرداند.
    ```python
    # Example Celery task
    from django.utils import timezone
    from datetime import timedelta

    @shared_task
    def cancel_unpaid_orders():
        expiration_time = timezone.now() - timedelta(minutes=15)
        expired_orders = Order.objects.filter(
            status=Order.Status.PENDING,
            order_date__lt=expiration_time
        )
        for order in expired_orders:
            with transaction.atomic():
                for item in order.items.all():
                    item.product.stock += item.quantity
                    item.product.save()
                order.status = Order.Status.CANCELED
                order.save()
    ```
*   **Regression Tests:**
    *   یک تست بنویسید که یک سفارش `pending` ایجاد کند. سپس زمان را به صورت مصنوعی جلو برده (با استفاده از کتابخانه‌هایی مانند `freezegun`) و وظیفه `cancel_unpaid_orders` را اجرا کنید. در نهایت، تأیید کنید که وضعیت سفارش به `canceled` تغییر کرده و موجودی محصول به حالت اولیه بازگشته است.

---

### [Severity: P3] عدم فعال‌سازی تاریخچه تغییرات، ردگیری و اشکال‌زدایی مشکلات سفارش را دشوار می‌کند

*   **Evidence:** `orders/models.py` → `Order`
    *   **توضیح:** کتابخانه `django-simple-history` در پروژه نصب شده است (`settings/base.py`) اما روی مدل `Order` فعال نشده است.
*   **Impact:** **عملیاتی/پشتیبانی.** بدون داشتن تاریخچه‌ای از تغییرات وضعیت یک سفارش، فهمیدن اینکه چه کسی (کدام کاربر یا کدام فرآیند سیستمی) و در چه زمانی وضعیت یک سفارش را تغییر داده است، بسیار دشوار می‌شود. این موضوع اشکال‌زدایی (Debugging) مشکلات و پاسخگویی به مشتریان را پیچیده می‌کند.
*   **Exploit/Repro:**
    1.  وضعیت یک سفارش به اشتباه از `PROCESSING` به `SHIPPED` تغییر می‌کند.
    2.  تیم پشتیبانی نمی‌تواند تشخیص دهد که این تغییر توسط چه کسی (یک ادمین یا یک باگ در سیستم) و در چه ساعتی انجام شده است.
*   **Fix:**
    *   قابلیت تاریخچه را به مدل `Order` اضافه کنید. این کار به سادگی و با افزودن یک خط کد به مدل امکان‌پذیر است.
    ```python
    # in orders/models.py
    from simple_history.models import HistoricalRecords

    class Order(models.Model):
        # ... existing fields
        history = HistoricalRecords()

        # ... rest of the model
    ```
*   **Regression Tests:**
    *   یک تست بنویسید که وضعیت یک سفارش را چند بار تغییر دهد. سپس کوئری به تاریخچه (`order.history.all()`) را اجرا کرده و تأیید کند که تمام تغییرات به درستی ثبت شده‌اند.

---

### [Severity: P3] Rate Limiting عمومی برای اندپوینت‌های حساس مانند پرداخت کافی نیست

*   **Evidence:** `ecommerce_api/settings/base.py` → `REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']`
    *   **توضیح:** یک سیاست محدودیت نرخ (`Rate Limiting`) سراسری برای کل API (`'user': '1000/day'`) تعریف شده است. اما اندپوینت‌های حساس مانند ایجاد درخواست پرداخت (`/payment/process/`) یا ایجاد سفارش (`/api/v1/orders/`) از همین سیاست عمومی استفاده می‌کنند.
*   **Impact:** **امنیتی/هزینه.** یک کاربر مخرب یا یک اسکریپت معیوب می‌تواند در یک بازه زمانی کوتاه تعداد زیادی درخواست پرداخت ناموفق ایجاد کند. این امر می‌تواند منجر به تحمیل هزینه از سوی درگاه پرداخت (در صورت وجود) یا قرار گرفتن در لیست سیاه آن درگاه به دلیل فعالیت مشکوک شود.
*   **Exploit/Repro:**
    1.  یک مهاجم با یک توکن کاربری معتبر، یک اسکریپت می‌نویسد که اندپوینت ایجاد سفارش و سپس ایجاد درخواست پرداخت را در یک حلقه تکرار می‌کند.
    2.  در عرض چند دقیقه، صدها سفارش `pending` و درخواست پرداخت ایجاد می‌شود که می‌تواند باعث اختلال در سرویس یا ایجاد هزینه شود.
*   **Fix:**
    *   برای ViewSetها یا APIViewهای حساس، کلاس‌های `throttle` سفارشی با محدودیت‌های سخت‌گیرانه‌تر تعریف کنید. برای مثال، می‌توان به هر کاربر اجازه داد در هر دقیقه تنها چند بار درخواست پرداخت ایجاد کند.
    ```python
    # in ecommerce_api/settings/base.py
    'DEFAULT_THROTTLE_RATES': {
        'anon': '400/day',
        'user': '1000/day',
        'payment': '5/min', # Add a new scope
    },

    # in payment/views.py
    from rest_framework.throttling import UserRateThrottle

    class PaymentProcessAPIView(APIView):
        permission_classes = [IsAuthenticated]
        throttle_scope = 'payment' # Apply the stricter scope

        def post(self, request, *args, **kwargs):
            # ...
    ```
*   **Regression Tests:**
    *   یک تست بنویسید که بیش از ۵ بار در یک دقیقه به اندپوینت پرداخت درخواست ارسال کند و تأیید کند که پس از تلاش پنجم، یک پاسخ `429 Too Many Requests` دریافت می‌شود.

---

### [Severity: P1] عدم وجود منطق بازگشت وجه (Refund) فرآیندهای مالی را ناقص و پرریسک می‌کند

*   **Evidence:** کل پایگاه کد.
    *   **توضیح:** هیچ API، سرویس یا تابعی برای مدیریت بازگشت وجه کامل یا جزئی یک سفارش در کد وجود ندارد.
*   **Impact:** **مالی/عملیاتی.** بدون یک فرآیند استاندارد برای بازگشت وجه، تیم پشتیبانی مجبور است این کار را به صورت دستی و خارج از سیستم (مثلاً از طریق پنل درگاه پرداخت) انجام دهد. این رویکرد مستعد خطای انسانی است، هیچ ردپایی در سیستم باقی نمی‌گذارد و منجر به عدم همخوانی داده‌های مالی بین سیستم فروشگاه و درگاه پرداخت می‌شود. همچنین، سناریوهایی مانند باگ کاهش موجودی تکراری (یافته P0) بدون این قابلیت قابل حل نیستند.
*   **Exploit/Repro:**
    1.  یک مشتری سفارشی را لغو می‌کند و درخواست بازگشت وجه دارد.
    2.  تیم پشتیبانی به صورت دستی از طریق پنل زیبال وجه را بازمی‌گرداند.
    3.  در سیستم فروشگاه، سفارش همچنان در وضعیت `PAID` باقی مانده و در گزارش‌های فروش به عنوان یک تراکنش موفق محاسبه می‌شود.
*   **Fix:**
    *   یک اندپوینت امن (فقط برای ادمین) برای آغاز فرآیند بازگشت وجه ایجاد کنید. این اندپوینت باید با API درگاه پرداخت ارتباط برقرار کرده، درخواست بازگشت وجه را ثبت کند و در صورت موفقیت، وضعیت سفارش را به `REFUNDED` تغییر دهد. همچنین، باید یک مدل `Refund` برای ثبت تمام تراکنش‌های بازگشت وجه ایجاد شود.
    ```python
    # Example View (simplified)
    class RefundOrderView(APIView):
        permission_classes = [IsAdminUser]

        def post(self, request, order_id):
            order = get_object_or_404(Order, order_id=order_id)
            if not order.can_be_refunded():
                return Response({'error': 'Order cannot be refunded.'}, status=400)

            gateway = ZibalGateway()
            success = gateway.refund(transaction_id=order.payment_ref_id, amount=order.total_payable)

            if success:
                order.status = Order.Status.REFUNDED
                order.save()
                Refund.objects.create(order=order, amount=order.total_payable, reason='User request')
                return Response({'status': 'Refunded successfully.'})
            else:
                return Response({'error': 'Gateway refund failed.'}, status=500)
    ```
*   **Regression Tests:**
    *   یک تست بنویسید که یک سفارش پرداخت‌شده ایجاد کند. سپس اندپوینت `Refund` را فراخوانی کرده (با `mock` کردن API درگاه) و تأیید کند که وضعیت سفارش به `REFUNDED` تغییر کرده و یک آبجکت `Refund` در پایگاه داده ایجاد شده است.

---

### [Severity: P2] عدم وجود مکانیزم جایگزین، سفارش‌ها را در صورت عدم دریافت وب‌هوک در وضعیت نامشخص قرار می‌دهد

*   **Evidence:** `payment/services.py` → `verify_payment`
    *   **توضیح:** کل فرآیند تأیید پرداخت و تغییر وضعیت سفارش به `PAID` به دریافت یک وب‌هوک از درگاه پرداخت وابسته است. هیچ مکانیزم جایگزینی (Fallback) برای حالتی که وب‌هوک به دلیل خطای شبکه یا مشکل از سمت درگاه هرگز دریافت نشود، وجود ندارد.
*   **Impact:** **یکپارچگی داده/تجربه کاربری.** اگر کاربر پول را پرداخت کند اما وب‌هوک دریافت نشود، سفارش او برای همیشه در وضعیت `PENDING` باقی می‌ماند. این امر منجر به سردرگمی مشتری و نیاز به پیگیری دستی توسط تیم پشتیبانی می‌شود.
*   **Exploit/Repro:**
    1.  کاربر هزینه سفارش را با موفقیت پرداخت می‌کند.
    2.  درگاه پرداخت زیبال به دلیل یک مشکل فنی داخلی، وب‌هوک تأیید را به سرور فروشگاه ارسال نمی‌کند.
    3.  سفارش مشتری در سیستم `PENDING` باقی می‌ماند و فرآیند ارسال هرگز آغاز نمی‌شود، در حالی که پول از حساب او کسر شده است.
*   **Fix:**
    *   یک وظیفه دوره‌ای (periodic task) با استفاده از Celery Beat ایجاد کنید تا وضعیت سفارش‌هایی که برای مدتی در حالت `PENDING` باقی مانده‌اند را مستقیماً از طریق API درگاه پرداخت استعلام کند. این کار به عنوان یک مکانیزم پشتیبان عمل کرده و سفارش‌های موفق را تأیید می‌کند.
    ```python
    # Example Celery task
    @shared_task
    def reconcile_pending_payments():
        # Look for orders that are pending for more than 10 minutes but less than an hour
        start_time = timezone.now() - timedelta(minutes=60)
        end_time = timezone.now() - timedelta(minutes=10)
        orders_to_check = Order.objects.filter(
            status=Order.Status.PENDING,
            payment_status=Order.PaymentStatus.PENDING,
            payment_track_id__isnull=False,
            order_date__range=(start_time, end_time)
        )
        gateway = ZibalGateway()
        for order in orders_to_check:
            response = gateway.verify_payment(order.payment_track_id)
            if response.get('result') == 100:
                # If payment was successful, update the order status
                order.payment_status = Order.PaymentStatus.SUCCESS
                order.status = Order.Status.PAID
                order.save()
                # Potentially trigger other post-payment tasks
    ```
*   **Regression Tests:**
    *   یک تست بنویسید که یک سفارش `PENDING` با `track_id` ایجاد کند. سپس وظیفه `reconcile_pending_payments` را اجرا کرده (با `mock` کردن پاسخ موفق از درگاه) و تأیید کند که وضعیت سفارش به `PAID` تغییر کرده است.
