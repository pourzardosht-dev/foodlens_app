import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

const defaultApiBaseUrl = String.fromEnvironment(
  'FOODLENS_API_URL',
  defaultValue: 'http://127.0.0.1:8000',
);

class RecognitionResult {
  const RecognitionResult({
    required this.foodId,
    required this.confidence,
    required this.isFood,
    required this.needsConfirmation,
  });

  final String? foodId;
  final double confidence;
  final bool isFood;
  final bool needsConfirmation;

  factory RecognitionResult.fromJson(Map<String, dynamic> json) {
    return RecognitionResult(
      foodId: json['food_id'] as String?,
      confidence: (json['confidence'] as num).toDouble(),
      isFood: json['is_food'] as bool,
      needsConfirmation: json['needs_confirmation'] as bool,
    );
  }
}

class RecognitionApiException implements Exception {
  const RecognitionApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class RecognitionApi {
  const RecognitionApi({this.client, this.baseUrl = defaultApiBaseUrl});

  final http.Client? client;
  final String baseUrl;

  Future<RecognitionResult> recognize(XFile image) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/v1/recognition'),
    );
    request.files.add(
      http.MultipartFile.fromBytes(
        'image',
        await image.readAsBytes(),
        filename: image.name.isEmpty ? 'upload.jpg' : image.name,
      ),
    );

    final ownedClient = client == null ? http.Client() : null;
    try {
      final response = await (client ?? ownedClient!).send(request);
      final responseBody = await response.stream.bytesToString();
      if (response.statusCode != 200) {
        throw RecognitionApiException(
          'Recognition failed with status ${response.statusCode}',
        );
      }
      return RecognitionResult.fromJson(
        jsonDecode(responseBody) as Map<String, dynamic>,
      );
    } on RecognitionApiException {
      rethrow;
    } catch (error) {
      throw RecognitionApiException('Recognition API is unavailable: $error');
    } finally {
      ownedClient?.close();
    }
  }
}
