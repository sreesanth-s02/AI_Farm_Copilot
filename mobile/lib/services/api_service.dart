import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../app_theme.dart';
import '../models/fertiliser_recommendation.dart';

class ApiService {
  const ApiService({this.baseUrl = apiBaseUrl});

  final String baseUrl;

  Future<Map<String, dynamic>> getObject(String path) async {
    final response = await http
        .get(Uri.parse('$baseUrl$path'))
        .timeout(const Duration(seconds: 25));
    return _decodeObject(response, path);
  }

  Future<List<Map<String, dynamic>>> getList(String path) async {
    final response = await http
        .get(Uri.parse('$baseUrl$path'))
        .timeout(const Duration(seconds: 25));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException('API returned HTTP ${response.statusCode}');
    }

    final decoded = jsonDecode(response.body);
    if (decoded is List) {
      return decoded
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    }
    throw ApiException('Unexpected response format from $path');
  }

  Future<FertiliserRecommendation> getFertiliserAssessment(int fieldId) async {
    final response =
        await getObject('/api/v1/recommendations/fertiliser/$fieldId');
    return FertiliserRecommendation.fromJson(response);
  }

  Future<Map<String, dynamic>> predictDisease({
    required Uint8List bytes,
    required String filename,
    required MediaType contentType,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/disease/predict'),
    )..files.add(http.MultipartFile.fromBytes(
        'image',
        bytes,
        filename: filename,
        contentType: contentType,
      ));
    final streamedResponse =
        await request.send().timeout(const Duration(seconds: 90));
    final response = await http.Response.fromStream(streamedResponse);
    final decoded = jsonDecode(response.body);
    final body = decoded is Map<String, dynamic>
        ? decoded
        : <String, dynamic>{};
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = body['detail'];
      throw ApiException(
        detail is String
            ? detail
            : 'The server could not analyze this image '
                '(HTTP ${response.statusCode}).',
      );
    }
    return body;
  }

  Map<String, dynamic> _decodeObject(http.Response response, String path) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException('API returned HTTP ${response.statusCode}');
    }
    final decoded = jsonDecode(response.body);
    if (decoded is Map<String, dynamic>) return decoded;
    throw ApiException('Unexpected response format from $path');
  }
}

class ApiException implements Exception {
  const ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

String friendlyApiError(Object error) {
  final message = error.toString();
  if (message.contains('SocketException') ||
      message.contains('Failed host lookup') ||
      message.contains('Connection refused')) {
    return 'Cannot reach the backend. Check that FastAPI is running at $apiBaseUrl.';
  }
  if (message.contains('TimeoutException')) {
    return 'The backend took too long to respond. Please retry.';
  }
  return message.replaceFirst('Exception: ', '');
}
