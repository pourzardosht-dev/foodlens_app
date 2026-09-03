import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:image_picker/image_picker.dart';
import 'package:foodlens_mobile/features/recognition/recognition_api.dart';

void main() {
  test('uploads an image and parses recognition result', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.toString(), 'https://api.example.test/v1/recognition');
      expect(request.headers['content-type'], startsWith('multipart/form-data;'));
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
  });
}