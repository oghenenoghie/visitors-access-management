import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../app.dart';
import '../../core/theme/app_theme.dart';
import '../invitations/invitation_repository.dart';

class VisitorHistoryScreen extends ConsumerStatefulWidget {
  const VisitorHistoryScreen({super.key});
  @override
  ConsumerState<VisitorHistoryScreen> createState() =>
      _VisitorHistoryScreenState();
}

class _VisitorHistoryScreenState extends ConsumerState<VisitorHistoryScreen> {
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;
  String? _error;
  String _filter = 'all';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final rows = await InvitationRepository(
              ref.read(apiClientProvider), ref.read(secureStorageProvider))
          .invitations();
      if (mounted)
        setState(() {
          _items = rows;
          _loading = false;
        });
    } catch (_) {
      if (mounted)
        setState(() {
          _error = 'Could not load visitor history.';
          _loading = false;
        });
    }
  }

  @override
  Widget build(BuildContext context) {
    final visible = _filter == 'all'
        ? _items
        : _items.where((item) => item['status'] == _filter).toList();
    return Scaffold(
      appBar: AppBar(title: const Text('Visitor history')),
      body: Column(children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
          child: Row(children: [
            _FilterChip(
                label: 'All',
                value: 'all',
                selected: _filter,
                onSelected: (value) => setState(() => _filter = value)),
            _FilterChip(
                label: 'Active',
                value: 'active',
                selected: _filter,
                onSelected: (value) => setState(() => _filter = value)),
            _FilterChip(
                label: 'Cancelled',
                value: 'cancelled',
                selected: _filter,
                onSelected: (value) => setState(() => _filter = value)),
            _FilterChip(
                label: 'Completed',
                value: 'completed',
                selected: _filter,
                onSelected: (value) => setState(() => _filter = value)),
          ]),
        ),
        Expanded(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _error != null
                  ? Center(
                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                      Text(_error!),
                      const SizedBox(height: 12),
                      OutlinedButton(
                          onPressed: _load, child: const Text('Retry'))
                    ]))
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: visible.isEmpty
                          ? ListView(children: const [
                              SizedBox(height: 110),
                              Icon(Icons.history,
                                  size: 42, color: AppColors.muted),
                              SizedBox(height: 12),
                              Center(
                                  child: Text(
                                      'No visitors found for this filter.'))
                            ])
                          : ListView.separated(
                              padding: const EdgeInsets.fromLTRB(16, 4, 16, 28),
                              itemCount: visible.length,
                              separatorBuilder: (_, __) =>
                                  const SizedBox(height: 8),
                              itemBuilder: (context, index) {
                                final item = visible[index];
                                final date = DateTime.tryParse(
                                    item['valid_from']?.toString() ?? '');
                                final status =
                                    item['status']?.toString() ?? 'unknown';
                                return Card(
                                    child: ListTile(
                                  leading: const CircleAvatar(
                                      backgroundColor: AppColors.mint,
                                      child: Icon(Icons.person_outline,
                                          color: AppColors.forest)),
                                  title: Text(
                                      item['visitor_name']?.toString() ??
                                          'Visitor',
                                      style: const TextStyle(
                                          fontWeight: FontWeight.w700)),
                                  subtitle: Text(
                                      'Unit ${item['unit_number'] ?? '—'} · ${date == null ? 'Date unavailable' : DateFormat('d MMM yyyy, h:mm a').format(date.toLocal())}'),
                                  trailing: Text(status,
                                      style: TextStyle(
                                          color: status == 'active'
                                              ? AppColors.forest
                                              : AppColors.muted,
                                          fontSize: 11,
                                          fontWeight: FontWeight.w700)),
                                  onTap: () =>
                                      context.push('/passes/${item['id']}'),
                                ));
                              },
                            ),
                    ),
        ),
      ]),
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip(
      {required this.label,
      required this.value,
      required this.selected,
      required this.onSelected});
  final String label;
  final String value;
  final String selected;
  final ValueChanged<String> onSelected;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(right: 8),
        child: ChoiceChip(
            label: Text(label),
            selected: selected == value,
            onSelected: (_) => onSelected(value)),
      );
}
