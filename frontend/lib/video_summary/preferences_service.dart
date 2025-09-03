// lib/services/preferences_service.dart
import 'package:shared_preferences/shared_preferences.dart';

class PreferencesService {
  static const String _videoIdKey = 'videoId';

  // Save video ID
  Future<void> saveVideoId(String videoId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_videoIdKey, videoId);
  }

  // Get saved video ID
  Future<String?> getVideoId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_videoIdKey);
  }

  // Clear video ID
  Future<void> clearVideoId() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_videoIdKey);
  }
}
