import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app.dart';
import '../../core/theme/app_theme.dart';

class RegistrationScreen extends ConsumerStatefulWidget {
  const RegistrationScreen({super.key});
  @override
  ConsumerState<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends ConsumerState<RegistrationScreen> {
  final _estateCode = TextEditingController();
  final _firstName = TextEditingController();
  final _lastName = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  bool _submitted = false;
  String? _error;

  @override
  void dispose() {
    _estateCode.dispose();
    _firstName.dispose();
    _lastName.dispose();
    _email.dispose();
    _phone.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _register() async {
    if ([_estateCode, _firstName, _lastName, _email, _password]
        .any((field) => field.text.trim().isEmpty)) {
      setState(
          () => _error = 'Complete all required fields before submitting.');
      return;
    }
    if (_password.text.length < 10) {
      setState(() => _error = 'Choose a password with at least 10 characters.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).dio.post(
            'residents/register/',
            data: {
              'estate_code': _estateCode.text.trim(),
              'first_name': _firstName.text.trim(),
              'last_name': _lastName.text.trim(),
              'email': _email.text.trim(),
              'phone_number': _phone.text.trim(),
              'password': _password.text,
            },
            options: Options(
                headers: {'Authorization': null}, extra: {'skipAuth': true}),
          );
      if (mounted) setState(() => _submitted = true);
    } on DioException catch (error) {
      final data = error.response?.data;
      if (mounted)
        setState(() => _error = data is Map
            ? (data['detail'] ?? data['error']?['message'] ?? data.toString())
                .toString()
            : 'Registration could not be submitted.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Resident registration')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: _submitted
                ? Column(children: [
                    Container(
                        width: 68,
                        height: 68,
                        decoration: BoxDecoration(
                            color: AppColors.mint,
                            borderRadius: BorderRadius.circular(22)),
                        child: const Icon(Icons.mark_email_read_outlined,
                            size: 34, color: AppColors.forest)),
                    const SizedBox(height: 20),
                    Text('Request submitted',
                        style: Theme.of(context)
                            .textTheme
                            .headlineSmall
                            ?.copyWith(fontWeight: FontWeight.w800)),
                    const SizedBox(height: 10),
                    const Text(
                        'Your account is pending estate management approval. You will be able to sign in after your resident profile has been reviewed and activated.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: AppColors.muted, height: 1.5)),
                    const SizedBox(height: 24),
                    FilledButton(
                        onPressed: () => context.go('/login'),
                        child: const Text('Back to sign in')),
                  ])
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                        Text('Request resident access',
                            style: Theme.of(context)
                                .textTheme
                                .headlineSmall
                                ?.copyWith(
                                    fontWeight: FontWeight.w800,
                                    color: AppColors.ink)),
                        const SizedBox(height: 8),
                        const Text(
                            'Submit your details for review by your estate management team.',
                            style:
                                TextStyle(color: AppColors.muted, height: 1.5)),
                        const SizedBox(height: 24),
                        TextField(
                            controller: _estateCode,
                            textCapitalization: TextCapitalization.characters,
                            decoration: const InputDecoration(
                                labelText: 'Estate code *')),
                        const SizedBox(height: 12),
                        TextField(
                            controller: _firstName,
                            textCapitalization: TextCapitalization.words,
                            decoration: const InputDecoration(
                                labelText: 'First name *')),
                        const SizedBox(height: 12),
                        TextField(
                            controller: _lastName,
                            textCapitalization: TextCapitalization.words,
                            decoration: const InputDecoration(
                                labelText: 'Last name *')),
                        const SizedBox(height: 12),
                        TextField(
                            controller: _email,
                            keyboardType: TextInputType.emailAddress,
                            decoration: const InputDecoration(
                                labelText: 'Email address *')),
                        const SizedBox(height: 12),
                        TextField(
                            controller: _phone,
                            keyboardType: TextInputType.phone,
                            decoration: const InputDecoration(
                                labelText: 'Phone number (optional)')),
                        const SizedBox(height: 12),
                        TextField(
                            controller: _password,
                            obscureText: true,
                            decoration: const InputDecoration(
                                labelText: 'Password *',
                                helperText: 'At least 10 characters')),
                        if (_error != null) ...[
                          const SizedBox(height: 12),
                          Text(_error!,
                              style: const TextStyle(color: AppColors.danger)),
                        ],
                        const SizedBox(height: 20),
                        FilledButton(
                          onPressed: _busy ? null : _register,
                          child: _busy
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2, color: Colors.white))
                              : const Text('Submit for approval'),
                        ),
                        const SizedBox(height: 12),
                        const Text(
                            'Registration does not grant access automatically. Estate management approval is required.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                                fontSize: 12,
                                color: AppColors.muted,
                                height: 1.5)),
                      ]),
          ),
        ),
      ),
    );
  }
}
