import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../recognition/recognition_api.dart';

class FoodOption {
  const FoodOption({
    required this.id,
    required this.name,
    required this.portionName,
    required this.portionGrams,
    required this.kcalPer100g,
    required this.uncertainty,
  });

  final String id;
  final String name;
  final String portionName;
  final double portionGrams;
  final double kcalPer100g;
  final double uncertainty;
}

class DiaryEntry {
  const DiaryEntry({
    required this.food,
    required this.quantity,
    required this.grams,
    required this.calories,
    required this.rangeMin,
    required this.rangeMax,
  });

  final FoodOption food;
  final double quantity;
  final double grams;
  final double calories;
  final double rangeMin;
  final double rangeMax;
}

const foods = <FoodOption>[
  FoodOption(
    id: 'ghormeh-sabzi',
    name: 'قرمه‌سبزی',
    portionName: 'ملاقه',
    portionGrams: 180,
    kcalPer100g: 165,
    uncertainty: .18,
  ),
  FoodOption(
    id: 'fesenjan',
    name: 'فسنجان',
    portionName: 'ملاقه',
    portionGrams: 180,
    kcalPer100g: 220,
    uncertainty: .22,
  ),
  FoodOption(
    id: 'cooked-rice',
    name: 'برنج پخته',
    portionName: 'کفگیر',
    portionGrams: 110,
    kcalPer100g: 130,
    uncertainty: .10,
  ),
  FoodOption(
    id: 'koobideh-kebab',
    name: 'کباب کوبیده',
    portionName: 'سیخ',
    portionGrams: 100,
    kcalPer100g: 250,
    uncertainty: .15,
  ),
  FoodOption(
    id: 'ash-reshteh',
    name: 'آش رشته',
    portionName: 'کاسه',
    portionGrams: 400,
    kcalPer100g: 110,
    uncertainty: .20,
  ),
];

