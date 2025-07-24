import 'dart:convert';
import 'package:frontend/auth/constants/server_constant.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AuthService {
  static final String serverUrl = ServerConstant.serverURL; 

  static Future<bool> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$serverUrl/login'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {
        'username': username,
        'password': password,
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('access_token', data['access_token']);
      return true;
    } else {
      return false;
    }
  }

  static Future<bool> signup(String email, String username, String password) async {
    final response = await http.post(
      Uri.parse('$serverUrl/signup'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'username': username,
        'password': password,
      }),
    );

    return response.statusCode == 200 || response.statusCode == 201;
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
  }
}
