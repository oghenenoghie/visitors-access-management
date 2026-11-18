import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:estate_security_app/main.dart';

void main() {
  testWidgets('security officer can reach the sign-in form', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: GateLogin(onAuthenticated: () {}),
    ));

    expect(find.text('Security officer sign in'), findsOneWidget);
    expect(find.text('Email address'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
  });
}
