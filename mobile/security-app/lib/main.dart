import 'dart:async';

import 'package:dio/dio.dart';
import 'package:material_ui/material_ui.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'push_notification_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await PushNotificationService.instance.initialize();
  runApp(const SecurityGateApp());
}

const _storage = FlutterSecureStorage();
const _accessKey = 'estate.access';
const _refreshKey = 'estate.refresh';
const _apiBase = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000/api/v1/',
);
const _gateDeviceId = String.fromEnvironment('GATE_DEVICE_ID');

final _api = _GateApi();

class _GateApi {
  _GateApi()
      : dio = Dio(BaseOptions(
          baseUrl: '${_apiBase.replaceAll(RegExp(r'/$'), '')}/',
          connectTimeout: const Duration(seconds: 12),
          receiveTimeout: const Duration(seconds: 18),
          headers: {'Accept': 'application/json'},
        )) {
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        if (options.extra['skipAuth'] != true) {
          final token = await _storage.read(key: _accessKey);
          if (token != null) options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401 &&
            error.requestOptions.extra['retried'] != true &&
            error.requestOptions.extra['skipAuth'] != true) {
          final refreshed = await refresh();
          if (refreshed) {
            final request = error.requestOptions;
            request.extra['retried'] = true;
            request.headers['Authorization'] =
                'Bearer ${await _storage.read(key: _accessKey)}';
            try {
              handler.resolve(await dio.fetch(request));
              return;
            } catch (_) {
              await clearSession();
            }
          }
        }
        handler.next(error);
      },
    ));
  }

  final Dio dio;

  Future<bool> refresh() async {
    final token = await _storage.read(key: _refreshKey);
    if (token == null) return false;
    try {
      final response = await dio.post(
        'auth/token/refresh/',
        data: {'refresh': token},
        options: Options(extra: {'skipAuth': true}),
      );
      final data = Map<String, dynamic>.from(response.data as Map);
      await _storage.write(key: _accessKey, value: data['access'] as String);
      final rotated = data['refresh'] as String?;
      if (rotated != null)
        await _storage.write(key: _refreshKey, value: rotated);
      return true;
    } on DioException {
      await clearSession();
      return false;
    }
  }

  Future<void> saveSession(Map<String, dynamic> data) async {
    await _storage.write(key: _accessKey, value: data['access'] as String);
    await _storage.write(key: _refreshKey, value: data['refresh'] as String);
    unawaited(PushNotificationService.instance.start(dio));
  }

  Future<void> clearSession() async {
    await PushNotificationService.instance.stop();
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }

  Future<bool> hasSession() async =>
      await _storage.read(key: _accessKey) != null;

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await dio.post(
      'auth/login/',
      data: {'email': email.trim(), 'password': password},
      options: Options(extra: {'skipAuth': true}),
    );
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> twoFactor(
      String challenge, String code, bool setup) async {
    final response = await dio.post(
      setup ? 'auth/2fa/confirm/' : 'auth/2fa/verify/',
      data: {'challenge_token': challenge, 'code': code.trim()},
      options: Options(extra: {'skipAuth': true}),
    );
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> verify(String credential) async {
    final response = await dio.post('gate/verify/', data: {
      'gate_device': _gateDeviceId,
      'credential': credential,
    });
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> checkIn(String credential) async {
    final response = await dio.post('gate/check-in/', data: {
      'gate_device': _gateDeviceId,
      'credential': credential,
    });
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> checkOut(String invitation) async {
    final response = await dio.post('gate/check-out/', data: {
      'gate_device': _gateDeviceId,
      'invitation': invitation,
    });
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<List<Map<String, dynamic>>> activity() async {
    final response = await dio.get('gate/activity/');
    final data = response.data;
    if (data is List)
      return data.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    if (data is Map && data['results'] is List) {
      return (data['results'] as List)
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
    }
    return [];
  }

  Future<Map<String, dynamic>> overrideAccess(
      String invitation, String reason) async {
    final response = await dio.post('gate/override/', data: {
      'gate_device': _gateDeviceId,
      'invitation': invitation,
      'reason': reason,
    });
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<void> logout() async {
    await PushNotificationService.instance.stop();
    final refreshToken = await _storage.read(key: _refreshKey);
    try {
      if (refreshToken != null) {
        await dio.post('auth/logout/', data: {'refresh': refreshToken});
      }
    } finally {
      await clearSession();
    }
  }
}

class SecurityGateApp extends StatefulWidget {
  const SecurityGateApp({super.key});
  @override
  State<SecurityGateApp> createState() => _SecurityGateAppState();
}

class _SecurityGateAppState extends State<SecurityGateApp> {
  bool _signedIn = false;
  bool _checking = true;

  @override
  void initState() {
    super.initState();
    _restore();
  }

  Future<void> _restore() async {
    final signedIn = await _api.hasSession();
    if (signedIn) unawaited(PushNotificationService.instance.start(_api.dio));
    if (mounted)
      setState(() {
        _signedIn = signedIn;
        _checking = false;
      });
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Estate Gate',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF173B5E)),
          scaffoldBackgroundColor: const Color(0xFFF4F7FA),
          cardTheme: const CardThemeData(elevation: 0, color: Colors.white),
        ),
        home: _checking
            ? const Scaffold(body: Center(child: CircularProgressIndicator()))
            : _signedIn
                ? GateHome(onLogout: () async {
                    await _api.logout();
                    if (mounted) setState(() => _signedIn = false);
                  })
                : GateLogin(
                    onAuthenticated: () => setState(() => _signedIn = true)),
      );
}

class GateLogin extends StatefulWidget {
  const GateLogin({super.key, required this.onAuthenticated});
  final VoidCallback onAuthenticated;
  @override
  State<GateLogin> createState() => _GateLoginState();
}

class _GateLoginState extends State<GateLogin> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _code = TextEditingController();
  String? _challenge;
  String? _error;
  bool _setup = false;
  bool _busy = false;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _code.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_challenge == null) {
        final result = await _api.login(_email.text, _password.text);
        if (result['status'] == 'authenticated') {
          await _api.saveSession(result);
          widget.onAuthenticated();
        } else if (result['status'] == 'two_factor_required' ||
            result['status'] == 'two_factor_setup_required') {
          _challenge = result['challenge_token'] as String;
          _setup = result['status'] == 'two_factor_setup_required';
          if (_setup) {
            final setup = await _api.dio.post('auth/2fa/setup/',
                data: {'challenge_token': _challenge},
                options: Options(extra: {'skipAuth': true}));
            _error = 'Authenticator setup secret: ${setup.data['secret']}';
          }
        } else {
          _error = 'The server returned an unsupported sign-in state.';
        }
      } else {
        final result = await _api.twoFactor(_challenge!, _code.text, _setup);
        if (result['status'] == 'authenticated') {
          await _api.saveSession(result);
          widget.onAuthenticated();
        }
      }
    } on DioException catch (e) {
      _error = e.response?.data is Map
          ? (e.response?.data['detail'] ?? 'Sign-in failed.').toString()
          : 'Unable to reach the access server.';
    } catch (_) {
      _error = 'Sign-in could not be completed.';
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
            child: Center(
                child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(Icons.shield_moon_outlined,
                      size: 54, color: Color(0xFF173B5E)),
                  const SizedBox(height: 24),
                  Text(
                      _challenge == null
                          ? 'Security officer sign in'
                          : 'Authenticator verification',
                      style: Theme.of(context)
                          .textTheme
                          .headlineSmall
                          ?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 8),
                  const Text(
                      'Use your assigned security account. Gate permissions are checked by the server.'),
                  const SizedBox(height: 24),
                  if (_challenge == null) ...[
                    TextField(
                        controller: _email,
                        keyboardType: TextInputType.emailAddress,
                        decoration: const InputDecoration(
                            labelText: 'Email address',
                            border: OutlineInputBorder())),
                    const SizedBox(height: 12),
                    TextField(
                        controller: _password,
                        obscureText: true,
                        decoration: const InputDecoration(
                            labelText: 'Password',
                            border: OutlineInputBorder())),
                  ] else
                    TextField(
                        controller: _code,
                        autofocus: true,
                        keyboardType: TextInputType.number,
                        maxLength: 8,
                        decoration: const InputDecoration(
                            labelText: 'Authenticator code',
                            border: OutlineInputBorder())),
                  if (_error != null)
                    Padding(
                        padding: const EdgeInsets.only(top: 12),
                        child: Text(_error!,
                            style: const TextStyle(color: Colors.red))),
                  const SizedBox(height: 20),
                  FilledButton(
                      onPressed: _busy ? null : _submit,
                      child: _busy
                          ? const CircularProgressIndicator()
                          : Text(_challenge == null ? 'Sign in' : 'Verify')),
                  if (_challenge != null)
                    TextButton(
                        onPressed: () => setState(() {
                              _challenge = null;
                              _code.clear();
                              _error = null;
                            }),
                        child: const Text('Use another account')),
                ]),
          ),
        ))),
      );
}

