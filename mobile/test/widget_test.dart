// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:foodlens_mobile/features/diary/personal_data_api.dart';
import 'package:foodlens_mobile/features/home/home_screen.dart';
import 'package:foodlens_mobile/features/recognition/recognition_api.dart';

class _FakeRecognitionApi extends RecognitionApi {
  const _FakeRecognitionApi();

  @override
  Future<List<FoodCatalogItem>> fetchFoods() async => const [
    FoodCatalogItem(
      id: 'test-food',
      name: 'غذای آزمایشی',
      kcalPer100g: 100,
      uncertainty: .1,
      defaultPortionId: '100g',
      portions: [FoodPortion(id: '100g', name: '۱۰۰ گرم', grams: 100)],
    ),
  ];
}

class _FakePersonalDataApi extends PersonalDataApi {
  @override
  Future<DiaryDay> fetchDay(DateTime day) async => const DiaryDay(
    totals: DiaryNutrients(
      kcal: 0,
      protein: 0,
      carbohydrate: 0,
      fat: 0,
      fiber: 0,
    ),
    meals: [],
  );
}

void main() {
  testWidgets('shows the FoodLens daily diary dashboard', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: HomeScreen(
            recognitionApi: const _FakeRecognitionApi(),
            personalDataApi: _FakePersonalDataApi(),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('امروز چه خوردید؟'), findsOneWidget);
    expect(find.text('ثبت غذای جدید'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('هنوز غذایی برای امروز ثبت نشده است.'),
      300,
      scrollable: find.byType(Scrollable),
    );
    expect(find.text('هنوز غذایی برای امروز ثبت نشده است.'), findsOneWidget);
  });

  test('converts a manually entered pot weight to food portions', () {
    expect(quantityForGrams(grams: 2400, portionGrams: 400), 6);
  });

  test('creates a manually named food with a 100 gram base portion', () {
    final food = manualFoodCatalogItem(
      name: '  غذای خانگی  ',
      kcalPer100g: 175,
    );

    expect(food.name, 'غذای خانگی');
    expect(food.kcalPer100g, 175);
    expect(food.defaultPortion.grams, 100);
    expect(food.uncertainty, .30);
  });
}
