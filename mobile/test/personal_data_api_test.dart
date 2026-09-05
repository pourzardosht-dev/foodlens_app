import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:foodlens_mobile/features/diary/personal_data_api.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class MemoryTokenStore implements TokenStore {
  String? value;

  @override
  Future<void> delete() async => value = null;

  @override
  Future<String?> read() async => value;

  @override
  Future<void> write(String token) async => value = token;
}

void main() {
  test('creates one profile, stores token, and loads persisted diary', () async {
    final store = MemoryTokenStore();
    var profileRequests = 0;
    final client = MockClient((request) async {
      if (request.url.path == '/v1/profiles/anonymous') {
        profileRequests++;
        return http.Response(jsonEncode({'token': 'device-token'}), 201);
      }
      expect(request.url.path, '/v1/diary/day');
      expect(request.url.queryParameters['date'], '2026-09-05');
      expect(request.headers['authorization'], 'Bearer device-token');
      return http.Response.bytes(
        utf8.encode(jsonEncode({
          'totals': {
            'kcal': 297.0,
            'protein_g': null,
            'carb_g': null,
            'fat_g': null,
            'fiber_g': null,
          },
          'meals': [
            {
              'id': 'meal-1',
              'meal_type': 'lunch',
              'eaten_at': '2026-09-05T09:45:00Z',
              'components': [
                {
                  'id': 'component-1',
                  'food_id': 'ghormeh-sabzi',
                  'food_name_fa': 'قرمه‌سبزی',
                  'grams': 180,
                  'portion_code': 'ladle',
                  'quantity': 1,
                  'nutrients': {
                    'kcal': 297.0,
                    'protein_g': null,
                    'carb_g': null,
                    'fat_g': null,
                    'fiber_g': null,
                  },
                  'uncertainty_percent': 18,
                },
              ],
            },
          ],
        })),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final api = PersonalDataApi(
      client: client,
      tokenStore: store,
      baseUrl: 'https://api.example.test',
    );

    final diary = await api.fetchDay(DateTime(2026, 9, 5));
    await api.ensureProfile();

    expect(profileRequests, 1);
    expect(store.value, 'device-token');
    expect(diary.totals.kcal, 297);
    expect(diary.meals.single.components.single.foodId, 'ghormeh-sabzi');
  });

  test('posts a multi-component meal with authorization', () async {
    final store = MemoryTokenStore()..value = 'existing-token';
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path, '/v1/meals');
      expect(request.headers['authorization'], 'Bearer existing-token');
      final body = jsonDecode(request.body) as Map<String, dynamic>;
      expect(body['meal_type'], 'dinner');
      expect(body['eaten_at'], endsWith('Z'));
      expect(body['components'], hasLength(2));
      return http.Response.bytes(
        utf8.encode(jsonEncode({
          'id': 'meal-2',
          'meal_type': 'dinner',
          'eaten_at': body['eaten_at'],
          'components': [
            {
              'id': 'component-1',
              'food_id': 'cooked-rice',
              'food_name_fa': 'برنج پخته',
              'grams': 200,
              'portion_code': 'scoop',
              'quantity': 2,
              'nutrients': {
                'kcal': 260,
                'protein_g': null,
                'carb_g': null,
                'fat_g': null,
                'fiber_g': null,
              },
              'uncertainty_percent': 10,
            },
          ],
        })),
        201,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final api = PersonalDataApi(
      client: client,
      tokenStore: store,
      baseUrl: 'https://api.example.test',
    );

    final meal = await api.createMeal(
      mealType: 'dinner',
      source: 'photo',
      eatenAt: DateTime(2026, 9, 5, 20),
      components: const [
        MealComponentInput(
          foodId: 'cooked-rice',
          grams: 200,
          portionCode: 'scoop',
          quantity: 2,
        ),
        MealComponentInput(foodId: 'ghormeh-sabzi', grams: 180),
      ],
    );

    expect(meal.id, 'meal-2');
    expect(meal.components.single.nutrients.kcal, 260);
  });
}
