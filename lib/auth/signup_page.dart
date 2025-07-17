import 'package:flutter/material.dart';
import 'package:frontend/auth/widget/auth_button.dart';
import 'package:frontend/auth/widget/customfield.dart';

class SignupPage extends StatefulWidget {
  SignupPage({super.key});

  @override
  State<SignupPage> createState() => _SignupPageState();
}

class _SignupPageState extends State<SignupPage> {
  final nameController = TextEditingController();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  @override
  void dispose() {
    nameController.dispose();
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
                "Sign Up. To get",
                style: TextStyle(
                  fontSize: 40,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF21005D),
                ),
              ),

              const SizedBox(height: 15,),
              Text(
                "Instant News from your ❤ Channels",
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFFFF7B07),
                ),
              ),
              const SizedBox(height: 15),
              CustomField(hint_text: "Username", controller: nameController),
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
                button_text: "Login", // or "Sign Up"
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
