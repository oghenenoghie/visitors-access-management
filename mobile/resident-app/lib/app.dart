import 'dart:async';

import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';

import 'core/api/api_client.dart';
import 'core/auth/auth_repository.dart';
import 'core/notifications/push_notification_service.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/login_screen.dart';
import 'features/auth/registration_screen.dart';
import 'features/history/visitor_history_screen.dart';
import 'features/home/home_screen.dart';
import 'features/invitations/create_invitation_screen.dart';
import 'features/invitations/pass_screen.dart';
import 'features/notifications/notification_inbox_screen.dart';

final secureStorageProvider =
    Provider<FlutterSecureStorage>((ref) => const FlutterSecureStorage());
final apiClientProvider =
    Provider<ApiClient>((ref) => ApiClient(ref.watch(secureStorageProvider)));
final authRepositoryProvider = Provider<AuthRepository>((ref) => AuthRepository(
    ref.watch(apiClientProvider), ref.watch(secureStorageProvider)));

class EstateResidentApp extends ConsumerStatefulWidget {
  const EstateResidentApp({super.key});
  @override
  ConsumerState<EstateResidentApp> createState() => _EstateResidentAppState();
}

class _EstateResidentAppState extends ConsumerState<EstateResidentApp> {
  late final GoRouter _router = GoRouter(
    initialLocation: '/login',
    redirect: (context, state) async {
      final hasSession = await ref.read(apiClientProvider).hasSession();
      final isLogin = state.matchedLocation == '/login';
      if (!hasSession && !isLogin) return '/login';
      if (hasSession && isLogin) return '/';
      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(
          path: '/register',
          builder: (context, state) => const RegistrationScreen()),
      GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
      GoRoute(
          path: '/history',
          builder: (context, state) => const VisitorHistoryScreen()),
      GoRoute(
          path: '/notifications',
          builder: (context, state) => NotificationInboxScreen(
              api: ref.read(apiClientProvider).dio)),
      GoRoute(
          path: '/invitations/new',
          builder: (context, state) => const CreateInvitationScreen()),
      GoRoute(
          path: '/passes/:id',
          builder: (context, state) =>
              PassScreen(invitationId: state.pathParameters['id']!)),
    ],
  );

  @override
  void initState() {
    super.initState();
    PushNotificationService.instance.setTapHandler((resourceId) {
      if (mounted) _router.go('/passes/$resourceId');
    });
    ref.read(apiClientProvider).hasSession().then((hasSession) {
      if (hasSession) {
        unawaited(PushNotificationService.instance
            .start(ref.read(apiClientProvider).dio));
      }
    });
  }

  @override
  Widget build(BuildContext context) => MaterialApp.router(
        title: 'Estate Access',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light,
        routerConfig: _router,
      );
}
