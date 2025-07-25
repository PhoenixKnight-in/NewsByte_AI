import 'dart:convert';
import 'package:http/http.dart' as http;

class GNewsService {
  static const String apiKey = '44d9f23cb545ff417e5333d9ce340cbb'; // Replace with your GNews API key
  static const String baseUrl = 'https://gnews.io/api/v4/top-headlines';

  static Future<List<dynamic>> fetchNews(String topic) async {
    final url = Uri.parse('$baseUrl?lang=en&max=10&topic=$topic&token=$apiKey');
    final response = await http.get(url);

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return data['articles'];
    } else {
      throw Exception('Failed to load news');
    }
  }
}
