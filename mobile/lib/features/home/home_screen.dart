import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../diary/personal_data_api.dart';
import '../recognition/recognition_api.dart';

class DiaryEntry {
  const DiaryEntry({
    required this.food,
    required this.portion,
    required this.quantity,
    required this.grams,
    required this.calories,
    required this.rangeMin,
    required this.rangeMax,
    this.mealId,
    this.componentId,
    this.mealType = 'snack',
    this.confidence,
  });

  final FoodCatalogItem food;
  final FoodPortion portion;
  final double quantity;
  final double grams;
  final double calories;
  final double rangeMin;
  final double rangeMax;
  final String? mealId;
  final String? componentId;
  final String mealType;
  final double? confidence;
}

class _MealDraftResult {
  const _MealDraftResult({required this.mealType, required this.entries});

  final String mealType;
  final List<DiaryEntry> entries;
}

class _PlateComponentDraft {
  _PlateComponentDraft({
    required this.food,
    required this.portion,
    required this.quantity,
    required this.confidence,
  });

  FoodCatalogItem food;
  FoodPortion portion;
  double quantity;
  final double? confidence;
  int fieldRevision = 0;
}

double quantityForGrams({
  required double grams,
  required double portionGrams,
}) => grams / portionGrams;

const _manualFoodChoice = FoodCatalogItem(
  id: 'manual-food-choice',
  name: 'غذا در فهرست نیست؛ ورود دستی',
  kcalPer100g: 0,
  uncertainty: 0,
  defaultPortionId: 'manual-100g',
  portions: [FoodPortion(id: 'manual-100g', name: '۱۰۰ گرم', grams: 100)],
  nutritionStatus: 'user_provided',
);

FoodCatalogItem manualFoodCatalogItem({
  required String name,
  required double kcalPer100g,
}) => FoodCatalogItem(
  id: 'manual-food',
  name: name.trim(),
  kcalPer100g: kcalPer100g,
  uncertainty: .30,
  defaultPortionId: 'manual-100g',
  portions: const [FoodPortion(id: 'manual-100g', name: '۱۰۰ گرم', grams: 100)],
  nutritionStatus: 'user_provided',
);

class HomeScreen extends StatefulWidget {
  const HomeScreen({
    super.key,
    this.recognitionApi = const RecognitionApi(),
    this.personalDataApi,
  });

  final RecognitionApi recognitionApi;
  final PersonalDataApi? personalDataApi;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _picker = ImagePicker();
  final _entries = <DiaryEntry>[];
  late final PersonalDataApi _personalDataApi;
  List<FoodCatalogItem> _foods = const [];
  DateTime _selectedDay = DateTime.now();
  DiaryNutrients? _dailyNutrients;
  Uint8List? _selectedImage;
  bool _isReadingImage = false;
  bool _isLoadingDiary = false;
  bool _isSavingMeal = false;

  double get _todayCalories =>
      _entries.fold(0, (sum, item) => sum + item.calories);

  @override
  void initState() {
    super.initState();
    _personalDataApi = widget.personalDataApi ?? PersonalDataApi();
    _loadDiary();
  }

