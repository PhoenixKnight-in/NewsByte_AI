import 'package:flutter/material.dart';

class UserDetailsPage extends StatelessWidget {
  const UserDetailsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
        title: const Text('User Profile'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            children: [
              const SizedBox(height: 10),

              // 👤 App logo as profile image
              Image.asset(
                'assets/logo.png',
                width: 70,
              ),
              const SizedBox(height: 20),

              const Text(
                "poojika",
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              const Text(
                "pujikasshree@gmail.com",
                style: TextStyle(fontSize: 16, color: Colors.grey),
              ),
              const SizedBox(height: 30),

              // 💳 Cards
              _buildInfoCard(
                title: "Member Since",
                value: "July 2025",
                icon: Icons.calendar_today_outlined,
              ),
              _buildInfoCard(
                title: "Subscription Plan",
                value: "Free Tier",
                icon: Icons.workspace_premium_outlined,
              ),
              _buildInfoCard(
                title: "Saved Articles",
                value: "12",
                icon: Icons.bookmark_border,
              ),
              _buildInfoCard(
                title: "Preferences",
                value: "Technology, Sports",
                icon: Icons.settings_outlined,
              ),

              const SizedBox(height: 30),

              // 🔒 Logout Button with purple text
              OutlinedButton.icon(
                onPressed: () {
                  // Handle logout
                },
                icon: const Icon(Icons.logout, color: Colors.deepPurple),
                label: const Text(
                  "Logout",
                  style: TextStyle(
                    color: Colors.deepPurple,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: Colors.deepPurple),
                  padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  // 🔧 Reusable info card with better icons
  Widget _buildInfoCard({
    required String title,
    required String value,
    required IconData icon,
  }) {
    return Card(
      elevation: 1,
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: Icon(icon, color: Colors.deepPurple),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(value),
      ),
    );
  }
}
