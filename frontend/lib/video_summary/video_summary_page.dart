// File: pages/enhanced_video_summary_page.dart
import 'package:flutter/material.dart';
import 'package:frontend/video_summary/api_service.dart';
import 'package:frontend/video_summary/news_item.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

class EnhancedVideoSummaryPage extends StatefulWidget {
  final NewsItem newsItem;

  const EnhancedVideoSummaryPage({
    super.key,
    required this.newsItem,
  });

  @override
  State<EnhancedVideoSummaryPage> createState() => _EnhancedVideoSummaryPageState();
}

class _EnhancedVideoSummaryPageState extends State<EnhancedVideoSummaryPage> {
  String? _summary;
  bool _isLoading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSummary();
  }

  Future<void> _loadSummary() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Always fetch from API first (don't rely on stale NewsItem data)
      final summaryData = await ApiService.getSummary(widget.newsItem.videoId);
      
      if (summaryData != null && summaryData['has_summary'] == true) {
        setState(() {
          _summary = summaryData['summary'];
          _isLoading = false;
        });
      } else {
        // No summary exists in database
        setState(() {
          _summary = null;
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Failed to load summary: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _generateSummary() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final result = await ApiService.generateSummary(widget.newsItem.videoId);
      
      if (result != null) {
        setState(() {
          _summary = result['summary'];
          _isLoading = false;
        });
        
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Summary generated successfully!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      setState(() {
        _error = 'Failed to generate summary: $e';
        _isLoading = false;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // Enhanced YouTube video launcher with multiple fallback strategies
  Future<void> _openYouTubeVideo() async {
    final videoUrl = widget.newsItem.videoUrl ?? _constructVideoUrl(widget.newsItem.videoId);
    
    if (videoUrl.isEmpty) {
      _showError('No video URL available');
      return;
    }

    try {
      // Try multiple launch strategies
      bool success = false;

      // Strategy 1: Try launching with YouTube app first
      success = await _tryLaunchYouTubeApp(videoUrl);
      
      if (!success) {
        // Strategy 2: Try launching with external browser
        success = await _tryLaunchBrowser(videoUrl);
      }
      
      if (!success) {
        // Strategy 3: Try launching with any available app
        success = await _tryLaunchAny(videoUrl);
      }

      if (!success) {
        _showError('No app available to open YouTube videos');
      }

    } catch (e) {
      _showError('Failed to open video: ${e.toString()}');
    }
  }

  Future<bool> _tryLaunchYouTubeApp(String videoUrl) async {
    try {
      // Extract video ID from URL
      String? videoId = _extractVideoId(videoUrl);
      if (videoId != null) {
        // Try YouTube app deep link
        final youtubeAppUri = Uri.parse('youtube://www.youtube.com/watch?v=$videoId');
        if (await canLaunchUrl(youtubeAppUri)) {
          return await launchUrl(youtubeAppUri);
        }
      }
    } catch (e) {
      print('YouTube app launch failed: $e');
    }
    return false;
  }

  Future<bool> _tryLaunchBrowser(String videoUrl) async {
    try {
      final uri = Uri.parse(videoUrl);
      print('Checking canLaunchUrl for browser: $uri');
      
      if (await canLaunchUrl(uri)) {
        print('canLaunchUrl returned true, launching...');
        return await launchUrl(
          uri,
          mode: LaunchMode.externalApplication,
        );
      } else {
        print('canLaunchUrl returned false for browser');
      }
    } catch (e) {
      print('Browser launch failed: $e');
    }
    return false;
  }

  Future<bool> _tryLaunchAny(String videoUrl) async {
    try {
      final uri = Uri.parse(videoUrl);
      print('Checking canLaunchUrl for platform default: $uri');
      
      if (await canLaunchUrl(uri)) {
        print('canLaunchUrl returned true, launching with platform default...');
        return await launchUrl(
          uri,
          mode: LaunchMode.platformDefault,
        );
      } else {
        print('canLaunchUrl returned false for platform default');
      }
    } catch (e) {
      print('Platform default launch failed: $e');
    }
    return false;
  }
  
  String? _extractVideoId(String url) {
    // Handle various YouTube URL formats
    final patterns = [
      RegExp(r'youtube\.com/watch\?v=([^&]+)'),
      RegExp(r'youtu\.be/([^?]+)'),
      RegExp(r'youtube\.com/embed/([^?]+)'),
    ];
    
    for (final pattern in patterns) {
      final match = pattern.firstMatch(url);
      if (match != null) {
        return match.group(1);
      }
    }
    return null;
  }

  String _constructVideoUrl(String videoId) {
    if (videoId.isEmpty) return '';
    return 'https://www.youtube.com/watch?v=$videoId';
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        action: SnackBarAction(
          label: 'OK',
          textColor: Colors.white,
          onPressed: () {},
        ),
      ),
    );
  }

  void _shareContent() {
    final videoUrl = widget.newsItem.videoUrl ?? _constructVideoUrl(widget.newsItem.videoId);
    final contentToShare = '${widget.newsItem.title}\n\n${_summary ?? 'No summary available'}\n\n$videoUrl';
    Share.share(contentToShare);
  }

  void _saveContent() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Saved for later!'),
        duration: Duration(seconds: 2),
      ),
    );
    // TODO: Implement actual save functionality
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF2F4F8),
      appBar: AppBar(
        backgroundColor: Colors.deepPurple,
        elevation: 0,
        centerTitle: true,
        iconTheme: const IconThemeData(color: Colors.white),
        title: Text(
          widget.newsItem.title,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.play_arrow, color: Colors.white),
            onPressed: _openYouTubeVideo,
            tooltip: 'Watch on YouTube',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Video Info Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    widget.newsItem.channelName,
                    style: const TextStyle(
                      fontSize: 14,
                      color: Colors.grey,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    widget.newsItem.title,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (widget.newsItem.publishedAt != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      'Published: ${_formatDate(widget.newsItem.publishedAt!)}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Summary Section Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Summary',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Colors.deepPurple,
                  ),
                ),
                if (_summary == null && !_isLoading)
                  ElevatedButton.icon(
                    onPressed: _generateSummary,
                    icon: const Icon(Icons.auto_awesome, size: 18),
                    label: const Text('Generate'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                  ),
              ],
            ),
            
            const SizedBox(height: 16),

            // Summary Content
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              constraints: const BoxConstraints(minHeight: 200),
              decoration: BoxDecoration(
                color: Colors.deepPurple,
                borderRadius: BorderRadius.circular(18),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: _buildSummaryContent(),
            ),
            
            const SizedBox(height: 20),

            // Action Buttons
            if (_summary != null) ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton.icon(
                    onPressed: _saveContent,
                    icon: const Icon(Icons.bookmark_add_outlined),
                    label: const Text('Save'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                          vertical: 10, horizontal: 20),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                  ElevatedButton.icon(
                    onPressed: _shareContent,
                    icon: const Icon(Icons.share_outlined),
                    label: const Text('Share'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                          vertical: 10, horizontal: 20),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: 16),
              
              // Regenerate Button
              Center(
                child: TextButton.icon(
                  onPressed: _isLoading ? null : _generateSummary,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Regenerate Summary'),
                  style: TextButton.styleFrom(
                    foregroundColor: Colors.deepPurple,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryContent() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Colors.white),
            SizedBox(height: 16),
            Text(
              'Generating summary...',
              style: TextStyle(
                fontSize: 16,
                color: Colors.white70,
              ),
            ),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              color: Colors.white70,
              size: 48,
            ),
            const SizedBox(height: 16),
            Text(
              _error!,
              style: const TextStyle(
                fontSize: 16,
                color: Colors.white70,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadSummary,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: Colors.deepPurple,
              ),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_summary == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.summarize,
              color: Colors.white70,
              size: 48,
            ),
            const SizedBox(height: 16),
            const Text(
              'No summary available',
              style: TextStyle(
                fontSize: 18,
                color: Colors.white,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Click "Generate" to create a summary for this video',
              style: TextStyle(
                fontSize: 14,
                color: Colors.white.withOpacity(0.8),
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return Text(
      _summary!,
      style: const TextStyle(
        fontSize: 16,
        height: 1.6,
        color: Colors.white,
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
}