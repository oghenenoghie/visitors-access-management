import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../api/api_client.dart';

class AuthRepository {
  AuthRepository(this.api, this.storage);
  final ApiClient api;
  final FlutterSecureStorage storage;

  Future<Map<String, dynamic>> signIn(
      {required String email, required String password}) async {
    final response = await api.dio.post('auth/login/',
        data: {'email': email.trim(), 'password': password},
        options: Options(headers: {'Authorization': null}));
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> beginTwoFactorSetup(String challenge) async {
    final response = await api.dio.post('auth/2fa/setup/',
        data: {'challenge_token': challenge},
        options: Options(headers: {'Authorization': null}));
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> completeTwoFactor(
      {required String challenge,
      required String code,
      required bool setup}) async {
    final response = await api.dio.post(
        setup ? 'auth/2fa/confirm/' : 'auth/2fa/verify/',
        data: {'challenge_token': challenge, 'code': code.trim()},
        options: Options(headers: {'Authorization': null}));
    final result = Map<String, dynamic>.from(response.data as Map);
    if (result['status'] == 'authenticated') {
      await api.saveSession(
          access: result['access'] as String,
          refresh: result['refresh'] as String);
    }
    return result;
  }

  Future<void> signOut() async {
    final refresh = await storage.read(key: ApiClient.refreshTokenKey);
    try {
      if (refresh != null)
        await api.dio.post('auth/logout/', data: {'refresh': refresh});
    } finally {
      await api.clearSession();
    }
  }
}
