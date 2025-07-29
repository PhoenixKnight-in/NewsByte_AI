import 'package:flutter/material.dart';
import 'auth/widget/channel_details_page.dart';
//import 'channel_details_page.dart';

class ChannelsPage extends StatelessWidget {
  const ChannelsPage({super.key});

  // Sample channel data
  final List<Map<String, String>> channels = const [
    {
      'name': 'NDTV',
      'logo': 'assets/1st.jpg',
      'headline': "Will Dreamliner's Black Box need to go abroad?",
      'description': 'An NDTV exclusive report on aviation safety and data tracking.',
      'videoThumbnail': 'assets/1st.jpg',
      'videoDuration': '2:03',
    },
    {
      'name': 'Times Now',
      'logo': 'assets/2nd.png',
      'headline': 'India vs England Test - Shubman Era Begins',
      'description': 'Shubman Gill leads a young team in a red-ball challenge.',
      'videoThumbnail': 'assets/2nd.png',
      'videoDuration': '11:56',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF2F4F8),
      appBar: AppBar(
        backgroundColor: Colors.deepPurple,
        title: const Text(
          'Explore Channels',
          style: TextStyle(color: Colors.white),
        ),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: channels.length,
        separatorBuilder: (_, __) => const SizedBox(height: 16),
        itemBuilder: (context, index) {
          final channel = channels[index];

          return InkWell(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ChannelDetailPage(
                    name: channel['name']!,
                    logo: channel['logo']!,
                    headline: channel['headline']!,
                    description: channel['description']!,
                    videoThumbnail: channel['videoThumbnail']!,
                    videoDuration: channel['videoDuration']!,
                  ),
                ),
              );
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    blurRadius: 8,
                    color: Colors.black.withOpacity(0.05),
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.asset(
                      channel['logo']!,
                      width: 60,
                      height: 60,
                      fit: BoxFit.cover,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Text(
                      channel['name']!,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const Icon(Icons.chevron_right, color: Colors.grey),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}