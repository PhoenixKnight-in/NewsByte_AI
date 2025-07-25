import 'package:flutter/material.dart';
import 'package:frontend/auth/widget/saved_news_page.dart';
import 'package:frontend/auth/widget/user_details_page.dart';
import 'package:frontend/channels_page.dart';
//import 'package:frontend/channels_page.dart';
import 'package:frontend/home/GNewsService.dart';
//import 'package:frontend/services/gnews_service.dart'; // Add this line
import 'package:frontend/home/GNewsService.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

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
          bottom: const TabBar(
            labelColor: Colors.deepPurple,
            unselectedLabelColor: Colors.grey,
            indicatorColor: Colors.deepPurple,
            tabs: [
              Tab(text: 'For you'),
              Tab(text: 'Sports'),
              Tab(text: 'Entertainment'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _buildNewsTab('general'), // "For You" -> General
            _buildNewsTab('sports'), // Sports
            _buildNewsTab('entertainment'), // Entertainment
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
          },
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.home), label: ''),
            BottomNavigationBarItem(icon: Icon(Icons.bookmark), label: ''),
          ],
        ),
      ),
    );
  }

  Widget _buildNewsTab(String topic) {
    return FutureBuilder<List<dynamic>>(
      future: GNewsService.fetchNews(topic),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        } else if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return const Center(child: Text('No news available.'));
        }

        final articles = snapshot.data!;
        return ListView.builder(
          itemCount: articles.length,
          itemBuilder: (context, index) {
            final article = articles[index];
            return Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (article['image'] != null)
                    ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: Image.network(
                        article['image'],
                        height: 200,
                        width: double.infinity,
                        fit: BoxFit.cover,
                      ),
                    ),
                  const SizedBox(height: 10),
                  Text(
                    article['title'] ?? 'No title',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    article['description'] ?? '',
                    style: const TextStyle(fontSize: 14),
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
}
