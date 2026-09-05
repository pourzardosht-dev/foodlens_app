import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../recognition/recognition_api.dart';

abstract interface class TokenStore {
  Future<String?> read();
  Future<void> write(String token);
  Future<void> delete();
}

class SecureTokenStore implements TokenStore {
  const SecureTokenStore({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  static const _key = 'foodlens_device_token';
  final FlutterSecureStorage _storage;

  @override
  Future<String?> read() => _storage.read(key: _key);

  @override
  Future<void> write(String token) => _storage.write(key: _key, value: token);

  @override
  Future<void> delete() => _storage.delete(key: _key);
}

class DiaryNutrients {
  const DiaryNutrients({
    required this.kcal,
    required this.protein,
    required this.carbohydrate,
    required this.fat,
    required this.fiber,
  });

  final double? kcal;
  final double? protein;
  final double? carbohydrate;
  final double? fat;
  final double? fiber;

  factory DiaryNutrients.fromJson(Map<String, dynamic> json) => DiaryNutrients(
    kcal: (json['kcal'] as num?)?.toDouble(),
    protein: (json['protein_g'] as num?)?.toDouble(),
    carbohydrate: (json['carb_g'] as num?)?.toDouble(),
    fat: (json['fat_g'] as num?)?.toDouble(),
    fiber: (json['fiber_g'] as num?)?.toDouble(),
  );
}

class PersistedMealComponent {
  const PersistedMealComponent({
    required this.id,
    required this.foodId,
    required this.foodName,
    required this.grams,
    required this.portionCode,
    required this.quantity,
    required this.nutrients,
    required this.uncertaintyPercent,
  });

  final String id;
  final String foodId;
  final String foodName;
  final double grams;
  final String? portionCode;
  final double? quantity;
  final DiaryNutrients nutrients;
  final double uncertaintyPercent;

  factory PersistedMealComponent.fromJson(Map<String, dynamic> json) =>
      PersistedMealComponent(
        id: json['id'] as String,
        foodId: json['food_id'] as String,
        foodName: json['food_name_fa'] as String,
        grams: (json['grams'] as num).toDouble(),
        portionCode: json['portion_code'] as String?,
        quantity: (json['quantity'] as num?)?.toDouble(),
        nutrients: DiaryNutrients.fromJson(
          json['nutrients'] as Map<String, dynamic>,
        ),
        uncertaintyPercent: (json['uncertainty_percent'] as num).toDouble(),
      );
}

class PersistedMeal {
  const PersistedMeal({
    required this.id,
    required this.mealType,
    required this.eatenAt,
    required this.components,
  });

  final String id;
  final String mealType;
  final DateTime eatenAt;
  final List<PersistedMealComponent> components;

  factory PersistedMeal.fromJson(Map<String, dynamic> json) => PersistedMeal(
    id: json['id'] as String,
    mealType: json['meal_type'] as String,
    eatenAt: DateTime.parse(json['eaten_at'] as String),
    components: (json['components'] as List<dynamic>)
        .map(
          (item) =>
              PersistedMealComponent.fromJson(item as Map<String, dynamic>),
        )
        .toList(growable: false),
  );
}

class DiaryDay {
  const DiaryDay({required this.totals, required this.meals});

  final DiaryNutrients totals;
  final List<PersistedMeal> meals;

  factory DiaryDay.fromJson(Map<String, dynamic> json) => DiaryDay(
    totals: DiaryNutrients.fromJson(json['totals'] as Map<String, dynamic>),
    meals: (json['meals'] as List<dynamic>)
        .map((item) => PersistedMeal.fromJson(item as Map<String, dynamic>))
        .toList(growable: false),
  );
}

class MealComponentInput {
  const MealComponentInput({
    required this.foodId,
    required this.grams,
    this.portionCode,
    this.quantity,
    this.recognitionConfidence,
  });

  final String foodId;
  final double grams;
  final String? portionCode;
  final double? quantity;
  final double? recognitionConfidence;

  Map<String, dynamic> toJson() => {
    'food_id': foodId,
    'grams': grams,
    if (portionCode != null) 'portion_code': portionCode,
    if (quantity != null) 'quantity': quantity,
    if (recognitionConfidence != null)
      'recognition_confidence': recognitionConfidence,
  };
}

class PersonalDataApiException implements Exception {
  const PersonalDataApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class PersonalDataApi {
  PersonalDataApi({
    http.Client? client,
    TokenStore? tokenStore,
    this.baseUrl = defaultApiBaseUrl,
  }) : _client = client ?? http.Client(),
       _tokenStore = tokenStore ?? const SecureTokenStore();

  final http.Client _client;
  final TokenStore _tokenStore;
  final String baseUrl;
  String? _token;

  Future<String> ensureProfile() async {
    final existing = _token ?? await _tokenStore.read();
    if (existing != null && existing.isNotEmpty) {
      _token = existing;
      return existing;
    }
    final response = await _client.post(
      Uri.parse('$baseUrl/v1/profiles/anonymous'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({'timezone': 'Asia/Tehran', 'locale': 'fa-IR'}),
    );
    if (response.statusCode != 201) {
      throw PersonalDataApiException(
        'Profile creation failed with status ${response.statusCode}',
      );
    }
    final token =
        (jsonDecode(response.body) as Map<String, dynamic>)['token'] as String;
    await _tokenStore.write(token);
    _token = token;
    return token;
  }

  Future<DiaryDay> fetchDay(DateTime day) async {
    final response = await _authorizedGet(
      Uri.parse(
        '$baseUrl/v1/diary/day',
      ).replace(queryParameters: {'date': _dateOnly(day)}),
    );
    if (response.statusCode != 200) {
      throw PersonalDataApiException(
        'Diary loading failed with status ${response.statusCode}',
      );
    }
    return DiaryDay.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<PersistedMeal> createMeal({
    required String mealType,
    required String source,
    required DateTime eatenAt,
    required List<MealComponentInput> components,
  }) async {
    final response = await _authorizedPost(Uri.parse('$baseUrl/v1/meals'), {
      'meal_type': mealType,
      'source': source,
      'eaten_at': eatenAt.toUtc().toIso8601String(),
      'components': components.map((item) => item.toJson()).toList(),
    });
    if (response.statusCode != 201) {
      throw PersonalDataApiException(
        'Meal creation failed with status ${response.statusCode}',
      );
    }
    return PersistedMeal.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<String> createCustomFood({
    required String name,
    required double kcalPer100g,
  }) async {
    final response =
        await _authorizedPost(Uri.parse('$baseUrl/v1/custom-foods'), {
          'name_fa': name,
          'name_en': 'Custom food',
          'kcal_per_100g': kcalPer100g,
          'portion_name_fa': '۱۰۰ گرم',
          'portion_grams': 100,
        });
    if (response.statusCode != 201) {
      throw PersonalDataApiException(
        'Custom food creation failed with status ${response.statusCode}',
      );
    }
    return (jsonDecode(response.body) as Map<String, dynamic>)['id'] as String;
  }

  Future<void> deleteMeal(String mealId) async {
    final token = await ensureProfile();
    final response = await _client.delete(
      Uri.parse('$baseUrl/v1/meals/$mealId'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode != 204) {
      throw PersonalDataApiException(
        'Meal deletion failed with status ${response.statusCode}',
      );
    }
  }

  Future<PersistedMeal> updateComponent({
    required String mealId,
    required String componentId,
    required MealComponentInput component,
  }) async {
    final token = await ensureProfile();
    final response = await _client.patch(
      Uri.parse('$baseUrl/v1/meals/$mealId/components/$componentId'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(component.toJson()),
    );
    if (response.statusCode != 200) {
      throw PersonalDataApiException(
        'Meal update failed with status ${response.statusCode}',
      );
    }
    return PersistedMeal.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<String> exportProfile() async {
    final response = await _authorizedGet(
      Uri.parse('$baseUrl/v1/profile/export'),
    );
    if (response.statusCode != 200) {
      throw PersonalDataApiException(
        'Profile export failed with status ${response.statusCode}',
      );
    }
    return const JsonEncoder.withIndent(
      '  ',
    ).convert(jsonDecode(response.body));
  }

  Future<void> deleteProfile() async {
    final token = await ensureProfile();
    final response = await _client.delete(
      Uri.parse('$baseUrl/v1/profile'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode != 204) {
      throw PersonalDataApiException(
        'Profile deletion failed with status ${response.statusCode}',
      );
    }
    await _tokenStore.delete();
    _token = null;
  }

  Future<http.Response> _authorizedGet(Uri uri) async {
    final token = await ensureProfile();
    return _client.get(uri, headers: {'Authorization': 'Bearer $token'});
  }

  Future<http.Response> _authorizedPost(
    Uri uri,
    Map<String, dynamic> body,
  ) async {
    final token = await ensureProfile();
    return _client.post(
      uri,
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(body),
    );
  }

  String _dateOnly(DateTime value) =>
      '${value.year.toString().padLeft(4, '0')}-'
      '${value.month.toString().padLeft(2, '0')}-'
      '${value.day.toString().padLeft(2, '0')}';
}
