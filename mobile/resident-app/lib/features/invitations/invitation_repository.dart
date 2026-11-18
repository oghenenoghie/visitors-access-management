import 'dart:convert';
import 'dart:math';

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../core/api/api_client.dart';

class InvitationRepository {
  InvitationRepository(this.api, this.storage);
  final ApiClient api;
  final FlutterSecureStorage storage;

  Future<List<Map<String, dynamic>>> activeUnits() async {
    final response = await api.dio.get('resident-unit-assignments/', queryParameters: {'status': 'active'});
    final data = response.data;
    final rows = data is Map ? data['results'] as List? ?? [] : data as List? ?? [];
    return rows.map((row) => Map<String, dynamic>.from(row as Map)).toList();
  }

  Future<List<Map<String, dynamic>>> invitations() async {
    final response = await api.dio.get('invitations/');
    final data = response.data;
    final rows = data is Map ? data['results'] as List? ?? [] : data as List? ?? [];
    return rows.map((row) => Map<String, dynamic>.from(row as Map)).toList();
  }

  Future<Map<String, dynamic>> create({
    required String visitorName,
    required String visitorPhone,
    required String vehicleRegistration,
    required String unitId,
    required DateTime validFrom,
    required DateTime validUntil,
    required String accessType,
    int? maxUses,
  }) async {
    final payload = <String, dynamic>{
      'visitor_name': visitorName.trim(),
      'visitor_phone': visitorPhone.trim(),
      'vehicle_registration': vehicleRegistration.trim(),
      'unit': unitId,
      'valid_from': validFrom.toUtc().toIso8601String(),
      'valid_until': validUntil.toUtc().toIso8601String(),
      'access_type': accessType,
      if (maxUses != null) 'max_uses': maxUses,
    };
    final random = Random.secure();
    final idempotencyKey = List.generate(32, (_) => random.nextInt(16).toRadixString(16)).join();
    final response = await api.dio.post(
      'invitations/',
      data: payload,
      options: Options(headers: {'Idempotency-Key': idempotencyKey}),
    );
    final result = Map<String, dynamic>.from(response.data as Map);
    final invitation = Map<String, dynamic>.from(result['invitation'] as Map);
    final id = invitation['id'] as String;
    await storage.write(
      key: 'estate.pass.$id',
      value: jsonEncode({'qr_token': result['qr_token'], 'access_code': result['access_code']}),
    );
    return result;
  }

  Future<Map<String, dynamic>?> credentials(String id) async {
    final value = await storage.read(key: 'estate.pass.$id');
    if (value == null) return null;
    return Map<String, dynamic>.from(jsonDecode(value) as Map);
  }

  Future<void> cancel(String id) async {
    await api.dio.post('invitations/$id/cancel/');
  }
}
