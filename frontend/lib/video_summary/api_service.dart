import 'dart:convert';
import 'package:frontend/video_summary/news_item.dart';
import 'package:http/http.dart' as http;


class ApiService {
  static const String baseUrl = 'http://192.168.31.14:8000'; // Change to your server URL
  static String? _authToken;

  // Set auth token after login
  static void setAuthToken(String token) {
    _authToken = token;
  }

  // Get auth headers
  static Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (_authToken != null) 'Authorization': 'Bearer $_authToken',
  };

  // Get news by channel
  static Future<List<NewsItem>> getNewsByChannel(String channelId, {int limit = 50}) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/get_news_by_channel/$channelId?limit=$limit'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((item) => NewsItem.fromJson(item)).toList();
      } else {
        throw Exception('Failed to fetch news: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching news: $e');
      return [];
    }
  }

  // Get summary for a specific video
  static Future<Map<String, dynamic>?> getSummary(String videoId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/get_summary/$videoId'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else if (response.statusCode == 404) {
        return null; // No summary exists
      } else {
        throw Exception('Failed to get summary: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting summary: $e');
      return null;
    }
  }

  // Generate summary for a video
  static Future<Map<String, dynamic>?> generateSummary(String videoId) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/summarize_news/$videoId'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final errorData = json.decode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to generate summary');
      }
    } catch (e) {
      print('Error generating summary: $e');
      throw e;
    }
  }

  // Get available channels
  static Future<List<Map<String, dynamic>>> getCachedChannels() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/get_cached_channels'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return List<Map<String, dynamic>>.from(data['channels'] ?? []);
      } else {
        throw Exception('Failed to fetch channels');
      }
    } catch (e) {
      print('Error fetching channels: $e');
      return [];
    }
  }
}