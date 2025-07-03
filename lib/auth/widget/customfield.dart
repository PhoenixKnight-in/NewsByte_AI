import 'package:flutter/material.dart';

class CustomField extends StatelessWidget {
  final String hint_text;
  final TextEditingController controller;
  final bool isObscureText;
  const CustomField({
    super.key,
    required this.hint_text,
    required this.controller,
    this.isObscureText = false,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      decoration: InputDecoration(
      contentPadding: const EdgeInsets.all(27),
      enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade400, width: 1),
          ),
      focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Color(0xFF21005D), width: 2),
          ),
      hintText: hint_text,
      ),
      validator: (val) {
        if (val!.trim().isEmpty) {
          return "$hint_text is missing!!";
        }
        return null;
      },
      obscureText: isObscureText,
    );
  }
}
