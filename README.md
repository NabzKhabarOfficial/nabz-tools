# NABZ Tools

مجموعه‌ی ۳۱ ابزار آنلاین رایگان و سبک برای استفاده‌ی روزمره، با تمرکز روی کاربر ایرانی.

🌐 سایت: https://nabzkhabarofficial.github.io/nabz-tools/

## ابزارها (۳۱)

### 💵 مالی، ارز و طلا
- تبدیل ارز با نرخ روز (ارز جهانی، رمزارز، سکه و تومان بازار آزاد) — `currency-converter`
- قیمت بازار (دلار، طلا، سکه) — `market-prices`
- محاسبه‌گر طلا — `gold-calculator`
- محاسبه حقوق و مالیات ۱۴۰۵ — `salary-calculator`
- سود سپرده بانکی — `deposit-interest`
- تبدیل رهن و اجاره — `rent-converter`
- محاسبه وام و اقساط — `loan-calculator`
- تخفیف و ارزش افزوده — `discount-vat`
- محاسبه درصد — `percentage`

### 🇮🇷 مخصوص ایران و فارسی
- بررسی کد ملی، کارت و شبا — `iran-validator`
- تبدیل تاریخ شمسی/میلادی — `jalali-converter`
- عدد به حروف — `number-to-words`
- تبدیل ارقام و اصلاح ي/ك — `digits-converter`

### ✍️ متن و کدنویسی
- شمارشگر کلمات و کاراکترها — `word-counter`
- JSON Formatter — `json-formatter`
- Base64 Encoder / Decoder — `base64`
- URL Encoder / Decoder — `url-encoder`
- تبدیل حالت متن — `text-case`
- مولد رمز عبور — `password-generator`
- Hash و UUID — `hash-generator`
- مبدل رنگ HEX / RGB — `color-converter`

### 🖼️ تصویر و فایل
- فشرده‌سازی تصویر — `image-compressor`
- تغییر اندازه تصویر — `image-resizer`
- تبدیل JPG / PNG / WebP — `image-converter`
- تبدیل چند تصویر به PDF — `pdf-tools`
- ساخت QR Code — `qr-generator`

### 🧮 محاسبه و زمان
- تبدیل واحد — `unit-converter`
- مبدل Unix Timestamp — `timestamp`
- محاسبه سن — `age-calculator`
- اختلاف دو تاریخ — `date-difference`
- محاسبه BMI — `bmi`

علاوه بر ابزارها، ۱۴ راهنمای کاربردی در پوشه‌ی `guides/` هست.

## ساختار پروژه

- `index.html` صفحه اصلی و جستجوی ابزارها
- `tools/` صفحه‌ی هر ابزار
- `guides/` راهنماها
- `assets/` اسکریپت‌ها و استایل‌های مشترک (`nabz.js` شامل سوییچر ابزارها با Ctrl+K)
- `data/rates.json` نرخ ارز، طلا و سکه
- `sitemap.xml` و `robots.txt` برای سئو

## خودکارسازی

- `.github/workflows/rates.yml` هر دو ساعت نرخ‌ها را از منابع عمومی به‌روز می‌کند (روزهای تعطیل با قیمت تتر تنظیم می‌شود).
- `.github/workflows/validate.yml` قبل از انتشار، کل سایت را با `tests/validate_site.py` بررسی می‌کند: وجود ۳۱ ابزار، لینک‌ها، متا تگ‌ها، canonical، JSON-LD، شناسه‌های تکراری، سینتکس جاوااسکریپت و تطابق دقیق sitemap.
- `.github/workflows/pages.yml` سایت را روی GitHub Pages منتشر می‌کند.

اجرای محلی اعتبارسنجی (نیاز به Python 3 و Node.js):

```bash
python3 tests/validate_site.py
```

## اصول پروژه

- کاملاً رایگان و بدون وابستگی به سرویس پولی
- پردازش داخل مرورگر؛ فایل‌ها و اطلاعات کاربر به سرور ارسال نمی‌شوند
- بدون نیاز به نصب یا ثبت‌نام
- طراحی واکنش‌گرا برای موبایل و دسکتاپ
- ساختار مناسب برای SEO

## افزودن ابزار جدید

1. صفحه را در `tools/<slug>.html` بساز.
2. کارت آن را در `index.html` و آیتم آن را در سوییچر `assets/nabz.js` اضافه کن.
3. آدرس آن را به `sitemap.xml` و slug را به لیست `TOOLS` در `tests/validate_site.py` اضافه کن.

> نرخ‌ها تقریبی‌اند و نرخ قطعی معامله نیستند.
