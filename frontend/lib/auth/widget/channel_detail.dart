import 'package:flutter/material.dart';
import '../../../video_summary_page.dart'; // ✅ Update path based on your folder structure


class ChannelDetailPage extends StatelessWidget {
 final String name;
 final String logo;


 const ChannelDetailPage({
   super.key,
   required this.name,
   required this.logo,
 });


 @override
 Widget build(BuildContext context) {
   return Scaffold(
     backgroundColor: const Color(0xFFF2F4F8),
     appBar: AppBar(
       backgroundColor: Colors.deepPurple,
       title: Text(name, style: const TextStyle(color: Colors.white)),
       centerTitle: true,
       iconTheme: const IconThemeData(color: Colors.white),
     ),
     body: SingleChildScrollView(
       padding: const EdgeInsets.all(20),
       child: Column(
         children: [
           // Channel Logo
           Center(
             child: Image.asset(
               logo,
               width: 120,
               height: 120,
               fit: BoxFit.contain,
             ),
           ),
           const SizedBox(height: 20),


           // Purple Button
           ElevatedButton(
             onPressed: () {},
             style: ElevatedButton.styleFrom(
               backgroundColor: Colors.deepPurple,
               shape: RoundedRectangleBorder(
                 borderRadius: BorderRadius.circular(30),
               ),
               padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
             ),
             child: const Text(
               'Click on videos to generate summary',
               style: TextStyle(fontSize: 14, color: Colors.white),
             ),
           ),


           const SizedBox(height: 30),


           // HEADLINE VIDEO CARDS
           _videoTile(
             context,
             Icons.memory,
             'Flight Data Recorder found in crash site',
             '2:03',
             Colors.blue,
             'This report covers how the flight data recorder was discovered and what it means for aviation safety.',
           ),
           const SizedBox(height: 16),
           _videoTile(
             context,
             Icons.sports_cricket,
             'India vs England Test – Day 1 Highlights',
             '11:56',
             Colors.green,
             'Catch all the key moments of Day 1, where Shubman Gill’s innings stood out.',
           ),
           const SizedBox(height: 16),
           _videoTile(
             context,
             Icons.account_balance,
             'PM addresses summit on AI policy',
             '6:41',
             Colors.red,
             'The Prime Minister elaborates on the government’s vision for responsible AI development.',
           ),
         ],
       ),
     ),
   );
 }


 // VIDEO TILE with tap to open summary
 Widget _videoTile(
     BuildContext context,
     IconData icon,
     String title,
     String duration,
     Color iconColor,
     String summary,
     ) {
   return GestureDetector(
     onTap: () {
       Navigator.push(
         context,
         MaterialPageRoute(
           builder: (_) => VideoSummaryPage(
             title: title,
             summary: summary,
           ),
         ),
       );
     },
     child: Container(
       padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 14),
       decoration: BoxDecoration(
         color: Colors.white,
         borderRadius: BorderRadius.circular(18),
         boxShadow: [
           BoxShadow(
             color: Colors.black.withOpacity(0.05),
             blurRadius: 8,
             offset: const Offset(0, 4),
           ),
         ],
       ),
       child: Row(
         children: [
           Icon(icon, size: 32, color: iconColor),
           const SizedBox(width: 16),
           Expanded(
             child: Text(
               title,
               style: const TextStyle(
                 fontSize: 17,
                 fontWeight: FontWeight.w600,
               ),
             ),
           ),
           Row(
             children: [
               const Icon(Icons.access_time, size: 16, color: Colors.grey),
               const SizedBox(width: 4),
               Text(
                 duration,
                 style: const TextStyle(fontSize: 14, color: Colors.grey),
               ),
             ],
           )
         ],
       ),
     ),
   );
 }
}
