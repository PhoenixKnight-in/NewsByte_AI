import 'package:flutter/material.dart';
import 'package:frontend/video_summary/preferences_service.dart';

class VideoSummaryPage extends StatefulWidget {
  final String title;       // required parameter
  final String transcript;  // required parameter

  const VideoSummaryPage({
    super.key,
    required this.title,
    required this.transcript,
  });

  @override
  _VideoSummaryPageState createState() => _VideoSummaryPageState();
}

class _VideoSummaryPageState extends State<VideoSummaryPage> {
  final PreferencesService _preferencesService = PreferencesService();
  String? _savedVideoId;

  @override
  void initState() {
    super.initState();
    _loadVideoId();
  }

  Future<void> _loadVideoId() async {
    String? videoId = await _preferencesService.getVideoId();
    setState(() {
      _savedVideoId = videoId;
    });
  }

  Future<void> _saveVideoId(String videoId) async {
    await _preferencesService.saveVideoId(videoId);
    setState(() {
      _savedVideoId = videoId;
    });
  }

  Future<void> _clearVideoId() async {
    await _preferencesService.clearVideoId();
    setState(() {
      _savedVideoId = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)), // ✅ use title from constructor
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.title,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                widget.transcript.isNotEmpty
                    ? widget.transcript
                    : "No transcript available.",
                style: const TextStyle(fontSize: 16),
              ),
              const SizedBox(height: 20),
              Text("Saved Video ID: ${_savedVideoId ?? 'None'}"),
              const SizedBox(height: 10),
              ElevatedButton(
                onPressed: () => _saveVideoId("exampleVideoId123"),
                child: const Text("Save Video ID"),
              ),
              ElevatedButton(
                onPressed: _clearVideoId,
                child: const Text("Clear Video ID"),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
