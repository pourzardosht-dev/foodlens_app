# FoodLens

نسخه اولیه FoodLens شامل یک اپ Flutter فارسی و یک API مبتنی بر FastAPI است. در این مرحله کاربر تصویر غذا را انتخاب می‌کند، نام و مقدار غذا را تأیید می‌کند و یک بازه کالری در دفتر روزانه ثبت می‌شود.

## وضعیت فعلی

- داشبورد فارسی و RTL
- دریافت تصویر از دوربین یا گالری
- پنج غذای اولیه: قرمه‌سبزی، فسنجان، برنج، کباب کوبیده و آش رشته
- محاسبه قطعی کالری و بازه عدم قطعیت
- API فهرست غذاها و تخمین تغذیه
- API تشخیص تصویر با provider قابل تعویض و حالت `unknown`
- scaffold استقرار PostgreSQL، pgvector و MinIO

اعداد تغذیه‌ای فعلی فقط seed توسعه هستند و پیش از انتشار باید توسط منبع معتبر و متخصص تغذیه بازبینی شوند.

## اجرای backend

```powershell
Set-Location backend
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

سپس مستندات API در `http://127.0.0.1:8000/docs` در دسترس است.

## اجرای اپ

```powershell
Set-Location mobile
flutter pub get
flutter run
```

برای اجرای مرورگر می‌توان از `flutter run -d chrome` استفاده کرد. دوربین و گالری روی دستگاه واقعی بهتر ارزیابی می‌شوند.

آدرس API در زمان build قابل تنظیم است:

```powershell
flutter run -d chrome --dart-define=FOODLENS_API_URL=http://127.0.0.1:8000
```

برای انتشار رایگان Flutter Web، راهنمای [GitHub Pages](docs/github-pages.md) را ببینید. Pages فقط frontend است و API همچنان روی VPS اجرا می‌شود.

## تست‌ها

```powershell
Set-Location backend
python -m pytest -q

Set-Location ../mobile
flutter test
flutter analyze
```

## اجرای زیرساخت روی VPS

پس از نصب Docker و Docker Compose روی VPS:

```bash
cp .env.example .env
# تمام رمزهای داخل .env را تغییر دهید.
docker compose -p foodlens --env-file .env -f infra/compose.yaml up -d --build api
```

در نسخه فعلی persistence هنوز به PostgreSQL و MinIO متصل نشده است، بنابراین Compose به‌صورت پیش‌فرض فقط API را اجرا می‌کند و سرویس‌های ذخیره‌سازی در profile اختیاری `storage` غیرفعال هستند. API فقط روی `127.0.0.1:18431` منتشر می‌شود. پیش از اجرا روی VPS مشترک، راهنمای [استقرار VPS](docs/vps-deployment.md) را دنبال کنید.

## Vision API

حالت پیش‌فرض `mock` است و هزینه API ندارد. برای فعال‌سازی Gemini، مقادیر زیر را فقط در فایل `.env` سرور تنظیم کنید:

```dotenv
VISION_PROVIDER=gemini
GEMINI_MODEL=gemini-3.6-flash
GEMINI_API_KEY=your-key-set-directly-on-the-server
```

کلید API نباید commit یا در گفتگو ارسال شود. انتخاب فعلی و برنامه benchmark در [تصمیم Vision Provider](docs/vision-provider.md) ثبت شده است.

## منابع داده

تصاویر و متن Cookpad بدون مجوز کتبی وارد dataset نمی‌شوند. جزئیات در [سیاست منابع داده](docs/data-sourcing.md) آمده است.

## دیتاست محلی

برای audit غیرمخرب تصاویر:

```powershell
Set-Location backend
python scripts/audit_dataset.py "../food pic"
```

این دستور فایل خراب، تصاویر کوچک و duplicateهای دقیق را گزارش می‌کند و هیچ تصویری را تغییر نمی‌دهد.

برای ساخت manifestهای قطعی train/validation/test بدون کپی یا جابه‌جایی تصاویر:

```powershell
Set-Location backend
python scripts/prepare_dataset.py "../food pic" "../dataset/manifests"
```

ابزار، تصاویر کوچک‌تر از 224px را در `excluded.jsonl` ثبت می‌کند و duplicateهای دقیق و نزدیک را همیشه در یک split نگه می‌دارد. اگر تصاویر مشابه در دو کلاس متفاوت باشند، هر دو با دلیل `label_conflict` از benchmark کنار گذاشته می‌شوند. پوشه‌های داده خام و manifest تولیدشده عمداً در Git نادیده گرفته می‌شوند.

## موارد موردنیاز از مالک محصول

1. ساخت Gemini API key؛ کلید را در گفتگو یا repository قرار ندهید.
2. قرار دادن حداقل 100 تصویر Gold دارای مجوز در یک پوشه محلی برای benchmark.
3. معرفی منابع تغذیه‌ای قابل استناد یا متخصص تغذیه برای بازبینی seed data.
4. انتخاب دامنه برای فعال‌سازی HTTPS در مرحله استقرار عمومی.

## گام فنی بعدی

اتصال Flutter به Recognition API، افزودن persistence با PostgreSQL، آپلود خصوصی تصاویر و ساخت benchmark مقایسه‌ای Gemini/OpenAI/DeepSeek.