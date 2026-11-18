import 'package:material_ui/material_ui.dart';
import 'core/notifications/push_notification_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await PushNotificationService.instance.initialize();
  runApp(const ProviderScope(child: EstateResidentApp()));
}