double quantityForGrams({
  required double grams,
  required double portionGrams,
}) => grams / portionGrams;

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, this.recognitionApi = const RecognitionApi()});

  final RecognitionApi recognitionApi;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _picker = ImagePicker();
  final _entries = <DiaryEntry>[];
  Uint8List? _selectedImage;
  bool _isReadingImage = false;

  double get _todayCalories =>
      _entries.fold(0, (sum, item) => sum + item.calories);

  Future<void> _pickImage(ImageSource source) async {
    setState(() => _isReadingImage = true);
    try {
      final image = await _picker.pickImage(
        source: source,
        imageQuality: 82,
        maxWidth: 1600,
      );
      if (image == null || !mounted) return;
      final bytes = await image.readAsBytes();
      if (!mounted) return;
      setState(() => _selectedImage = bytes);
      RecognitionResult? recognition;
      var recognitionUnavailable = false;
      try {
        recognition = await widget.recognitionApi.recognize(image);
      } on RecognitionApiException {
        recognitionUnavailable = true;
      }
      if (!mounted) return;
      await _openAnalysisSheet(
        recognition: recognition,
        recognitionUnavailable: recognitionUnavailable,
      );
    } finally {
      if (mounted) setState(() => _isReadingImage = false);
    }
  }

  Future<void> _showImageSource() async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'افزودن تصویر',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              ListTile(
                leading: const Icon(Icons.photo_camera_outlined),
                title: const Text('گرفتن عکس'),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.camera);
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library_outlined),
                title: const Text('انتخاب از گالری'),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.gallery);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _openAnalysisSheet({
    RecognitionResult? recognition,
    required bool recognitionUnavailable,
  }) async {
    FoodOption selectedFood = foods.firstWhere(
      (food) => food.id == recognition?.foodId,
      orElse: () => foods.first,
    );
    double quantity = 1;
    final entry = await showModalBottomSheet<DiaryEntry>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) {
          final grams = selectedFood.portionGrams * quantity;
          final calories = grams * selectedFood.kcalPer100g / 100;
          final rangeMin = calories * (1 - selectedFood.uncertainty);
          final rangeMax = calories * (1 + selectedFood.uncertainty);
          return SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (_selectedImage case final image?)
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.memory(
                        image,
                        height: 190,
                        fit: BoxFit.cover,
                      ),
                    ),
                  const SizedBox(height: 20),
                  Text(
                    'تأیید نتیجه',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    _recognitionMessage(
                      recognition,
                      recognitionUnavailable: recognitionUnavailable,
                    ),
                  ),
                  const SizedBox(height: 18),
                  DropdownButtonFormField<FoodOption>(
                    initialValue: selectedFood,
                    decoration: const InputDecoration(
                      labelText: 'غذا',
                      border: OutlineInputBorder(),
                    ),
                    items: foods
                        .map(
                          (food) => DropdownMenuItem(
                            value: food,
                            child: Text(food.name),
                          ),
                        )
                        .toList(),
                    onChanged: (food) {
                      if (food != null) {
                        setSheetState(() {
                          selectedFood = food;
                          quantity = 1;
                        });
                      }
                    },
                  ),
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'مقدار: ${_formatQuantity(quantity)} ${selectedFood.portionName}',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                      IconButton.outlined(
                        tooltip: 'کاهش مقدار',
                        onPressed: quantity > .5
                            ? () => setSheetState(() => quantity -= .5)
                            : null,
                        icon: const Icon(Icons.remove),
                      ),
                      const SizedBox(width: 8),
                      IconButton.filled(
                        tooltip: 'افزایش مقدار',
                        onPressed: () => setSheetState(() => quantity += .5),
                        icon: const Icon(Icons.add),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    key: const Key('edit-portion-weight'),
                    onPressed: () async {
                      final editedGrams = await _editPortionWeight(
                        context,
                        initialGrams: grams,
                      );
                      if (editedGrams != null) {
                        setSheetState(
                          () => quantity = quantityForGrams(
                            grams: editedGrams,
                            portionGrams: selectedFood.portionGrams,
                          ),
                        );
                      }
                    },
                    icon: const Icon(Icons.edit_outlined),
                    label: const Text('تغییر مقدار یا وزن کل'),
                  ),
                  const SizedBox(height: 18),
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE4EFE9),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.local_fire_department_outlined),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            '${calories.round()} کیلوکالری\nبازه محتمل: ${rangeMin.round()} تا ${rangeMax.round()}',
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                        ),
                        Text('${grams.round()} گرم'),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),
                  FilledButton.icon(
                    onPressed: () => Navigator.pop(
                      context,
                      DiaryEntry(
                        food: selectedFood,
                        quantity: quantity,
                        grams: grams,
                        calories: calories,
                        rangeMin: rangeMin,
                        rangeMax: rangeMax,
                      ),
                    ),
                    icon: const Icon(Icons.check),
                    label: const Text('ثبت در وعده امروز'),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
    if (entry != null && mounted) setState(() => _entries.insert(0, entry));
  }

  String _formatQuantity(double value) => value == value.roundToDouble()
      ? value.toInt().toString()
      : value.toStringAsFixed(1);

  Future<double?> _editPortionWeight(
    BuildContext context, {
    required double initialGrams,
  }) async {
    final controller = TextEditingController(
      text: initialGrams.round().toString(),
    );
    String? errorText;
    final result = await showDialog<double>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('ویرایش مقدار غذا'),
          content: TextField(
            key: const Key('portion-weight-input'),
            controller: controller,
            autofocus: true,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(
              labelText: 'وزن تقریبی کل',
              suffixText: 'گرم',
              helperText: 'وزن تمام غذای داخل تصویر را وارد کنید.',
              errorText: errorText,
              border: const OutlineInputBorder(),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('انصراف'),
            ),
            FilledButton(
              onPressed: () {
                final value = double.tryParse(
                  controller.text.trim().replaceAll(',', '.'),
                );
                if (value == null || value <= 0 || value > 100000) {
                  setDialogState(
                    () => errorText = 'وزنی بین ۱ تا ۱۰۰٬۰۰۰ گرم وارد کنید.',
                  );
                  return;
                }
                Navigator.pop(context, value);
              },
              child: const Text('اعمال مقدار'),
            ),
          ],
        ),
      ),
    );
    controller.dispose();
    return result;
  }

  String _recognitionMessage(
    RecognitionResult? result, {
    required bool recognitionUnavailable,
  }) {
    if (recognitionUnavailable) {
      return 'ارتباط با سرویس تشخیص برقرار نشد؛ غذا را دستی انتخاب کنید.';
    }
    if (result == null || result.foodId == null) {
      return 'نتیجه قطعی نبود؛ لطفاً نام غذا را انتخاب کنید.';
    }
    final confidence = (result.confidence * 100).round();
    return result.needsConfirmation
        ? 'پیشنهاد هوش مصنوعی با اطمینان $confidence٪؛ لطفاً بررسی کنید.'
        : 'تشخیص هوش مصنوعی با اطمینان $confidence٪؛ نام غذا را تأیید کنید.';
  }

  @override
  Widget build(BuildContext context) {
    const target = 2000.0;
    final progress = (_todayCalories / target).clamp(0.0, 1.0);
    return Scaffold(
      appBar: AppBar(
        title: const Text('FoodLens'),
        actions: [
          IconButton(
            tooltip: 'پروفایل',
            onPressed: () {},
            icon: const Icon(Icons.account_circle_outlined),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
              sliver: SliverList.list(
                children: [
                  Text(
                    'امروز چه خوردید؟',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'غذای ایرانی را ثبت کنید و یک برآورد شفاف ببینید.',
                  ),
                  const SizedBox(height: 22),
                  _CapturePanel(
                    isLoading: _isReadingImage,
                    onPressed: _isReadingImage ? null : _showImageSource,
                  ),
                  const SizedBox(height: 26),
                  _DailySummary(
                    calories: _todayCalories,
                    target: target,
                    progress: progress,
                  ),
                  const SizedBox(height: 28),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'وعده‌های امروز',
                          style: Theme.of(context).textTheme.titleLarge
                              ?.copyWith(fontWeight: FontWeight.w800),
                        ),
                      ),
                      Text('${_entries.length} مورد'),
                    ],
                  ),
                  const SizedBox(height: 12),
                  if (_entries.isEmpty)
                    const _EmptyDiary()
                  else
                    ..._entries.map(
                      (entry) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: _DiaryTile(
                          entry: entry,
                          quantityLabel: _formatQuantity(entry.quantity),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CapturePanel extends StatelessWidget {
  const _CapturePanel({required this.isLoading, required this.onPressed});
  final bool isLoading;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: const Color(0xFF17201B),
      borderRadius: BorderRadius.circular(8),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Icon(
          Icons.center_focus_strong,
          color: Color(0xFFF3C969),
          size: 42,
        ),
        const SizedBox(height: 12),
        Text(
          'یک عکس، یک ثبت ساده',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            color: Colors.white,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 6),
        const Text(
          'عکس غذا را بگیرید یا از گالری انتخاب کنید.',
          textAlign: TextAlign.center,
          style: TextStyle(color: Color(0xFFBEC7C1)),
        ),
        const SizedBox(height: 18),
        FilledButton.icon(
          onPressed: onPressed,
          style: FilledButton.styleFrom(
            backgroundColor: const Color(0xFFF3C969),
            foregroundColor: const Color(0xFF17201B),
          ),
          icon: isLoading
              ? const SizedBox.square(
                  dimension: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.photo_camera_outlined),
          label: Text(isLoading ? 'در حال آماده‌سازی...' : 'ثبت غذای جدید'),
        ),
      ],
    ),
  );
}

class _DailySummary extends StatelessWidget {
  const _DailySummary({
    required this.calories,
    required this.target,
    required this.progress,
  });
  final double calories;
  final double target;
  final double progress;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(18),
      child: Column(
        children: [
          Row(
            children: [
              const Icon(Icons.today_outlined),
              const SizedBox(width: 10),
              const Expanded(child: Text('مصرف امروز')),
              Text(
                '${calories.round()} / ${target.round()}',
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
            ],
          ),
          const SizedBox(height: 14),
          LinearProgressIndicator(
            value: progress,
            minHeight: 10,
            borderRadius: BorderRadius.circular(5),
            backgroundColor: const Color(0xFFE4E0D6),
            color: const Color(0xFF237A57),
          ),
        ],
      ),
    ),
  );
}

class _EmptyDiary extends StatelessWidget {
  const _EmptyDiary();
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 28),
    decoration: BoxDecoration(
      border: Border.all(color: const Color(0xFFD5D0C4)),
      borderRadius: BorderRadius.circular(8),
    ),
    child: const Column(
      children: [
        Icon(Icons.restaurant_menu, color: Color(0xFF718078)),
        SizedBox(height: 10),
        Text('هنوز غذایی برای امروز ثبت نشده است.'),
      ],
    ),
  );
}

class _DiaryTile extends StatelessWidget {
  const _DiaryTile({required this.entry, required this.quantityLabel});
  final DiaryEntry entry;
  final String quantityLabel;

  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: const Icon(Icons.ramen_dining_outlined),
      title: Text(
        entry.food.name,
        style: const TextStyle(fontWeight: FontWeight.w800),
      ),
      subtitle: Text(
        '$quantityLabel ${entry.food.portionName}، ${entry.grams.round()} گرم',
      ),
      trailing: Text(
        '${entry.calories.round()} kcal\n${entry.rangeMin.round()}–${entry.rangeMax.round()}',
        textAlign: TextAlign.end,
        style: const TextStyle(fontWeight: FontWeight.w700),
      ),
    ),
  );
}
