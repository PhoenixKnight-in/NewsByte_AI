import 'package:flutter/material.dart';
import 'package:frontend/youtube_channel/channel_home.dart';
import 'auth/widget/channel_details_page.dart';
//import 'channel_details_page.dart';

class ChannelsPage extends StatelessWidget {
  const ChannelsPage({super.key});

  // Sample channel data
  final List<Map<String, String>> channels = const [
    {
      'name': 'NDTV',
      'logo': 'assets/1st.jpg',
      'channel_id':"UCZFMm1mMw0F81Z37aaEzTUA",
      
    },
    {
      'name': 'Times Now',
      'logo': 'assets/2nd.png',
      'channel_id':"UC6RJ7-PaXg6TIH2BzZfTV7w",
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
                  builder: (context) => ChannelHPage(
                    channelName: channel['name']!,
                    channelID: channel['channel_id']!,
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