// lib/home/YouTubeNewsService.dart
import 'dart:convert';
import 'package:frontend/auth/constants/server_constant.dart';
import 'package:http/http.dart' as http;

const String baseUrl = ServerConstant.serverURL; 

class YouTubeNewsService {
  static Future<List<dynamic>> fetchNews(String channel, {String? channelId}) async {
    final query = '$channel';
    final params = {
      'query': query,
      'num_videos': '10',
      'minutes_ago':'2000',
      if (channelId != null) 'channel_id': channelId,
    };
    final uri = Uri.parse('$baseUrl/get_latest_news').replace(queryParameters: params);
    print('YouTubeNewsService fetching: $uri');

    try {
      final response = await http.get(uri);
      print('Response status: ${response.statusCode}');
      if (response.statusCode == 200) {
        final decoded = json.decode(response.body);
        return decoded is List ? decoded : [];
      } else {
        throw Exception('Failed to fetch YouTube news: ${response.statusCode}');
      }
    } catch (e) {
      print('Fetch error: $e');
      rethrow;
    }
  }
}
