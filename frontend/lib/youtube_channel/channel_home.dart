import 'package:flutter/material.dart';
import 'package:frontend/auth/widget/saved_news_page.dart';
import 'package:frontend/auth/widget/user_details_page.dart';
import 'package:frontend/channels_page.dart';
import 'package:frontend/home_page.dart';
import 'package:frontend/video_summary/video_summary_page.dart';
import 'package:frontend/youtube_channel/YoutubeNewsService.dart';

import 'package:frontend/video_summary/news_item.dart'; // Add this import

class ChannelHPage extends StatelessWidget {
  final String channelName;
  final String channelID;
  const ChannelHPage({super.key, required this.channelName, required this.channelID});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3, // For You, Sports, Entertainment
      child: Scaffold(
        backgroundColor: const Color(0xFFF2F4F8),
        drawer: Drawer(
          child: ListView(
            padding: EdgeInsets.zero,
            children: [
              DrawerHeader(
                decoration: BoxDecoration(color: Colors.deepPurple),
                child: Text(
                  'Menu',
                  style: TextStyle(color: Colors.white, fontSize: 24),
                ),
              ),
              ListTile(leading: Icon(Icons.settings), title: Text('Settings')),
              ListTile(leading: Icon(Icons.info), title: Text('About')),
              ListTile(
                leading: Icon(Icons.add_box),
                title: Text("Explore Channels"),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const ChannelsPage(),
                    ),
                  );
                },
              ),
              ListTile(
                leading: Icon(Icons.home),
                title: Text("Home"),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const HomePage()),
                  );
                },
              ),
            ],
          ),
        ),
        appBar: AppBar(
          backgroundColor: Colors.white,
          elevation: 0,
          leading: Builder(
            builder: (context) => IconButton(
              icon: const Icon(Icons.menu, color: Colors.black),
              onPressed: () {
                Scaffold.of(context).openDrawer();
              },
            ),
          ),
          title: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Image.asset(
                'assets/logo.png',
                width: 40,
                height: 40,
                fit: BoxFit.cover,
              ),
              const SizedBox(width: 8),
              const Text(
                'News Byte AI',
                style: TextStyle(
                  color: Colors.black,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          centerTitle: true,
          actions: [
            IconButton(
              icon: const Icon(Icons.person_outline, color: Colors.black),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const UserDetailsPage(),
                  ),
                );
              },
            ),
          ],
          bottom: TabBar(
            labelColor: Colors.deepPurple,
            unselectedLabelColor: Colors.grey,
            indicatorColor: Colors.deepPurple,
            tabs: [
              Tab(text: '$channelName Latest News'),
              // Tab(text: '$channelName Entertainment'),
              // Tab(text: '$channelName Politics'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _buildNewsTab("$channelName", '$channelID'), // "For You" -> General
          ],
        ),
        bottomNavigationBar: BottomNavigationBar(
          currentIndex: 0,
          selectedItemColor: Colors.deepPurple,
          unselectedItemColor: Colors.grey,
          onTap: (index) {
            if (index == 1) {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const SavedNewsPage()),
              );
            }
            if (index == 2) {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const ChannelsPage()),
              );
            }
          },
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
            BottomNavigationBarItem(icon: Icon(Icons.bookmark), label: 'Saved'),
            BottomNavigationBarItem(
              icon: Icon(Icons.add_box),
              label: 'Explore Channels',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNewsTab(String channel, String channel_id) {
    return FutureBuilder<List<dynamic>>(
      future: YouTubeNewsService.fetchNews(
        channel,
        channelId: channel_id,
      ),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        } else if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return const Center(child: Text('No news available.'));
        }

        final videos = snapshot.data!;
        return ListView.builder(
          itemCount: videos.length,
          itemBuilder: (context, index) {
            final video = videos[index];
            return Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (video['thumbnail'] != null)
                    ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: Image.network(
                        video['thumbnail'],
                        height: 200,
                        width: double.infinity,
                        fit: BoxFit.cover,
                      ),
                    ),
                  const SizedBox(height: 10),
                  Text(
                    video['title'] ?? 'No title',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    video['genre'] ?? 'Unknown',
                    style: const TextStyle(
                      fontSize: 14,
                      color: Colors.deepPurple,
                    ),
                  ),
                  const SizedBox(height: 6),
                  TextButton(
                    onPressed: () {
                      // Navigate to Enhanced Video Summary Page
                      _navigateToSummaryPage(context, video, channel);
                    },
                    child: const Text("Generate Summary"),
                  ),
                  const Divider(height: 30, thickness: 1),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _navigateToSummaryPage(BuildContext context, Map<String, dynamic> video, String channelName) {
    // Create a NewsItem object from the video data
    final newsItem = NewsItem(
      videoId: _extractVideoId(video['video_url'] ?? ''),
      title: video['title'] ?? 'No title',
      channelName: channelName,
      videoUrl: video['video_url'],
      thumbnailUrl: video['thumbnail'],
      publishedAt: video['published_at'] != null 
          ? DateTime.tryParse(video['published_at']) 
          : null, channelId: channelID,
    );

    // Navigate to the Enhanced Video Summary Page
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => EnhancedVideoSummaryPage(
          newsItem: newsItem,
        ),
      ),
    );
  }

  String _extractVideoId(String videoUrl) {
    // Extract video ID from YouTube URL
    if (videoUrl.isEmpty) return '';
    
    // Handle different YouTube URL formats
    RegExp regExp = RegExp(
      r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})',
      caseSensitive: false,
      multiLine: false,
    );
    
    Match? match = regExp.firstMatch(videoUrl);
    return match?.group(1) ?? '';
  }
}