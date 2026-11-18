import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../app.dart';
import '../../core/theme/app_theme.dart';
import 'invitation_repository.dart';

class CreateInvitationScreen extends ConsumerStatefulWidget {
  const CreateInvitationScreen({super.key});
  @override
  ConsumerState<CreateInvitationScreen> createState() => _CreateInvitationScreenState();
}

class _CreateInvitationScreenState extends ConsumerState<CreateInvitationScreen> {
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _vehicle = TextEditingController();
  List<Map<String, dynamic>> _units = [];
  String? _unitId;
  String _accessType = 'single_use';
  int _maxUses = 2;
  DateTime _from = DateTime.now().add(const Duration(minutes: 5));
  DateTime _until = DateTime.now().add(const Duration(hours: 4));
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadUnits();
  }

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    _vehicle.dispose();
    super.dispose();
  }

  Future<void> _loadUnits() async {
    try {
      final rows = await InvitationRepository(ref.read(apiClientProvider), ref.read(secureStorageProvider)).activeUnits();
      if (!mounted) return;
      setState(() {
        _units = rows;
        if (rows.isNotEmpty) _unitId = rows.first['unit_id']?.toString();
        _loading = false;
      });
    } on DioException {
      if (mounted) setState(() { _error = 'Could not load your approved home or unit assignment.'; _loading = false; });
    }
  }

  Future<void> _pickDate({required bool start}) async {
    final current = start ? _from : _until;
    final selected = await showDatePicker(
      context: context,
      initialDate: current,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (selected == null || !mounted) return;
    final time = await showTimePicker(context: context, initialTime: TimeOfDay.fromDateTime(current));
    if (time == null) return;
    setState(() {
      final value = DateTime(selected.year, selected.month, selected.day, time.hour, time.minute);
      if (start) {
        _from = value;
        if (!_until.isAfter(_from)) _until = _from.add(const Duration(hours: 1));
      } else {
        _until = value;
      }
    });
  }

  Future<void> _create() async {
    if (_name.text.trim().isEmpty || _unitId == null || !_until.isAfter(_from)) {
      setState(() => _error = 'Enter the visitor name, choose a home and set a valid time window.');
      return;
    }
    setState(() { _saving = true; _error = null; });
    try {
      final result = await InvitationRepository(ref.read(apiClientProvider), ref.read(secureStorageProvider)).create(
        visitorName: _name.text,
        visitorPhone: _phone.text,
        vehicleRegistration: _vehicle.text,
        unitId: _unitId!,
        validFrom: _from,
        validUntil: _until,
        accessType: _accessType,
        maxUses: _accessType == 'multi_use' ? _maxUses : null,
      );
      final invitation = Map<String, dynamic>.from(result['invitation'] as Map);
      if (mounted) context.go('/passes/${invitation['id']}');
    } on DioException catch (error) {
      final data = error.response?.data;
      if (mounted) setState(() => _error = data is Map ? (data['detail'] ?? data['error']?['message'] ?? 'Invitation could not be created.').toString() : 'Unable to connect to the service.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('New visitor pass')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
              children: [
                const Text('VISITOR DETAILS', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1.3, fontSize: 11, color: AppColors.muted)),
                const SizedBox(height: 12),
                TextField(controller: _name, textCapitalization: TextCapitalization.words, decoration: const InputDecoration(labelText: 'Visitor full name')),
                const SizedBox(height: 12),
                TextField(controller: _phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Phone number (optional)')),
                const SizedBox(height: 12),
                TextField(controller: _vehicle, textCapitalization: TextCapitalization.characters, decoration: const InputDecoration(labelText: 'Vehicle registration (optional)')),
                const SizedBox(height: 24),
                const Text('VISIT DETAILS', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1.3, fontSize: 11, color: AppColors.muted)),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: _unitId,
                  decoration: const InputDecoration(labelText: 'Home / unit'),
                  items: _units.map((unit) => DropdownMenuItem<String>(
                    value: unit['unit_id']?.toString(),
                    child: Text(unit['unit_number']?.toString() ?? 'Assigned unit'),
                  )).toList(),
                  onChanged: (value) => setState(() => _unitId = value),
                ),
                const SizedBox(height: 12),
                _DateField(label: 'Valid from', value: _from, onTap: () => _pickDate(start: true)),
                const SizedBox(height: 12),
                _DateField(label: 'Valid until', value: _until, onTap: () => _pickDate(start: false)),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: _accessType,
                  decoration: const InputDecoration(labelText: 'Access type'),
                  items: const [
                    DropdownMenuItem(value: 'single_use', child: Text('Single entry')),
                    DropdownMenuItem(value: 'multi_use', child: Text('Multiple entries')),
                  ],
                  onChanged: (value) => setState(() => _accessType = value ?? 'single_use'),
                ),
                if (_accessType == 'multi_use') ...[
                  const SizedBox(height: 12),
                  DropdownButtonFormField<int>(
                    value: _maxUses,
                    decoration: const InputDecoration(labelText: 'Maximum entries'),
                    items: [2, 3, 5, 10, 20].map((count) => DropdownMenuItem(value: count, child: Text('$count entries'))).toList(),
                    onChanged: (value) => setState(() => _maxUses = value ?? 2),
                  ),
                ],
                if (_units.isEmpty)
                  const Padding(padding: EdgeInsets.only(top: 14), child: Text('No active home assignment was found. Contact estate management to confirm your unit.', style: TextStyle(color: AppColors.amber))),
                if (_error != null) ...[
                  const SizedBox(height: 14),
                  Text(_error!, style: const TextStyle(color: AppColors.danger)),
                ],
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: _saving || _units.isEmpty ? null : _create,
                  child: _saving ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Text('Create visitor pass'),
                ),
                const SizedBox(height: 10),
                const Text('Your QR token and manual access code are shown once and stored securely on this device for later sharing.', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: AppColors.muted, height: 1.5)),
              ],
            ),
    );
  }
}

class _DateField extends StatelessWidget {
  const _DateField({required this.label, required this.value, required this.onTap});
  final String label;
  final DateTime value;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onTap,
    borderRadius: BorderRadius.circular(14),
    child: InputDecorator(
      decoration: InputDecoration(labelText: label, suffixIcon: const Icon(Icons.calendar_month_outlined)),
      child: Text(DateFormat('EEE, d MMM yyyy · h:mm a').format(value)),
    ),
  );
}