class GateHome extends StatefulWidget {
  const GateHome({super.key, required this.onLogout});
  final VoidCallback onLogout;
  @override
  State<GateHome> createState() => _GateHomeState();
}

class _GateHomeState extends State<GateHome> {
  int _tab = 0;
  String? _error;

  @override
  void initState() {
    super.initState();
    PushNotificationService.instance.setTapHandler((resourceId) {
      if (mounted) setState(() => _tab = 1);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_gateDeviceId.isEmpty) {
      return Scaffold(
          appBar: AppBar(title: const Text('Estate Gate')),
          body: const Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                  'Gate device is not configured. Build with --dart-define=GATE_DEVICE_ID=<registered-gate-uuid>. No access operation can proceed without an assigned gate device.')));
    }
    return Scaffold(
      appBar: AppBar(title: const Text('Estate Gate'), actions: [
        IconButton(
            tooltip: 'Sign out',
            onPressed: widget.onLogout,
            icon: const Icon(Icons.logout)),
      ]),
      body: IndexedStack(index: _tab, children: [
        GateOperations(onError: (message) => setState(() => _error = message)),
        const GateActivity(),
      ]),
      bottomNavigationBar: NavigationBar(
          selectedIndex: _tab,
          onDestinationSelected: (index) => setState(() => _tab = index),
          destinations: const [
            NavigationDestination(
                icon: Icon(Icons.qr_code_scanner), label: 'Verify'),
            NavigationDestination(icon: Icon(Icons.history), label: 'Activity'),
          ]),
      floatingActionButton: _error == null
          ? null
          : FloatingActionButton.small(
              onPressed: () => setState(() => _error = null),
              child: const Icon(Icons.close)),
    );
  }
}

