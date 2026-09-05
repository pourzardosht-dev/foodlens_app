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
    required this.components,
  });

  final String? foodId;
  final double confidence;
  final bool isFood;
  final bool needsConfirmation;
  final List<RecognizedComponent> components;

  factory RecognitionResult.fromJson(Map<String, dynamic> json) {
    final foodId = json['food_id'] as String?;
    final componentsJson = json['components'] as List<dynamic>?;
    final components = componentsJson
        ?.map(
          (item) => RecognizedComponent.fromJson(item as Map<String, dynamic>),
        )
        .toList(growable: false);
    return RecognitionResult(
      foodId: foodId,
      confidence: (json['confidence'] as num).toDouble(),
      isFood: json['is_food'] as bool,
      needsConfirmation: json['needs_confirmation'] as bool,
      components: components != null && components.isNotEmpty
          ? components
          : foodId == null
          ? const []
          : [
              RecognizedComponent(
                foodId: foodId,
                confidence: (json['confidence'] as num).toDouble(),
                estimatedGrams: null,
              ),
            ],
    );
  }
}

class RecognizedComponent {
  const RecognizedComponent({
    required this.foodId,
    required this.confidence,
    required this.estimatedGrams,
  });

  final String foodId;
  final double confidence;
  final double? estimatedGrams;

  factory RecognizedComponent.fromJson(Map<String, dynamic> json) =>
      RecognizedComponent(
        foodId: json['food_id'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        estimatedGrams: (json['estimated_grams'] as num?)?.toDouble(),
      );
}

class FoodPortion {
  const FoodPortion({
    required this.id,
    required this.name,
    required this.grams,
  });

  final String id;
  final String name;
  final double grams;

  factory FoodPortion.fromJson(Map<String, dynamic> json) => FoodPortion(
    id: json['id'] as String,
    name: json['name_fa'] as String,
    grams: (json['grams'] as num).toDouble(),
  );
}

class FoodCatalogItem {
  const FoodCatalogItem({
    required this.id,
    required this.name,
    required this.kcalPer100g,
    required this.uncertainty,
    required this.defaultPortionId,
    required this.portions,
  });

  final String id;
  final String name;
  final double kcalPer100g;
  final double uncertainty;
  final String defaultPortionId;
  final List<FoodPortion> portions;

  FoodPortion get defaultPortion => portions.firstWhere(
    (portion) => portion.id == defaultPortionId,
    orElse: () => portions.first,
  );

  factory FoodCatalogItem.fromJson(Map<String, dynamic> json) =>
      FoodCatalogItem(
        id: json['id'] as String,
        name: json['name_fa'] as String,
        kcalPer100g: (json['kcal_per_100g'] as num).toDouble(),
        uncertainty: (json['uncertainty_percent'] as num).toDouble() / 100,
        defaultPortionId: json['default_portion_id'] as String,
        portions: (json['portions'] as List<dynamic>)
            .map((item) => FoodPortion.fromJson(item as Map<String, dynamic>))
            .toList(growable: false),
      );
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

  Future<List<FoodCatalogItem>> fetchFoods() async {
    final ownedClient = client == null ? http.Client() : null;
    try {
      final response = await (client ?? ownedClient!).get(
        Uri.parse('$baseUrl/v1/foods'),
      );
      if (response.statusCode != 200) {
        throw RecognitionApiException(
          'Food catalog failed with status ${response.statusCode}',
        );
      }
      final items = jsonDecode(response.body) as List<dynamic>;
      return items
          .map((item) => FoodCatalogItem.fromJson(item as Map<String, dynamic>))
          .toList(growable: false);
    } on RecognitionApiException {
      rethrow;
    } catch (error) {
      throw RecognitionApiException('Food catalog is unavailable: $error');
    } finally {
      ownedClient?.close();
    }
  }

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
