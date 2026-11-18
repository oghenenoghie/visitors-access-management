import 'dart:io';
import 'dart:ui' as ui;

import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:share_plus/share_plus.dart';

import '../../app.dart';
import '../../core/theme/app_theme.dart';
import 'invitation_repository.dart';

class PassScreen extends ConsumerStatefulWidget {
  const PassScreen({super.key, required this.invitationId});
  final String invitationId;
  @override
  ConsumerState<PassScreen> createState() => _PassScreenState();
}

class _PassScreenState extends ConsumerState<PassScreen> {
  Map<String, dynamic>? _invitation;
  Map<String, dynamic>? _credentials;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final api = ref.read(apiClientProvider);
      final repo = InvitationRepository(api, ref.read(secureStorageProvider));
      final invitationResponse =
          await api.dio.get('invitations/${widget.invitationId}/');
      final credentials = await repo.credentials(widget.invitationId);
      if (!mounted) return;
      setState(() {
        _invitation = Map<String, dynamic>.from(invitationResponse.data as Map);
        _credentials = credentials;
        _loading = false;
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'This invitation could not be loaded.';
          _loading = false;
        });
      }
    }
  }

  Future<void> _share() async {
    if (_invitation == null || _credentials == null) return;
    final start =
        DateTime.tryParse(_invitation!['valid_from']?.toString() ?? '');
    final end =
        DateTime.tryParse(_invitation!['valid_until']?.toString() ?? '');
    final message = [
      'ESTATE VISITOR PASS',
      'Visitor: ${_invitation!['visitor_name'] ?? 'Visitor'}',
      'Unit: ${_invitation!['unit_number'] ?? '—'}',
      'Access code: ${_credentials!['access_code']}',
      'Valid from: ${start == null ? '—' : DateFormat('d MMM yyyy, h:mm a').format(start.toLocal())}',
      'Valid until: ${end == null ? '—' : DateFormat('d MMM yyyy, h:mm a').format(end.toLocal())}',
      'QR token: ${_credentials!['qr_token']}',
      'Present this pass to security at the estate gate.',
    ].join('\n');
    final token = _credentials!['qr_token'] as String;
    final painter =
        QrPainter(data: token, version: QrVersions.auto, gapless: true);
    final imageData =
        await painter.toImageData(1024, format: ui.ImageByteFormat.png);
    if (imageData == null) return;
    final directory = await getTemporaryDirectory();
    final imageFile = File(
        '${directory.path}/estate-visitor-pass-${widget.invitationId}.png');
    await imageFile.writeAsBytes(imageData.buffer.asUint8List(), flush: true);
    await Share.shareXFiles(
      [XFile(imageFile.path)],
      text: message,
      subject: 'Estate visitor pass',
    );
  }

  Future<void> _cancel() async {
    await InvitationRepository(
            ref.read(apiClientProvider), ref.read(secureStorageProvider))
        .cancel(widget.invitationId);
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (_error != null || _invitation == null) {
      return Scaffold(
          appBar: AppBar(),
          body: Center(child: Text(_error ?? 'Invitation unavailable')));
    }
    final item = _invitation!;
    final credentials = _credentials;
    final start = DateTime.tryParse(item['valid_from']?.toString() ?? '');
    final end = DateTime.tryParse(item['valid_until']?.toString() ?? '');
    final active = item['status'] == 'active';
    return Scaffold(
      appBar: AppBar(title: const Text('Digital visitor pass')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: AppColors.line)),
            child: Column(children: [
              Container(
                  width: 52,
                  height: 52,
                  decoration: BoxDecoration(
                      color: AppColors.mint,
                      borderRadius: BorderRadius.circular(16)),
                  child: const Icon(Icons.verified_user_outlined,
                      color: AppColors.forest, size: 28)),
              const SizedBox(height: 14),
              const Text('VISITOR ACCESS PASS',
                  style: TextStyle(
                      fontSize: 11,
                      letterSpacing: 1.6,
                      fontWeight: FontWeight.w800,
                      color: AppColors.muted)),
              const SizedBox(height: 8),
              Text(item['visitor_name']?.toString() ?? 'Visitor',
                  style: const TextStyle(
                      fontSize: 23,
                      fontWeight: FontWeight.w800,
                      color: AppColors.ink)),
              const SizedBox(height: 5),
              Text('Unit ${item['unit_number'] ?? '—'}',
                  style: const TextStyle(color: AppColors.muted)),
              const SizedBox(height: 22),
              if (credentials != null)
                QrImageView(
                    data: credentials['qr_token'] as String,
                    size: 210,
                    backgroundColor: Colors.white)
              else
                const Padding(
                  padding: EdgeInsets.all(24),
                  child: Text(
                      'The original one-time QR credential is not stored on this device. Ask the resident who created the pass to share it.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: AppColors.amber)),
                ),
              const SizedBox(height: 12),
              const Text('MANUAL ACCESS CODE',
                  style: TextStyle(
                      fontSize: 10,
                      letterSpacing: 1.4,
                      color: AppColors.muted,
                      fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              Text(credentials?['access_code']?.toString() ?? '••••••••',
                  style: const TextStyle(
                      fontSize: 28,
                      letterSpacing: 6,
                      fontWeight: FontWeight.w900,
                      color: AppColors.ink)),
              const SizedBox(height: 20),
              _PassDetail(
                  label: 'Valid from',
                  value: start == null
                      ? '—'
                      : DateFormat('d MMM yyyy · h:mm a')
                          .format(start.toLocal())),
              _PassDetail(
                  label: 'Valid until',
                  value: end == null
                      ? '—'
                      : DateFormat('d MMM yyyy · h:mm a')
                          .format(end.toLocal())),
              _PassDetail(
                  label: 'Access type',
                  value: item['access_type']?.toString().replaceAll('_', ' ') ??
                      '—'),
              _PassDetail(
                  label: 'Status',
                  value: item['status']?.toString().toUpperCase() ?? '—'),
            ]),
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
              onPressed: credentials == null ? null : _share,
              icon: const Icon(Icons.share_outlined),
              label: const Text('Share visitor pass')),
          if (active) ...[
            const SizedBox(height: 10),
            OutlinedButton(
              onPressed: () async {
                final confirmed = await showDialog<bool>(
                  context: context,
                  builder: (dialogContext) => AlertDialog(
                    title: const Text('Cancel this pass?'),
                    content: const Text(
                        'The visitor will no longer be able to use these credentials.'),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(dialogContext, false),
                          child: const Text('Keep pass')),
                      FilledButton(
                          onPressed: () => Navigator.pop(dialogContext, true),
                          child: const Text('Cancel pass')),
                    ],
                  ),
                );
                if (confirmed == true) {
                  await _cancel();
                  if (!mounted) return;
                  context.pop();
                }
              },
              child: const Text('Cancel invitation'),
            ),
          ],
        ],
      ),
    );
  }
}

class _PassDetail extends StatelessWidget {
  const _PassDetail({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 7),
        child: Row(children: [
          Expanded(
              child:
                  Text(label, style: const TextStyle(color: AppColors.muted))),
          Text(value,
              style: const TextStyle(
                  fontWeight: FontWeight.w700, color: AppColors.ink)),
        ]),
      );
}
