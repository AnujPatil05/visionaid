import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

class ApiService {
  // ⚠ Replace X with your laptop's WiFi IP before demo
  static const String baseUrl = 'http://10.43.178.159:8000';

  static Future<Map<String, dynamic>> processFrame(File imageFile) async {
    try {
      var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/process'));
      
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          imageFile.path,
          contentType: MediaType('image', 'jpeg'),
        ),
      );

      // Increased timeout to 15s to accommodate high-res OCR inference processing on standard CPU
      var streamedResponse = await request.send().timeout(const Duration(seconds: 15));
      var responseString = await streamedResponse.stream.bytesToString();
      
      return jsonDecode(responseString) as Map<String, dynamic>;
    } catch (e) {
      return {'action': 'error', 'message': e.toString()};
    }
  }

  static Future<bool> checkHealth() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health')).timeout(const Duration(seconds: 3));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
