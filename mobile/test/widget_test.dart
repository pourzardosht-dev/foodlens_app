// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';

import 'package:foodlens_mobile/app.dart';
import 'package:foodlens_mobile/features/home/home_screen.dart';

void main() {
  testWidgets('shows the FoodLens daily diary dashboard', (tester) async {
    await tester.pumpWidget(const FoodLensApp());
    await tester.pumpAndSettle();

    expect(find.text('امروز چه خوردید؟'), findsOneWidget);
    expect(find.text('ثبت غذای جدید'), findsOneWidget);
    expect(find.text('هنوز غذایی برای امروز ثبت نشده است.'), findsOneWidget);
  });

  test('converts a manually entered pot weight to food portions', () {
    expect(quantityForGrams(grams: 2400, portionGrams: 400), 6);
  });
}
