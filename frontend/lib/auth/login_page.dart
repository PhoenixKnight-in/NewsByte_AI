import 'package:flutter/material.dart';
import 'package:frontend/auth/widget/auth_button.dart';
import 'package:frontend/auth/widget/customfield.dart';

class LoginPage extends StatefulWidget {
  LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  @override
  void dispose() {
    emailController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  Widget build(BuildContext context) {
    return Scaffold(
      // appBar: AppBar(),
      backgroundColor: Color(0xFFF2F4F8),
      body: Padding(
        padding: const EdgeInsets.only(top: 50.0, left: 15, right: 15),
        child: Center(
          child: Column(
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(125),
                child: Image.asset('assets/logo.png', height: 250),
              ),
              const SizedBox(height: 30),
              Text(
                "Login",
                style: TextStyle(
                  fontSize: 40,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF21005D),
                ),
              ),
              const SizedBox(height: 15),
              Text(
                "Welcome back",
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFFFF7B07),
                ),
              ),
              const SizedBox(height: 15),
              CustomField(hint_text: "Email", controller: emailController),
              const SizedBox(height: 15),
              CustomField(
                hint_text: "Password",
                controller: passwordController,
                isObscureText: true,
              ),

              const SizedBox(height: 15.0),
              AuthButton(
                button_text: "Login",
                onTap: () {
                  Navigator.pushNamed(context, '/home');
                },
              )

            ],
          ),
        ),
      ),
    );
  }
}