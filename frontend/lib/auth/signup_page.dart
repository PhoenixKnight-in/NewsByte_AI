import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:frontend/auth/constants/server_constant.dart';
import 'package:frontend/auth/login_page.dart';
import 'package:frontend/auth/widget/auth_button.dart';
import 'package:frontend/auth/widget/customfield.dart';
import 'package:http/http.dart' as http;

class SignupPage extends StatefulWidget {
  SignupPage({super.key});

  @override
  State<SignupPage> createState() => _SignupPageState();
}

class _SignupPageState extends State<SignupPage> {
  final nameController = TextEditingController();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();

  Future<void> signupUser() async {
    print("User signing in");
    final name = nameController.text.trim();
    final email = emailController.text.trim();
    final password = passwordController.text.trim();

    if (name.isEmpty || email.isEmpty || password.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('All fields are required')));
      return;
    }

    final response = await http.post(
      Uri.parse('${ServerConstant.serverURL}/signup'), // update with actual URL
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': name,
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Signup successful! Please login.')),
      );
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => LoginPage()),
      );
    } else {
      final error = jsonDecode(response.body);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Signup failed: ${error['detail'] ?? 'Try again'}'),
        ),
      );
    }
  }

  @override
  void dispose() {
    nameController.dispose();
    emailController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFF2F4F8),
      resizeToAvoidBottomInset: true, // Important: Allow scaffold to resize
      body: SingleChildScrollView( // Wrap body with SingleChildScrollView
        child: Padding(
          padding: const EdgeInsets.only(top: 50.0, left: 15, right: 15, bottom: 20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SizedBox(height: MediaQuery.of(context).size.height * 0.05), // Dynamic spacing
              ClipRRect(
                borderRadius: BorderRadius.circular(125),
                child: Image.asset(
                  'assets/logo.png', 
                  height: 180, // Reduced height for better spacing (signup has more fields)
                ),
              ),
              const SizedBox(height: 20),
              Text(
                "Sign Up. To get",
                style: TextStyle(
                  fontSize: 34, // Slightly reduced for better fit
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF21005D),
                ),
              ),
              const SizedBox(height: 10),
              Text(
                "Instant News from NewsByte",
                style: TextStyle(
                  fontSize: 18, // Slightly reduced for better fit
                  fontWeight: FontWeight.bold,
                  color: Color(0xFFFF7B07),
                ),
              ),
              const SizedBox(height: 25),
              CustomField(hint_text: "Username", controller: nameController),
              const SizedBox(height: 15),
              CustomField(hint_text: "Email", controller: emailController),
              const SizedBox(height: 15),
              CustomField(
                hint_text: "Password",
                controller: passwordController,
                isObscureText: true,
              ),
              const SizedBox(height: 25),
              AuthButton(button_text: "Sign Up", onTap: signupUser),
              const SizedBox(height: 20),
              GestureDetector(
                onTap: () {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (context) => LoginPage()),
                  );
                },
                child: RichText(
                  text: TextSpan(
                    text: "Already have an account? ",
                    style: Theme.of(context).textTheme.titleMedium,
                    children: const [
                      TextSpan(
                        text: "Sign in",
                        style: TextStyle(color: Color(0xFFFF7B07)),
                      ),
                    ],
                  ),
                ),
              ),
              SizedBox(height: MediaQuery.of(context).viewInsets.bottom), // Add bottom padding for keyboard
            ],
          ),
        ),
      ),
    );
  }
}