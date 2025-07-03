import 'package:flutter/material.dart';

class ChannelDetailPage extends StatelessWidget {
  final String name;
  final String logo;
  final String headline;
  final String description;
  final String videoThumbnail;
  final String videoDuration;

  const ChannelDetailPage({
    super.key,
    required this.name,
    required this.logo,
    required this.headline,
    required this.description,
    required this.videoThumbnail,
    required this.videoDuration,
  });

  final List<Map<String, String>> moreVideos = const [
    {
      'title': 'Flight Data Recorder found in crash site',
      'thumbnail': 'assets/1st.jpg',
      'duration': '2:03',
    },
    {
      'title': 'India vs England Test – Day 1 Highlights',
      'thumbnail': 'assets/2nd.png',
      'duration': '11:56',
    },
    {
      'title': 'PM addresses summit on AI policy',
      'thumbnail': 'assets/3rd.png',
      'duration': '6:41',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF2F4F8),
      appBar: AppBar(
        backgroundColor: Colors.deepPurple,
        title: Text(
          name,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Big Logo instead of video
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.asset(
                logo,
                width: double.infinity,
                height: 150,
                fit: BoxFit.contain,
              ),
            ),
            const SizedBox(height: 12),

            // Summary Button
            Center(
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.purple,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding:
                  const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
                onPressed: () {
                  // TODO: Add action to generate summary
                },
                child: const Text(
                  'Click on videos to generate summary',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),

            Text(
              headline,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              description,
              style: const TextStyle(fontSize: 15, color: Colors.black87),
            ),
            const SizedBox(height: 24),

            const Text(
              'More Videos',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),

            Column(
              children: moreVideos.map((video) {
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black12,
                        blurRadius: 5,
                        offset: const Offset(0, 3),
                      )
                    ],
                  ),
                  child: Row(
                    children: [
                      ClipRRect(
                        borderRadius: const BorderRadius.only(
                          topLeft: Radius.circular(12),
                          bottomLeft: Radius.circular(12),
                        ),
                        child: Image.asset(
                          video['thumbnail']!,
                          width: 120,
                          height: 80,
                          fit: BoxFit.cover,
                        ),
                      ),
                      Expanded(
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                video['title']!,
                                style:
                                const TextStyle(fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  const Icon(Icons.schedule,
                                      size: 14, color: Colors.grey),
                                  const SizedBox(width: 4),
                                  Text(
                                    video['duration']!,
                                    style: const TextStyle(color: Colors.grey),
                                  ),
                                ],
                              )
                            ],
                          ),
                        ),
                      )
                    ],
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
}
