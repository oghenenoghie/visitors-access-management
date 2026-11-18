import 'package:dio/dio.dart';
import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../app.dart';
import '../../core/theme/app_theme.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});
  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  Map<String, dynamic>? _user;
  Map<String, dynamic>? _resident;
  List<Map<String, dynamic>> _invitations = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  List<Map<String, dynamic>> _rows(dynamic value) {
    final items = value is Map ? value['results'] : value;
    if (items is! List) return [];
    return items.map((item) => Map<String, dynamic>.from(item as Map)).toList();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final dio = ref.read(apiClientProvider).dio;
      final responses = await Future.wait([
        dio.get('auth/me/'),
        dio.get('residents/'),
        dio.get('invitations/')
      ]);
      final residents = _rows(responses[1].data);
      setState(() {
        _user = Map<String, dynamic>.from(responses[0].data as Map);
        _resident = residents.isEmpty ? null : residents.first;
        _invitations = _rows(responses[2].data);
        _loading = false;
      });
    } on DioException catch (error) {
      setState(() {
        _error = error.response?.statusCode == 403
            ? 'Your resident access is not yet approved by estate management.'
            : 'We could not load your home information. Pull down to retry.';
        _loading = false;
      });
    }
  }

  Future<void> _signOut() async {
    await ref.read(authRepositoryProvider).signOut();
    if (mounted) context.go('/login');
  }

  @override
  Widget build(BuildContext context) {
    final firstName = (_user?['first_name'] as String?)?.trim() ?? '';
    final activeCount =
        _invitations.where((item) => item['status'] == 'active').length;
    final recent = _invitations.take(5).toList();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Estate Access'),
        actions: [
          IconButton(
              onPressed: () => context.push('/notifications'),
              icon: const Icon(Icons.notifications_outlined),
              tooltip: 'Notifications'),
          IconButton(
              onPressed: _load,
              icon: const Icon(Icons.refresh_rounded),
              tooltip: 'Refresh'),
          IconButton(
              onPressed: _signOut,
              icon: const Icon(Icons.logout_rounded),
              tooltip: 'Sign out'),
          const SizedBox(width: 8),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
                children: [
                  Text('YOUR HOME',
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          letterSpacing: 1.6,
                          color: AppColors.muted,
                          fontWeight: FontWeight.w700)),
                  const SizedBox(height: 8),
                  Text('Hello${firstName.isEmpty ? '' : ', $firstName'} 👋',
                      style: Theme.of(context)
                          .textTheme
                          .headlineMedium
                          ?.copyWith(
                              fontWeight: FontWeight.w800,
                              color: AppColors.ink)),
                  const SizedBox(height: 6),
                  const Text('Your visitors, made simple and secure.',
                      style: TextStyle(color: AppColors.muted)),
                  const SizedBox(height: 22),
                  if (_error != null)
                    _MessageCard(message: _error!, onRetry: _load)
                  else ...[
                    _EstateCard(resident: _resident, user: _user),
                    const SizedBox(height: 18),
                    FilledButton.icon(
                        onPressed: () => context.push('/invitations/new'),
                        icon: const Icon(Icons.add_rounded),
                        label: const Text('Create visitor pass')),
                    const SizedBox(height: 22),
                    Row(children: [
                      Expanded(
                          child: _MetricCard(
                              label: 'Active passes',
                              value: activeCount.toString(),
                              icon: Icons.confirmation_number_outlined)),
                      const SizedBox(width: 12),
                      Expanded(
                          child: _MetricCard(
                              label: 'All invitations',
                              value: _invitations.length.toString(),
                              icon: Icons.groups_2_outlined)),
                    ]),
                    const SizedBox(height: 28),
                    Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Recent invitations',
                              style: Theme.of(context)
                                  .textTheme
                                  .titleLarge
                                  ?.copyWith(fontWeight: FontWeight.w800)),
                          TextButton(
                              onPressed: () => context.push('/history'),
                              child: const Text('View all')),
                        ]),
                    const SizedBox(height: 12),
                    if (recent.isEmpty)
                      const _EmptyState()
                    else
                      ...recent.map((item) => Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: _InvitationTile(item: item))),
                  ],
                ],
              ),
            ),
    );
  }
}

