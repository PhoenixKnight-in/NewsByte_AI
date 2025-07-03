import 'package:flutter/material.dart';
import 'channels_page.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3, // For You, Sports, Entertainment
      child: Scaffold(
        backgroundColor: const Color(0xFFF2F4F8),
        appBar: AppBar(
          backgroundColor: Colors.white,
          elevation: 0,
          leading: const Padding(
            padding: EdgeInsets.all(10),
            child: Icon(Icons.menu, color: Colors.black),
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
          actions: const [
            Padding(
              padding: EdgeInsets.all(10),
              child: Icon(Icons.person_outline, color: Colors.black),
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
            _buildForYouTab(context),
            const Center(child: Text("Sports Tab")),
            const Center(child: Text("Entertainment Tab")),
          ],
        ),
        bottomNavigationBar: BottomNavigationBar(
          currentIndex: 0,
          selectedItemColor: Colors.deepPurple,
          unselectedItemColor: Colors.grey,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.home),
              label: '',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.bookmark),
              label: '',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildForYouTab(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        children: [
          const SizedBox(height: 15),

          // 📰 First News
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: Image.asset(
              'assets/Canada_G7_Summit_44906.jpg',
              width: double.infinity,
              height: 200,
              fit: BoxFit.cover,
            ),
          ),
          const SizedBox(height: 15),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              "G7 summit LIVE: Leaders fail to reach ambitious joint agreements on key issues after Trump’s exit",
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
                color: Colors.black,
              ),
              textAlign: TextAlign.center,
            ),
          ),

          const SizedBox(height: 30),

          // 📰 Second News
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: Image.asset(
              'assets/2nd_news.jpg.avif',
              width: double.infinity,
              height: 200,
              fit: BoxFit.cover,
            ),
          ),
          const SizedBox(height: 15),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              "India vs England LIVE Score, 2nd Test Day 2: Ravindra Jadeja departs for 89, IND 416/6 vs ENG in Edgbaston",
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
                color: Colors.black,
              ),
              textAlign: TextAlign.center,
            ),
          ),

          const SizedBox(height: 30),

          // ✅ Button at the very bottom
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const ChannelsPage(),
                  ),
                );
              },

              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4B0082),
                padding: const EdgeInsets.symmetric(vertical: 15),
                minimumSize: const Size(double.infinity, 50),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text(
                "Explore more channels here",
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.white,
                ),
              ),
            ),
          ),

          const SizedBox(height: 30),
        ],
      ),
    );
  }
}
