import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app.dart';
import '../../core/theme/app_theme.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _code = TextEditingController();
  bool _busy = false;
  String? _challenge;
  bool _setup = false;
  String? _secret;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _code.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() { _busy = true; _error = null; });
    try {
      final auth = ref.read(authRepositoryProvider);
      if (_challenge == null) {
        final result = await auth.signIn(email: _email.text, password: _password.text);
        final state = result['status'];
        if (state == 'authenticated') {
          await ref.read(apiClientProvider).saveSession(access: result['access'] as String, refresh: result['refresh'] as String);
          if (mounted) context.go('/');
          return;
        }
        if (state == 'two_factor_required' || state == 'two_factor_setup_required') {
          _challenge = result['challenge_token'] as String;
          _setup = state == 'two_factor_setup_required';
          if (_setup) {
            final setup = await auth.beginTwoFactorSetup(_challenge!);
            _secret = setup['secret'] as String;
          }
          if (mounted) setState(() {});
        } else {
          throw StateError('Unsupported authentication response.');
        }
      } else {
        final result = await auth.completeTwoFactor(challenge: _challenge!, code: _code.text, setup: _setup);
        if (result['status'] == 'authenticated' && mounted) {
          context.go('/');
          return;
        }
      }
    } on DioException catch (error) {
      final data = error.response?.data;
      setState(() => _error = data is Map ? (data['detail'] ?? data['error']?['message'] ?? 'Sign-in failed.').toString() : 'Cannot reach the API. Check the server address and connection.');
    } catch (_) {
      setState(() => _error = 'Something went wrong. Please try again.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final awaitingCode = _challenge != null;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(width: 58, height: 58, decoration: BoxDecoration(color: AppColors.mint, borderRadius: BorderRadius.circular(18)), child: const Icon(Icons.shield_outlined, color: AppColors.forest, size: 30)),
                  const SizedBox(height: 32),
                  Text(awaitingCode ? 'Verify it’s you' : 'Welcome home', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800, color: AppColors.ink)),
                  const SizedBox(height: 8),
                  Text(awaitingCode ? 'Enter the current code from your authenticator app.' : 'Sign in to manage visitors and keep your home connected.', style: const TextStyle(color: AppColors.muted, height: 1.5)),
                  const SizedBox(height: 28),
                  if (!awaitingCode) ...[
                    TextField(controller: _email, keyboardType: TextInputType.emailAddress, textInputAction: TextInputAction.next, autofillHints: const [AutofillHints.username], decoration: const InputDecoration(labelText: 'Email address', prefixIcon: Icon(Icons.mail_outline))),
                    const SizedBox(height: 14),
                    TextField(controller: _password, obscureText: true, autofillHints: const [AutofillHints.password], onSubmitted: (_) => _submit(), decoration: const InputDecoration(labelText: 'Password', prefixIcon: Icon(Icons.lock_outline))),
                  ] else ...[
                    if (_secret != null)
                      Container(
                        padding: const EdgeInsets.all(16),
                        margin: const EdgeInsets.only(bottom: 16),
                        decoration: BoxDecoration(color: AppColors.mint, borderRadius: BorderRadius.circular(14)),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          const Text('Set up your authenticator', style: TextStyle(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 8),
                          const Text('Add this secret manually in your authenticator app, then enter its current code.'),
                          const SizedBox(height: 8),
                          SelectableText(_secret!, style: const TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1.2)),
                        ]),
                      ),
                    TextField(controller: _code, keyboardType: TextInputType.number, maxLength: 8, autofocus: true, onSubmitted: (_) => _submit(), decoration: const InputDecoration(labelText: 'Authenticator code', prefixIcon: Icon(Icons.verified_user_outlined))),
                    TextButton(onPressed: () => setState(() { _challenge = null; _secret = null; _code.clear(); }), child: const Text('Use a different account')),
                  ],
                  if (_error != null) ...[
                    const SizedBox(height: 12),
                    Text(_error!, style: const TextStyle(color: AppColors.danger)),
                  ],
                  const SizedBox(height: 20),
                  FilledButton(
                    onPressed: _busy ? null : _submit,
                    child: _busy ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : Text(awaitingCode ? 'Verify and continue' : 'Sign in'),
                  ),
                  const SizedBox(height: 20),
                  const Center(child: Text('Access is available to residents approved by estate management.', textAlign: TextAlign.center, style: TextStyle(color: AppColors.muted, fontSize: 12, height: 1.5))),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