class _EstateCard extends StatelessWidget {
  const _EstateCard({required this.resident, required this.user});
  final Map<String, dynamic>? resident;
  final Map<String, dynamic>? user;

  @override
  Widget build(BuildContext context) {
    final memberships = user?['memberships'];
    final fallback = memberships is List && memberships.isNotEmpty
        ? (memberships.first as Map)['estate_code']?.toString() ??
            'Resident account'
        : 'Resident account';
    final estate = resident?['estate_name']?.toString() ?? fallback;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
            colors: [AppColors.ink, AppColors.forest],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Row(children: [
        Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: .14),
                borderRadius: BorderRadius.circular(15)),
            child: const Icon(Icons.home_work_outlined, color: Colors.white)),
        const SizedBox(width: 14),
        Expanded(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('RESIDENT PROFILE',
              style: TextStyle(
                  color: Colors.white70,
                  fontSize: 10,
                  letterSpacing: 1.4,
                  fontWeight: FontWeight.w700)),
          const SizedBox(height: 5),
          Text(estate,
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 17,
                  fontWeight: FontWeight.w800)),
          const SizedBox(height: 3),
          Text(resident?['status']?.toString().toUpperCase() ?? 'ACCOUNT',
              style: const TextStyle(color: Colors.white70, fontSize: 11)),
        ])),
        const Icon(Icons.verified_user_outlined, color: Colors.white70),
      ]),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard(
      {required this.label, required this.value, required this.icon});
  final String label;
  final String value;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Card(
          child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(icon, color: AppColors.forest),
          const SizedBox(height: 14),
          Text(value,
              style: const TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  color: AppColors.ink)),
          const SizedBox(height: 3),
          Text(label,
              style: const TextStyle(color: AppColors.muted, fontSize: 12)),
        ]),
      ));
}

class _InvitationTile extends StatelessWidget {
  const _InvitationTile({required this.item});
  final Map<String, dynamic> item;
  @override
  Widget build(BuildContext context) {
    final date = DateTime.tryParse(item['valid_from']?.toString() ?? '');
    final status = item['status']?.toString() ?? 'unknown';
    return Card(
        child: ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: const CircleAvatar(
          backgroundColor: AppColors.mint,
          child: Icon(Icons.person_outline, color: AppColors.forest)),
      title: Text(item['visitor_name']?.toString() ?? 'Visitor',
          style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Text(date == null
          ? 'Date not available'
          : DateFormat('EEE, d MMM · h:mm a').format(date.toLocal())),
      trailing: _StatusPill(status: status),
      onTap: () => context.push('/passes/${item['id']}'),
    ));
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.status});
  final String status;
  @override
  Widget build(BuildContext context) {
    final active = status == 'active';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
          color: active ? AppColors.mint : const Color(0xFFF1F2F2),
          borderRadius: BorderRadius.circular(30)),
      child: Text(status,
          style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: active ? AppColors.forest : AppColors.muted)),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();
  @override
  Widget build(BuildContext context) => const Padding(
        padding: EdgeInsets.symmetric(vertical: 32),
        child: Column(children: [
          Icon(Icons.event_available_outlined,
              size: 42, color: AppColors.muted),
          SizedBox(height: 10),
          Text('No invitations yet',
              style: TextStyle(fontWeight: FontWeight.w700)),
          SizedBox(height: 4),
          Text('Create a pass when you are expecting a visitor.',
              style: TextStyle(color: AppColors.muted),
              textAlign: TextAlign.center),
        ]),
      );
}

class _MessageCard extends StatelessWidget {
  const _MessageCard({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;
  @override
  Widget build(BuildContext context) => Card(
          child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(children: [
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 12),
          OutlinedButton(onPressed: onRetry, child: const Text('Try again'))
        ]),
      ));
}
