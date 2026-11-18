import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

@pragma('vm:entry-point')
Future<void> estatePushBackgroundHandler(RemoteMessage message) async {
  try {
    await Firebase.initializeApp();
  } catch (_) {
    // Firebase is optional until the estate project is configured.
  }
}

class PushNotificationService {
  PushNotificationService._();
  static final PushNotificationService instance = PushNotificationService._();

  final FlutterLocalNotificationsPlugin _local =
      FlutterLocalNotificationsPlugin();
  StreamSubscription<RemoteMessage>? _foregroundSubscription;
  StreamSubscription<RemoteMessage>? _openedSubscription;
  StreamSubscription<String>? _tokenSubscription;
  Dio? _api;
  void Function(String resourceId)? _onInvitationTap;
  bool _initialized = false;
  bool _available = false;

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;
    try {
      await Firebase.initializeApp();
      FirebaseMessaging.onBackgroundMessage(estatePushBackgroundHandler);
      const settings = InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(),
      );
      await _local.initialize(
        settings,
        onDidReceiveNotificationResponse: (response) {
          _dispatchPayload(response.payload);
        },
      );
      const channel = AndroidNotificationChannel(
        'estate_access_alerts',
        'Estate access alerts',
        description: 'Visitor access and invitation updates.',
        importance: Importance.high,
      );
      await _local
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>()
          ?.createNotificationChannel(channel);
      _foregroundSubscription =
          FirebaseMessaging.onMessage.listen(_showForeground);
      _openedSubscription =
          FirebaseMessaging.onMessageOpenedApp.listen(_handleTap);
      _available = true;
    } catch (_) {
      // No Firebase project configuration: push remains safely disabled.
      _available = false;
    }
  }

  Future<void> start(
    Dio api, {
    required void Function(String resourceId) onInvitationTap,
  }) async {
    _api = api;
    _onInvitationTap = onInvitationTap;
    await initialize();
    if (!_available) return;
    try {
      final messaging = FirebaseMessaging.instance;
      final permission = await messaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );
      if (permission.authorizationStatus == AuthorizationStatus.denied) {
        return;
      }
      final token = await messaging.getToken();
      if (token != null && token.isNotEmpty) {
        await _register(token);
      }
      await _tokenSubscription?.cancel();
      _tokenSubscription = messaging.onTokenRefresh.listen((token) {
        if (token.isNotEmpty) unawaited(_register(token));
      });
      final initial = await messaging.getInitialMessage();
      if (initial != null) _handleTap(initial);
    } catch (_) {
      // Permission or token failures must not block sign-in.
    }
  }

  Future<void> _register(String token) async {
    final api = _api;
    if (api == null) return;
    try {
      await api.post('devices/push-token/', data: {
        'token': token,
        'platform': Platform.isIOS ? 'ios' : 'android',
      });
    } catch (_) {
      // The persisted inbox remains available if push registration fails.
    }
  }

  Future<void> stop() async {
    final api = _api;
    if (api != null && _available) {
      try {
        final token = await FirebaseMessaging.instance.getToken();
        if (token != null && token.isNotEmpty) {
          await api.delete('devices/push-token/', data: {
            'token': token,
            'platform': Platform.isIOS ? 'ios' : 'android',
          });
        }
      } catch (_) {
        // Logout must complete even when the device is offline.
      }
    }
    await _tokenSubscription?.cancel();
    _tokenSubscription = null;
    _api = null;
    _onInvitationTap = null;
  }

  Future<void> _showForeground(RemoteMessage message) async {
    final notification = message.notification;
    if (notification == null) return;
    final safePayload = _safePayload(message.data);
    try {
      await _local.show(
        notification.hashCode,
        notification.title ?? 'Estate access update',
        notification.body ?? 'There is an update to your visitor access.',
        const NotificationDetails(
          android: AndroidNotificationDetails(
            'estate_access_alerts',
            'Estate access alerts',
            channelDescription: 'Visitor access and invitation updates.',
            importance: Importance.high,
            priority: Priority.high,
          ),
          iOS: DarwinNotificationDetails(),
        ),
        payload: jsonEncode(safePayload),
      );
    } catch (_) {
      // Foreground notification display is best-effort.
    }
  }

  void _handleTap(RemoteMessage message) {
    final safePayload = _safePayload(message.data);
    final resourceId = safePayload['resource_id'];
    if (resourceId is String) _onInvitationTap?.call(resourceId);
  }

  Map<String, String> _safePayload(Map<String, dynamic> data) {
    final id = data['resource_id'] ?? data['invitation_id'];
    if (id is String &&
        RegExp(r'^[0-9a-fA-F-]{36}$').hasMatch(id) &&
        !data.containsKey('credential') &&
        !data.containsKey('token')) {
      return {'resource_id': id};
    }
    return {};
  }

  void _dispatchPayload(String? payload) {
    if (payload == null || payload.isEmpty) return;
    try {
      final decoded = jsonDecode(payload);
      if (decoded is Map) {
        final id = decoded['resource_id'];
        if (id is String &&
            RegExp(r'^[0-9a-fA-F-]{36}$').hasMatch(id)) {
          _onInvitationTap?.call(id);
        }
      }
    } catch (_) {
      // Ignore malformed or stale notification payloads.
    }
  }

  Future<void> dispose() async {
    await _foregroundSubscription?.cancel();
    await _openedSubscription?.cancel();
    await _tokenSubscription?.cancel();
  }
}
