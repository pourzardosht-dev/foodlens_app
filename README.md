# FoodLens

نسخه اولیه FoodLens شامل یک اپ Flutter فارسی و یک API مبتنی بر FastAPI است. کاربر تصویر غذا را انتخاب می‌کند، اجزای مستقل بشقاب و وزن هرکدام را تأیید یا اصلاح می‌کند و بازه کالری آن‌ها در دفتر روزانه ثبت می‌شود.

## وضعیت فعلی

- داشبورد فارسی و RTL
- دریافت تصویر از دوربین یا گالری
- تشخیص و ویرایش حداکثر هشت جزء مستقل در هر بشقاب
- کاتالوگ مرکزی ۸۷ غذای ایرانی و عمومی، میوه، نوشیدنی و تنقلات با واحدهای مصرف و بازه عدم‌قطعیت
- محاسبه قطعی کالری و بازه عدم قطعیت
- API فهرست غذاها و تخمین تغذیه
- API تشخیص تصویر با provider قابل تعویض و حالت `unknown`
- پروفایل ناشناس با token امن و دفتر غذایی پایدار مبتنی بر PostgreSQL
- CRUD وعده و اجزای آن، غذای سفارشی خصوصی، export JSON و حذف کامل پروفایل
- Nutrition Engine قطعی برای کالری، پروتئین، کربوهیدرات، چربی و فیبر با snapshot تاریخی
- پیمایش روزها، خلاصه ماکروها، ویرایش و حذف وعده در Flutter
- rate limit، request ID، متریک HTTP و audit log رویدادهای export و deletion
- migration یک‌مرحله‌ای، backup رمزگذاری‌شده و restore test ایزوله

اعداد تغذیه‌ای فعلی فقط seed توسعه هستند و پیش از انتشار باید توسط منبع معتبر و متخصص تغذیه بازبینی شوند.

فرمت release و importer کنترل‌شده برای ۲۰ غذای نخست در [راهنمای انتشار داده تغذیه‌ای](docs/nutrition-release.md) مستند شده است.

جزئیات قراردادها و gateهای انتشار در [PRD زیرساخت داده شخصی و Nutrition Engine V1](docs/personal-data-nutrition-v1-prd.md) آمده است. کاتالوگ توسعه ۸۷ غذا همچنان `draft` است؛ production فقط نسخه‌های `source_checked` یا `nutritionist_reviewed` را برمی‌گرداند.

## اجرای backend

```powershell
Set-Location backend
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

سپس مستندات API در `http://127.0.0.1:8000/docs` در دسترس است.

برای اعمال schema اولیه روی PostgreSQL، `DATABASE_URL` را تنظیم و migration را اجرا کنید:

```powershell
Set-Location backend
$env:DATABASE_URL="postgresql+psycopg://foodlens:password@localhost:5432/foodlens"
alembic upgrade head
```

وضعیت مستقل database از مسیر `/health/database` قابل بررسی است. قطع بودن database مسیر `/health` و قابلیت تشخیص تصویر را از دسترس خارج نمی‌کند.

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

Compose به‌صورت پیش‌فرض فقط API را اجرا می‌کند؛ PostgreSQL و migration task در profile اختیاری `database` و MinIO در profile جداگانه `object-storage` قرار دارند. API فقط روی `127.0.0.1:18431` منتشر می‌شود. پیش از rollout روی VPS مشترک، migration، backup و restore را طبق [راهنمای استقرار VPS](docs/vps-deployment.md) در staging واقعی PostgreSQL تمرین کنید.

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

برای اجرای ارزیابی تکرارپذیر Recognition API و گزارش accuracy، unknown rate و latency، [راهنمای benchmark](docs/recognition-benchmark.md) را ببینید.

## موارد موردنیاز از مالک محصول

1. ساخت Gemini API key؛ کلید را در گفتگو یا repository قرار ندهید.
2. قرار دادن حداقل 100 تصویر Gold دارای مجوز در یک پوشه محلی برای benchmark.
3. معرفی منابع تغذیه‌ای قابل استناد یا متخصص تغذیه برای بازبینی seed data.
4. انتخاب دامنه برای فعال‌سازی HTTPS در مرحله استقرار عمومی.

## Gateهای انتشار باقی‌مانده

1. انتخاب ۲۰ غذای پرتکرار و ورود پنج nutrient از منبع دارای مجوز، سپس review و تغییر وضعیت به `source_checked`؛ مقدار macro بدون منبع ساخته نمی‌شود.
2. اجرای migration، integration test، backup و restore روی PostgreSQL 17 واقعی؛ محیط توسعه فعلی Docker ندارد.
3. benchmark حداقل ۱۰۰ تصویر مجاز و انتخاب provider بر پایه دقت، unknown recall، latency و هزینه.
4. preflight و rollout مرحله‌ای روی VPS پس از انتخاب دامنه، بدون تغییر QuizLens یا containerهای نامرتبط.