  Future<void> _loadDiary() async {
    if (mounted) setState(() => _isLoadingDiary = true);
    try {
      if (!await _ensureFoodCatalog()) return;
      final diary = await _personalDataApi.fetchDay(_selectedDay);
      if (!mounted) return;
      setState(() {
        _dailyNutrients = diary.totals;
        _entries
          ..clear()
          ..addAll(
            diary.meals.expand(
              (meal) => meal.components.map(
                (component) => _entryFromPersisted(meal, component),
              ),
            ),
          );
      });
    } on PersonalDataApiException {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'دفتر آنلاین در دسترس نیست؛ تشخیص غذا همچنان فعال است.',
            ),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoadingDiary = false);
    }
  }

  DiaryEntry _entryFromPersisted(
    PersistedMeal meal,
    PersistedMealComponent component,
  ) {
    final knownFood = _foodById(component.foodId);
    final calories = component.nutrients.kcal ?? 0;
    final uncertainty = component.uncertaintyPercent / 100;
    final portion = knownFood?.portions.cast<FoodPortion?>().firstWhere(
      (item) => item?.id == component.portionCode,
      orElse: () => null,
    );
    final resolvedPortion =
        portion ??
        FoodPortion(
          id: component.portionCode ?? 'recorded-grams',
          name: 'مقدار ثبت‌شده',
          grams: component.quantity == null
              ? component.grams
              : component.grams / component.quantity!,
        );
    final food =
        knownFood ??
        FoodCatalogItem(
          id: component.foodId,
          name: component.foodName,
          kcalPer100g: component.grams == 0
              ? 0
              : calories * 100 / component.grams,
          uncertainty: uncertainty,
          defaultPortionId: resolvedPortion.id,
          portions: [resolvedPortion],
          nutritionStatus: 'user_provided',
        );
    return DiaryEntry(
      food: food,
      portion: resolvedPortion,
      quantity: component.quantity ?? component.grams / resolvedPortion.grams,
      grams: component.grams,
      calories: calories,
      rangeMin: calories * (1 - uncertainty),
      rangeMax: calories * (1 + uncertainty),
      mealId: meal.id,
      componentId: component.id,
      mealType: meal.mealType,
    );
  }

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
      if (!await _ensureFoodCatalog()) return;
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

  Future<bool> _ensureFoodCatalog() async {
    if (_foods.isNotEmpty) return true;
    try {
      final foods = await widget.recognitionApi.fetchFoods();
      if (!mounted) return false;
      if (foods.isEmpty) {
        throw const RecognitionApiException('Food catalog is empty');
      }
      setState(() => _foods = foods);
      return true;
    } on RecognitionApiException {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('فهرست غذاها دریافت نشد؛ دوباره تلاش کنید.'),
          ),
        );
      }
      return false;
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
    final drafts = <_PlateComponentDraft>[];
    var mealType = 'lunch';
    for (final component in recognition?.components ?? const []) {
      final food = _foodById(component.foodId);
      if (food == null) continue;
      final portion = food.defaultPortion;
      drafts.add(
        _PlateComponentDraft(
          food: food,
          portion: portion,
          quantity: component.estimatedGrams == null
              ? 1
              : quantityForGrams(
                  grams: component.estimatedGrams!,
                  portionGrams: portion.grams,
                ),
          confidence: component.confidence,
        ),
      );
    }
    final result = await showModalBottomSheet<_MealDraftResult>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) {
          final totalCalories = drafts.fold<double>(
            0,
            (sum, draft) =>
                sum +
                draft.portion.grams *
                    draft.quantity *
                    draft.food.kcalPer100g /
                    100,
          );
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
                    'اجزای بشقاب',
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
                  if (drafts.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: Text(
                        'جزء قابل تشخیصی پیدا نشد. غذاهای بشقاب را اضافه کنید.',
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ...drafts.asMap().entries.map((item) {
                    final index = item.key;
                    final draft = item.value;
                    final grams = draft.portion.grams * draft.quantity;
                    final calories = grams * draft.food.kcalPer100g / 100;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Column(
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      'جزء ${index + 1}',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                  ),
                                  if (draft.confidence case final confidence?)
                                    Text(
                                      '${(confidence * 100).round()}٪ اطمینان',
                                    ),
                                  IconButton(
                                    tooltip: 'حذف جزء',
                                    onPressed: () => setSheetState(
                                      () => drafts.removeAt(index),
                                    ),
                                    icon: const Icon(Icons.delete_outline),
                                  ),
                                ],
                              ),
                              DropdownButtonFormField<FoodCatalogItem>(
                                key: ValueKey(
                                  'component-$index-${draft.fieldRevision}-${draft.food.id}',
                                ),
                                initialValue: draft.food,
                                decoration: const InputDecoration(
                                  labelText: 'غذا',
                                  border: OutlineInputBorder(),
                                ),
                                items:
                                    [
                                          _manualFoodChoice,
                                          if (draft.food.id == 'manual-food')
                                            draft.food,
                                          ..._foods,
                                        ]
                                        .map(
                                          (food) => DropdownMenuItem(
                                            value: food,
                                            child: Text(
                                              food.isEstimated
                                                  ? '${food.name} · برآوردی'
                                                  : food.name,
                                            ),
                                          ),
                                        )
                                        .toList(),
                                onChanged: (food) async {
                                  var selected = food;
                                  if (food == _manualFoodChoice) {
                                    selected = await _createManualFood(context);
                                    if (!context.mounted) return;
                                  }
                                  setSheetState(() {
                                    draft.fieldRevision++;
                                    if (selected != null) {
                                      draft.food = selected;
                                      draft.portion = selected.defaultPortion;
                                      draft.quantity = 1;
                                    }
                                  });
                                },
                              ),
                              const SizedBox(height: 12),
                              DropdownButtonFormField<FoodPortion>(
                                key: ValueKey(
                                  'component-portion-$index-${draft.food.id}',
                                ),
                                initialValue: draft.portion,
                                decoration: const InputDecoration(
                                  labelText: 'واحد اندازه‌گیری',
                                  border: OutlineInputBorder(),
                                ),
                                items: draft.food.portions
                                    .map(
                                      (portion) => DropdownMenuItem(
                                        value: portion,
                                        child: Text(portion.name),
                                      ),
                                    )
                                    .toList(),
                                onChanged: (portion) {
                                  if (portion != null) {
                                    setSheetState(() {
                                      draft.portion = portion;
                                      draft.quantity = 1;
                                    });
                                  }
                                },
                              ),
                              const SizedBox(height: 12),
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      '${grams.round()} گرم · ${calories.round()} کیلوکالری',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                  ),
                                  IconButton.outlined(
                                    tooltip: 'ویرایش وزن',
                                    onPressed: () async {
                                      final edited = await _editPortionWeight(
                                        context,
                                        initialGrams: grams,
                                      );
                                      if (edited != null) {
                                        setSheetState(
                                          () =>
                                              draft.quantity = quantityForGrams(
                                                grams: edited,
                                                portionGrams:
                                                    draft.portion.grams,
                                              ),
                                        );
                                      }
                                    },
                                    icon: const Icon(Icons.scale_outlined),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }),
                  OutlinedButton.icon(
                    onPressed: drafts.length >= 8
                        ? null
                        : () async {
                            final food = await _selectFood(context);
                            if (food != null) {
                              setSheetState(
                                () => drafts.add(
                                  _PlateComponentDraft(
                                    food: food,
                                    portion: food.defaultPortion,
                                    quantity: 1,
                                    confidence: null,
                                  ),
                                ),
                              );
                            }
                          },
                    icon: const Icon(Icons.add),
                    label: const Text('افزودن جزء دیگر'),
                  ),
                  if (drafts.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      initialValue: mealType,
                      decoration: const InputDecoration(
                        labelText: 'نوع وعده',
                        border: OutlineInputBorder(),
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'breakfast',
                          child: Text('صبحانه'),
                        ),
                        DropdownMenuItem(value: 'lunch', child: Text('ناهار')),
                        DropdownMenuItem(value: 'dinner', child: Text('شام')),
                        DropdownMenuItem(
                          value: 'snack',
                          child: Text('میان‌وعده'),
                        ),
                      ],
                      onChanged: (value) {
                        if (value != null) {
                          setSheetState(() => mealType = value);
                        }
                      },
                    ),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(16),
                      color: const Color(0xFFE4EFE9),
                      child: Text(
                        'مجموع بشقاب: ${totalCalories.round()} کیلوکالری',
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                    ),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: () => Navigator.pop(
                        context,
                        _MealDraftResult(
                          mealType: mealType,
                          entries: drafts
                              .map((draft) {
                                final grams =
                                    draft.portion.grams * draft.quantity;
                                final calories =
                                    grams * draft.food.kcalPer100g / 100;
                                return DiaryEntry(
                                  food: draft.food,
                                  portion: draft.portion,
                                  quantity: draft.quantity,
                                  grams: grams,
                                  calories: calories,
                                  rangeMin:
                                      calories * (1 - draft.food.uncertainty),
                                  rangeMax:
                                      calories * (1 + draft.food.uncertainty),
                                  mealType: mealType,
                                  confidence: draft.confidence,
                                );
                              })
                              .toList(growable: false),
                        ),
                      ),
                      icon: const Icon(Icons.check),
                      label: Text('ثبت ${drafts.length} جزء در وعده امروز'),
                    ),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
    if (result != null && mounted) {
      await _persistMeal(result);
    }
  }

  Future<void> _persistMeal(_MealDraftResult result) async {
    setState(() => _isSavingMeal = true);
    try {
      final components = <MealComponentInput>[];
      for (final entry in result.entries) {
        var foodId = entry.food.id;
        if (foodId == 'manual-food') {
          foodId = await _personalDataApi.createCustomFood(
            name: entry.food.name,
            kcalPer100g: entry.food.kcalPer100g,
          );
        }
        components.add(
          MealComponentInput(
            foodId: foodId,
            grams: entry.grams,
            portionCode: entry.portion.id,
            quantity: entry.quantity,
            recognitionConfidence: entry.confidence,
          ),
        );
      }
      await _personalDataApi.createMeal(
        mealType: result.mealType,
        source: 'photo',
        eatenAt: DateTime(
          _selectedDay.year,
          _selectedDay.month,
          _selectedDay.day,
          DateTime.now().hour,
          DateTime.now().minute,
        ),
        components: components,
      );
      await _loadDiary();
    } on PersonalDataApiException {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('وعده ذخیره نشد؛ دوباره تلاش کنید.')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSavingMeal = false);
    }
  }

  FoodCatalogItem? _foodById(String foodId) => _foods
      .cast<FoodCatalogItem?>()
      .firstWhere((food) => food?.id == foodId, orElse: () => null);

  Future<FoodCatalogItem?> _selectFood(BuildContext context) async {
    final selected = await showDialog<FoodCatalogItem>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('افزودن جزء بشقاب'),
        children: [
          SimpleDialogOption(
            onPressed: () => Navigator.pop(context, _manualFoodChoice),
            child: const Row(
              children: [
                Icon(Icons.edit_outlined),
                SizedBox(width: 10),
                Text('ورود نام غذا به‌صورت دستی'),
              ],
            ),
          ),
          ..._foods.map(
            (food) => SimpleDialogOption(
              onPressed: () => Navigator.pop(context, food),
              child: Text(food.name),
            ),
          ),
        ],
      ),
    );
    if (selected == _manualFoodChoice && context.mounted) {
      return _createManualFood(context);
    }
    return selected;
  }

  String _formatQuantity(double value) => value == value.roundToDouble()
      ? value.toInt().toString()
      : value.toStringAsFixed(1);

  Future<FoodCatalogItem?> _createManualFood(BuildContext context) async {
    final nameController = TextEditingController();
    final caloriesController = TextEditingController();
    String? nameError;
    String? caloriesError;
    final result = await showDialog<FoodCatalogItem>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('ورود دستی غذا'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                key: const Key('manual-food-name-input'),
                controller: nameController,
                autofocus: true,
                textInputAction: TextInputAction.next,
                decoration: InputDecoration(
                  labelText: 'نام غذا',
                  hintText: 'مثلاً خوراک خانگی',
                  errorText: nameError,
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                key: const Key('manual-food-calories-input'),
                controller: caloriesController,
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                decoration: InputDecoration(
                  labelText: 'کالری تقریبی در ۱۰۰ گرم',
                  suffixText: 'kcal',
                  helperText: 'برای محاسبه کالری و ثبت وعده لازم است.',
                  errorText: caloriesError,
                  border: const OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('انصراف'),
            ),
            FilledButton(
              onPressed: () {
                final name = nameController.text.trim();
                final calories = double.tryParse(
                  caloriesController.text.trim().replaceAll(',', '.'),
                );
                final validName = name.isNotEmpty && name.length <= 80;
                final validCalories =
                    calories != null && calories > 0 && calories <= 2000;
                if (!validName || !validCalories) {
                  setDialogState(() {
                    nameError = validName
                        ? null
                        : 'نام غذا را در حداکثر ۸۰ نویسه وارد کنید.';
                    caloriesError = validCalories
                        ? null
                        : 'عددی بین ۱ تا ۲۰۰۰ وارد کنید.';
                  });
                  return;
                }
                Navigator.pop(
                  context,
                  manualFoodCatalogItem(name: name, kcalPer100g: calories),
                );
              },
              child: const Text('ثبت غذا'),
            ),
          ],
        ),
      ),
    );
    nameController.dispose();
    caloriesController.dispose();
    return result;
  }

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

  Future<void> _deleteMeal(String mealId) async {
    setState(() => _isSavingMeal = true);
    try {
      await _personalDataApi.deleteMeal(mealId);
      await _loadDiary();
    } on PersonalDataApiException {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('حذف وعده انجام نشد.')));
      }
    } finally {
      if (mounted) setState(() => _isSavingMeal = false);
    }
  }

  Future<void> _editEntry(DiaryEntry entry) async {
    if (entry.mealId == null || entry.componentId == null) return;
    final grams = await _editPortionWeight(context, initialGrams: entry.grams);
    if (grams == null || !mounted) return;
    setState(() => _isSavingMeal = true);
    try {
      await _personalDataApi.updateComponent(
        mealId: entry.mealId!,
        componentId: entry.componentId!,
        component: MealComponentInput(
          foodId: entry.food.id,
          grams: grams,
          portionCode: entry.portion.id,
          quantity: grams / entry.portion.grams,
        ),
      );
      await _loadDiary();
    } on PersonalDataApiException {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('ویرایش وعده انجام نشد.')));
      }
    } finally {
      if (mounted) setState(() => _isSavingMeal = false);
    }
  }

  Future<void> _changeDay(int offset) async {
    setState(() => _selectedDay = _selectedDay.add(Duration(days: offset)));
    await _loadDiary();
  }

  Future<void> _showProfile() async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'داده‌های من',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              const Text(
                'این پروفایل ناشناس به همین دستگاه وابسته است. پاک‌کردن داده‌های مرورگر ممکن است دسترسی را از بین ببرد.',
              ),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                icon: const Icon(Icons.download_outlined),
                label: const Text('نمایش خروجی JSON'),
                onPressed: () async {
                  try {
                    final data = await _personalDataApi.exportProfile();
                    if (!sheetContext.mounted) return;
                    await showDialog<void>(
                      context: sheetContext,
                      builder: (context) => AlertDialog(
                        title: const Text('خروجی اطلاعات'),
                        content: SizedBox(
                          width: 520,
                          child: SingleChildScrollView(
                            child: SelectableText(data),
                          ),
                        ),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(context),
                            child: const Text('بستن'),
                          ),
                        ],
                      ),
                    );
                  } on PersonalDataApiException {
                    if (sheetContext.mounted) {
                      ScaffoldMessenger.of(sheetContext).showSnackBar(
                        const SnackBar(
                          content: Text('دریافت خروجی انجام نشد.'),
                        ),
                      );
                    }
                  }
                },
              ),
              TextButton.icon(
                icon: const Icon(Icons.delete_forever_outlined),
                label: const Text('حذف کامل اطلاعات'),
                style: TextButton.styleFrom(
                  foregroundColor: Colors.red.shade700,
                ),
                onPressed: () async {
                  final confirmed = await showDialog<bool>(
                    context: sheetContext,
                    builder: (context) => AlertDialog(
                      title: const Text('حذف کامل اطلاعات؟'),
                      content: const Text('این عملیات قابل بازگشت نیست.'),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context, false),
                          child: const Text('انصراف'),
                        ),
                        FilledButton(
                          onPressed: () => Navigator.pop(context, true),
                          child: const Text('حذف'),
                        ),
                      ],
                    ),
                  );
                  if (confirmed != true) return;
                  try {
                    await _personalDataApi.deleteProfile();
                    if (!sheetContext.mounted) return;
                    Navigator.pop(sheetContext);
                    if (mounted) {
                      setState(() {
                        _entries.clear();
                        _dailyNutrients = null;
                      });
                    }
                  } on PersonalDataApiException {
                    if (sheetContext.mounted) {
                      ScaffoldMessenger.of(sheetContext).showSnackBar(
                        const SnackBar(content: Text('حذف اطلاعات انجام نشد.')),
                      );
                    }
                  }
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _mealTypeLabel(String value) => switch (value) {
    'breakfast' => 'صبحانه',
    'lunch' => 'ناهار',
    'dinner' => 'شام',
    _ => 'میان‌وعده',
  };

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
            onPressed: _showProfile,
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
                  const SizedBox(height: 14),
                  Row(
                    children: [
                      IconButton(
                        tooltip: 'روز قبل',
                        onPressed: _isLoadingDiary
                            ? null
                            : () => _changeDay(-1),
                        icon: const Icon(Icons.chevron_right),
                      ),
                      Expanded(
                        child: Text(
                          '${_selectedDay.year}/${_selectedDay.month.toString().padLeft(2, '0')}/${_selectedDay.day.toString().padLeft(2, '0')}',
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontWeight: FontWeight.w800),
                        ),
                      ),
                      IconButton(
                        tooltip: 'روز بعد',
                        onPressed: _isLoadingDiary ? null : () => _changeDay(1),
                        icon: const Icon(Icons.chevron_left),
                      ),
                    ],
                  ),
                  const SizedBox(height: 22),
                  _CapturePanel(
                    isLoading: _isReadingImage || _isSavingMeal,
                    onPressed: _isReadingImage || _isSavingMeal
                        ? null
                        : _showImageSource,
                  ),
                  if (_isLoadingDiary) ...[
                    const SizedBox(height: 12),
                    const LinearProgressIndicator(),
                  ],
                  const SizedBox(height: 26),
                  _DailySummary(
                    calories: _todayCalories,
                    target: target,
                    progress: progress,
                    nutrients: _dailyNutrients,
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
                          mealTypeLabel: _mealTypeLabel(entry.mealType),
                          onEdit: entry.componentId == null || _isSavingMeal
                              ? null
                              : () => _editEntry(entry),
                          onDelete: entry.mealId == null || _isSavingMeal
                              ? null
                              : () => _deleteMeal(entry.mealId!),
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
    required this.nutrients,
  });
  final double calories;
  final double target;
  final double progress;
  final DiaryNutrients? nutrients;

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
          if (nutrients != null) ...[
            const SizedBox(height: 14),
            Wrap(
              spacing: 16,
              runSpacing: 8,
              children: [
                Text('پروتئین: ${_macro(nutrients!.protein)}'),
                Text('کربوهیدرات: ${_macro(nutrients!.carbohydrate)}'),
                Text('چربی: ${_macro(nutrients!.fat)}'),
                Text('فیبر: ${_macro(nutrients!.fiber)}'),
              ],
            ),
          ],
        ],
      ),
    ),
  );

  String _macro(double? value) =>
      value == null ? 'نامشخص' : '${value.toStringAsFixed(1)} g';
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
  const _DiaryTile({
    required this.entry,
    required this.quantityLabel,
    required this.mealTypeLabel,
    required this.onEdit,
    required this.onDelete,
  });
  final DiaryEntry entry;
  final String quantityLabel;
  final String mealTypeLabel;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: const Icon(Icons.ramen_dining_outlined),
      title: Row(
        children: [
          Flexible(
            child: Text(
              entry.food.name,
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
          ),
          if (entry.food.isEstimated) ...[
            const SizedBox(width: 8),
            const Text(
              'برآوردی',
              style: TextStyle(fontSize: 11, color: Color(0xFF7A5B00)),
            ),
          ],
        ],
      ),
      subtitle: Text(
        '$mealTypeLabel · $quantityLabel ${entry.portion.name}، ${entry.grams.round()} گرم',
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '${entry.calories.round()} kcal\n${entry.rangeMin.round()}–${entry.rangeMax.round()}',
            textAlign: TextAlign.end,
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
          IconButton(
            tooltip: 'ویرایش وزن',
            onPressed: onEdit,
            icon: const Icon(Icons.edit_outlined),
          ),
          IconButton(
            tooltip: 'حذف وعده',
            onPressed: onDelete,
            icon: const Icon(Icons.delete_outline),
          ),
        ],
      ),
    ),
  );
}
