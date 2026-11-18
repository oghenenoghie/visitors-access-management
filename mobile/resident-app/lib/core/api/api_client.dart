import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  ApiClient(this.storage, {String? baseUrl})
      : dio = Dio(BaseOptions(
          baseUrl: (baseUrl ??
                      const String.fromEnvironment('API_BASE_URL',
                          defaultValue: 'http://10.0.2.2:8000/api/v1/'))
                  .replaceAll(RegExp(r'/$'), '') +
              '/',
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 20),
          sendTimeout: const Duration(seconds: 20),
          headers: {'Accept': 'application/json'},
        )) {
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        if (options.extra['skipAuth'] != true) {
          final token = await storage.read(key: accessTokenKey);
          if (token != null && token.isNotEmpty)
            options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401 &&
            error.requestOptions.extra['skipAuth'] != true &&
            error.requestOptions.extra['retried'] != true) {
          final refreshed = await _refresh();
          if (refreshed) {
            final request = error.requestOptions;
            request.extra['retried'] = true;
            final token = await storage.read(key: accessTokenKey);
            request.headers['Authorization'] = 'Bearer $token';
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

  static const accessTokenKey = 'estate.access';
  static const refreshTokenKey = 'estate.refresh';
  final FlutterSecureStorage storage;
  final Dio dio;

  Future<bool> _refresh() async {
    final refresh = await storage.read(key: refreshTokenKey);
    if (refresh == null) return false;
    try {
      final response = await dio.post('auth/token/refresh/',
          data: {'refresh': refresh},
          options: Options(
              headers: {'Authorization': null}, extra: {'skipAuth': true}));
      final data = Map<String, dynamic>.from(response.data as Map);
      final access = data['access'] as String?;
      if (access == null) return false;
      await storage.write(key: accessTokenKey, value: access);
      final rotated = data['refresh'] as String?;
      if (rotated != null)
        await storage.write(key: refreshTokenKey, value: rotated);
      return true;
    } on DioException {
      await clearSession();
      return false;
    }
  }

  Future<void> saveSession(
      {required String access, required String refresh}) async {
    await storage.write(key: accessTokenKey, value: access);
    await storage.write(key: refreshTokenKey, value: refresh);
  }

  Future<void> clearSession() async {
    await storage.delete(key: accessTokenKey);
    await storage.delete(key: refreshTokenKey);
  }

  Future<bool> hasSession() async =>
      (await storage.read(key: accessTokenKey)) != null;
}
