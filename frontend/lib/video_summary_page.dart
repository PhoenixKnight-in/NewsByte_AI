import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
// Add this in pubspec.yaml under dependencies


class VideoSummaryPage extends StatelessWidget {
 final String title;
 final String summary;


 const VideoSummaryPage({
   super.key,
   required this.title,
   required this.summary,
 });


 void _shareContent(BuildContext context) {
   final contentToShare = '$title\n\n$summary';
   Share.share(contentToShare);
 }


 void _saveContent(BuildContext context) {
   ScaffoldMessenger.of(context).showSnackBar(
     const SnackBar(
       content: Text('Saved for later!'),
       duration: Duration(seconds: 2),
     ),
   );
   // TODO: You can also store the saved content in local storage or a provider later.
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
         title,
         style: const TextStyle(
           color: Colors.white,
           fontWeight: FontWeight.w600,
           fontSize: 18,
         ),
       ),
     ),
     body: SingleChildScrollView(
       padding: const EdgeInsets.all(24.0),
       child: Column(
         crossAxisAlignment: CrossAxisAlignment.start,
         children: [
           const Text(
             'Summary',
             style: TextStyle(
               fontSize: 22,
               fontWeight: FontWeight.bold,
               color: Colors.deepPurple,
             ),
           ),
           const SizedBox(height: 16),


           // Summary Box
           Container(
             width: double.infinity,
             padding: const EdgeInsets.all(20),
             constraints: const BoxConstraints(minHeight: 500),
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
             child: Text(
               summary.isNotEmpty
                   ? summary
                   : "This video provides a detailed explanation of the recent developments, "
                   "highlighting expert insights, political reactions, and the public's response. "
                   "It aims to help viewers understand the context, significance, and possible "
                   "outcomes of the situation in a simple and engaging way.",
               style: const TextStyle(
                 fontSize: 16,
                 height: 1.6,
                 color: Colors.white,
               ),
             ),
           ),
           const SizedBox(height: 20),


           // Save & Share Buttons Row
           Row(
             mainAxisAlignment: MainAxisAlignment.spaceEvenly,
             children: [
               ElevatedButton.icon(
                 onPressed: () => _saveContent(context),
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
                 onPressed: () => _shareContent(context),
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
         ],
       ),
     ),
   );
 }
}
