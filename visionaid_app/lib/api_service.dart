import 'dart:io';
import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

class ApiService {
  static String _baseUrl = 'http://10.43.178.159:8000'; // overwritten by init()

  /// Must be called once from main() before runApp().
  /// Reads assets/config.json and sets the base URL.
  static Future<void> init() async {
    try {
      final raw = await rootBundle.loadString('assets/config.json');
      final cfg = jsonDecode(raw) as Map<String, dynamic>;
      final ip = cfg['server_ip'] as String? ?? '10.43.178.159';
      final port = cfg['server_port'] as int? ?? 8000;
      _baseUrl = 'http://$ip:$port';
    } catch (e) {
      // Keep the compiled default if asset loading fails
      print('[ApiService] Failed to load config.json: $e');
    }
  }

  static Future<Map<String, dynamic>> processFrame(File imageFile) async {
    try {
      var request =
          http.MultipartRequest('POST', Uri.parse('$_baseUrl/process'));

      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          imageFile.path,
          contentType: MediaType('image', 'jpeg'),
        ),
      );

      // 15 s timeout accommodates CPU-only OCR inference
      var streamedResponse =
          await request.send().timeout(const Duration(seconds: 15));
      var responseString = await streamedResponse.stream.bytesToString();

      return jsonDecode(responseString) as Map<String, dynamic>;
    } catch (e) {
      return {'action': 'error', 'message': e.toString()};
    }
  }

  static Future<String> sceneDescribe(File imageFile) async {
    try {
      var request = http.MultipartRequest('POST', Uri.parse('$_baseUrl/scene'));

      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          imageFile.path,
          contentType: MediaType('image', 'jpeg'),
        ),
      );

      var streamedResponse =
          await request.send().timeout(const Duration(seconds: 20));
      var responseString = await streamedResponse.stream.bytesToString();
      final data = jsonDecode(responseString) as Map<String, dynamic>;
      return data['summary'] as String? ?? 'Could not analyse scene.';
    } catch (e) {
      return 'Could not analyse scene.';
    }
  }

  static Future<bool> checkHealth() async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/health'))
          .timeout(const Duration(seconds: 3));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
