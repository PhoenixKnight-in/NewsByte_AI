import 'package:flutter/material.dart';
import 'package:frontend/home_page.dart';
import 'auth/login_page.dart';
import 'auth/signup_page.dart';
//import '../frontend/lib/home_page.dart'; // Make sure this is imported

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      initialRoute: '/',
      routes: {
        '/': (context) => SignupPage(),       // Login screen
        '/login': (context) => LoginPage(), // Signup screen
        '/home': (context) => HomePage(),     // Home screen
      },
    );
  }
}