class GateOperations extends StatefulWidget {
  const GateOperations({super.key, required this.onError});
  final ValueChanged<String> onError;
  @override
  State<GateOperations> createState() => _GateOperationsState();
}

class _GateOperationsState extends State<GateOperations> {
  final _manual = TextEditingController();
  bool _busy = false;
  bool _scannerOpen = false;
  Map<String, dynamic>? _result;
  String? _credential;

  @override
  void dispose() {
    _manual.dispose();
    super.dispose();
  }

  Future<void> _verify(String value) async {
    final credential = value.trim();
    if (credential.isEmpty || _busy) return;
    setState(() {
      _busy = true;
      _result = null;
      _credential = credential;
      _scannerOpen = false;
    });
    try {
      final result = await _api.verify(credential);
      if (mounted) setState(() => _result = result);
    } on DioException catch (e) {
      widget.onError(e.response?.data is Map
          ? (e.response?.data['detail'] ?? 'Verification failed.').toString()
          : 'Live verification unavailable. Do not admit the visitor; contact the supervisor.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _checkIn() async {
    if (_credential == null || _busy) return;
    setState(() => _busy = true);
    try {
      final event = await _api.checkIn(_credential!);
      final accepted =
          event['status'] == 'accepted' || event['status'] == 'overridden';
      if (mounted) {
        setState(() => _result = {
              'result': accepted ? 'ENTRY_RECORDED' : 'ENTRY_REJECTED',
              'visitor_name': event['visitor_name'],
              'event': event,
            });
      }
    } on DioException catch (e) {
      widget.onError(e.response?.data is Map
          ? (e.response?.data['detail'] ?? 'Check-in failed.').toString()
          : 'Could not record entry. Confirm the live connection and retry safely.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Color _statusColor(String status) =>
      status == 'VALID' || status == 'ENTRY_RECORDED'
          ? const Color(0xFF137A4B)
          : const Color(0xFFB42318);

  @override
  Widget build(BuildContext context) {
    final status = _result?['result']?.toString() ?? '';
    final valid = status == 'VALID';
    return ListView(padding: const EdgeInsets.all(20), children: [
      Text('Visitor verification',
          style: Theme.of(context)
              .textTheme
              .headlineSmall
              ?.copyWith(fontWeight: FontWeight.w800)),
      const SizedBox(height: 6),
      const Text(
          'Scan the visitor pass or enter the 8-digit access code. Decisions are verified live.'),
      const SizedBox(height: 20),
      FilledButton.icon(
          onPressed:
              _busy ? null : () => setState(() => _scannerOpen = !_scannerOpen),
          icon: const Icon(Icons.qr_code_scanner),
          label: Text(_scannerOpen ? 'Close scanner' : 'Scan QR pass')),
      if (_scannerOpen)
        Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: SizedBox(
                height: 280,
                child: ClipRRect(
                    borderRadius: BorderRadius.circular(18),
                    child: MobileScanner(onDetect: (capture) {
                      final value = capture.barcodes.firstOrNull?.rawValue;
                      if (value != null && value.isNotEmpty && !_busy)
                        _verify(value);
                    })))),
      const SizedBox(height: 18),
      TextField(
          controller: _manual,
          keyboardType: TextInputType.number,
          maxLength: 8,
          decoration: const InputDecoration(
              labelText: 'Manual access code',
              hintText: 'Enter visitor code',
              border: OutlineInputBorder())),
      OutlinedButton(
          onPressed: _busy ? null : () => _verify(_manual.text),
          child: const Text('Verify access code')),
      if (_busy)
        const Padding(
            padding: EdgeInsets.all(24),
            child: Center(child: CircularProgressIndicator())),
      if (_result != null)
        Card(
            margin: const EdgeInsets.only(top: 18),
            child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        Icon(
                            valid || status == 'ENTRY_RECORDED'
                                ? Icons.verified
                                : Icons.gpp_bad,
                            color: _statusColor(status),
                            size: 30),
                        const SizedBox(width: 10),
                        Expanded(
                            child: Text(_label(status),
                                style: TextStyle(
                                    fontWeight: FontWeight.w800,
                                    fontSize: 18,
                                    color: _statusColor(status)))),
                      ]),
                      if (_result?['visitor_name'] != null)
                        Padding(
                            padding: const EdgeInsets.only(top: 12),
                            child: Text('Visitor: ${_result!['visitor_name']}',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w600))),
                      if (_result?['unit'] != null)
                        Text('Unit: ${_result!['unit']}'),
                      if (_result?['valid_until'] != null)
                        Text('Valid until: ${_result!['valid_until']}'),
                      if (valid)
                        Padding(
                            padding: const EdgeInsets.only(top: 16),
                            child: SizedBox(
                                width: double.infinity,
                                child: FilledButton.icon(
                                    onPressed: _busy ? null : _checkIn,
                                    icon: const Icon(Icons.login),
                                    label:
                                        const Text('Confirm visitor entry')))),
                      if (status == 'ENTRY_RECORDED')
                        const Padding(
                            padding: EdgeInsets.only(top: 10),
                            child: Text('Entry was recorded by the server.',
                                style: TextStyle(color: Color(0xFF137A4B)))),
                    ]))),
      const SizedBox(height: 14),
      TextButton(
          onPressed: () => setState(() {
                _result = null;
                _credential = null;
                _manual.clear();
              }),
          child: const Text('Clear and scan next visitor')),
    ]);
  }

  String _label(String status) => switch (status) {
        'VALID' => 'Credential valid',
        'EXPIRED' => 'Pass expired',
        'CANCELLED' => 'Pass cancelled',
        'REVOKED' => 'Pass revoked',
        'ALREADY_USED' => 'Pass already used',
        'NOT_YET_VALID' => 'Pass not yet valid',
        'ALREADY_CHECKED_IN' => 'Visitor already inside',
        'INVALID' => 'Invalid access credential',
        'ENTRY_RECORDED' => 'Entry recorded',
        'ENTRY_REJECTED' => 'Entry rejected',
        _ => 'Verification unavailable',
      };
}

