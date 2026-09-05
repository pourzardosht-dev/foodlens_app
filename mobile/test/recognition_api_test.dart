import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:image_picker/image_picker.dart';
import 'package:foodlens_mobile/features/recognition/recognition_api.dart';

void main() {
  test('loads the food catalog with nutrition and default portion', () async {
    final client = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.toString(), 'https://api.example.test/v1/foods');
      return http.Response(
        jsonEncode([
          {
            'id': 'gheimeh',
            'name_fa': 'خورش قیمه',
            'name_en': 'Gheimeh',
            'kcal_per_100g': 180,
            'uncertainty_percent': 22,
            'default_portion_id': 'ladle',
            'portions': [
              {'id': 'tablespoon', 'name_fa': 'قاشق غذاخوری', 'grams': 25},
              {'id': 'ladle', 'name_fa': 'ملاقه', 'grams': 180},
            ],
          },
        ]),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final api = RecognitionApi(
      client: client,
      baseUrl: 'https://api.example.test',
    );

    final foods = await api.fetchFoods();

    expect(foods, hasLength(1));
    expect(foods.single.name, 'خورش قیمه');
    expect(foods.single.kcalPer100g, 180);
    expect(foods.single.uncertainty, 0.22);
    expect(foods.single.defaultPortion.name, 'ملاقه');
  });

  test('uploads an image and parses recognition result', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.toString(), 'https://api.example.test/v1/recognition');
      expect(
        request.headers['content-type'],
        startsWith('multipart/form-data;'),
      );
      final body = utf8.decode(request.bodyBytes, allowMalformed: true);
      expect(body, contains('name="image"'));
      expect(body, contains('filename="upload.jpg"'));

      return http.Response(
        jsonEncode({
          'food_id': 'fesenjan',
          'confidence': 0.92,
          'is_food': true,
          'needs_confirmation': false,
          'alternatives': <Object>[],
          'components': [
            {
              'food_id': 'cooked-rice',
              'confidence': 0.89,
              'estimated_grams': 250,
            },
            {'food_id': 'fesenjan', 'confidence': 0.92, 'estimated_grams': 180},
          ],
        }),
        200,
      );
    });
    final api = RecognitionApi(
      client: client,
      baseUrl: 'https://api.example.test',
    );
    final image = XFile.fromData(
      Uint8List.fromList([0xFF, 0xD8, 0xFF, 0xD9]),
      name: 'food.jpg',
      mimeType: 'image/jpeg',
    );

    final result = await api.recognize(image);

    expect(result.foodId, 'fesenjan');
    expect(result.confidence, 0.92);
    expect(result.needsConfirmation, isFalse);
    expect(result.components, hasLength(2));
    expect(result.components.first.foodId, 'cooked-rice');
    expect(result.components.first.estimatedGrams, 250);
  });

  test('converts a legacy recognition response to one component', () async {
    final client = MockClient(
      (_) async => http.Response(
        jsonEncode({
          'food_id': 'fesenjan',
          'confidence': 0.92,
          'is_food': true,
          'needs_confirmation': false,
          'alternatives': <Object>[],
        }),
        200,
      ),
    );
    final api = RecognitionApi(
      client: client,
      baseUrl: 'https://api.example.test',
    );
    final image = XFile.fromData(Uint8List(1), name: 'food.jpg');

    final result = await api.recognize(image);

    expect(result.components, hasLength(1));
    expect(result.components.single.foodId, 'fesenjan');
    expect(result.components.single.estimatedGrams, isNull);
  });
}