class GateActivity extends StatefulWidget {
  const GateActivity({super.key});
  @override
  State<GateActivity> createState() => _GateActivityState();
}

class _GateActivityState extends State<GateActivity> {
  late Future<List<Map<String, dynamic>>> _future = _api.activity();

  Future<void> _refresh() async {
    setState(() => _future = _api.activity());
    await _future;
  }

  Future<void> _checkout(String invitation) async {
    try {
      await _api.checkOut(invitation);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Visitor exit recorded.')));
        await _refresh();
      }
    } on DioException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e.response?.data is Map
                ? (e.response?.data['detail'] ?? 'Check-out failed.').toString()
                : 'Could not record visitor exit.')));
      }
    }
  }

  @override
  Widget build(BuildContext context) =>
      FutureBuilder<List<Map<String, dynamic>>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting)
            return const Center(child: CircularProgressIndicator());
          if (snapshot.hasError)
            return Center(
                child: TextButton(
                    onPressed: _refresh,
                    child: const Text('Unable to load activity. Retry')));
          final events = snapshot.data ?? [];
          if (events.isEmpty) {
            return RefreshIndicator(
                onRefresh: _refresh,
                child: ListView(children: const [
                  SizedBox(height: 140),
                  Icon(Icons.history, size: 42),
                  Center(child: Text('No gate activity yet.'))
                ]));
          }
          return RefreshIndicator(
              onRefresh: _refresh,
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: events.length,
                itemBuilder: (context, index) {
                  final event = events[index];
                  final invitation = event['invitation']?.toString();
                  final entry = event['event_type'] == 'entry';
                  final accepted = event['status'] == 'accepted' ||
                      event['status'] == 'overridden';
                  return Card(
                      child: ListTile(
                    leading: Icon(entry ? Icons.login : Icons.logout,
                        color: accepted ? const Color(0xFF137A4B) : Colors.red),
                    title: Text(event['visitor_name']?.toString() ??
                        'Visitor access event'),
                    subtitle: Text(
                        '${event['event_type']} · ${event['status']} · ${event['occurred_at']}'),
                    trailing: entry && accepted && invitation != null
                        ? IconButton(
                            tooltip: 'Record exit',
                            icon: const Icon(Icons.exit_to_app),
                            onPressed: () => _checkout(invitation))
                        : null,
                  ));
                },
              ));
        },
      );
}
