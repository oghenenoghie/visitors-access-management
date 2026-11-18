import 'package:dio/dio.dart';
import 'package:material_ui/material_ui.dart';
import 'package:intl/intl.dart';

class NotificationInboxScreen extends StatefulWidget {
  const NotificationInboxScreen({super.key, required this.api});
  final Dio api;

  @override
  State<NotificationInboxScreen> createState() =>
      _NotificationInboxScreenState();
}

class _NotificationInboxScreenState extends State<NotificationInboxScreen> {
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;
  String? _error;
  bool _unreadOnly = false;
  final Set<String> _marking = {};

  int _unreadCount = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  List<Map<String, dynamic>> _parseRows(dynamic value) {
    final rows = value is Map ? value['results'] : value;
    if (rows is! List) return [];
    return rows
        .whereType<Map>()
        .map((row) => Map<String, dynamic>.from(row))
        .toList();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final responses = await Future.wait([
        widget.api.get('notifications/'),
        widget.api.get('notifications/unread-count/'),
      ]);
      if (!mounted) return;
      setState(() {
        _items = _parseRows(responses[0].data);
        _unreadCount =
            (responses[1].data as Map)['unread_count'] as int? ?? 0;
        _loading = false;
      });
    } on DioException catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.response?.statusCode == 401
            ? 'Your session has expired. Sign in again.'
            : 'We could not load your notifications. Please retry.';
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'We could not load your notifications. Please retry.';
        _loading = false;
      });
    }
  }

  Future<void> _markRead(Map<String, dynamic> item) async {
    final id = item['id']?.toString();
    if (id == null || id.isEmpty || item['read_at'] != null) return;
    setState(() => _marking.add(id));
    try {
      final response = await widget.api.post('notifications/$id/read/');
      if (!mounted) return;
      final updated = Map<String, dynamic>.from(response.data as Map);
      setState(() {
        final index = _items.indexWhere((entry) => entry['id'] == id);
        if (index >= 0) {
          final wasUnread = _items[index]['read_at'] == null;
          _items[index] = updated;
          if (wasUnread && updated['read_at'] != null && _unreadCount > 0) {
            _unreadCount--;
          }
        }
        _marking.remove(id);
      });
    } on DioException {
      if (!mounted) return;
      setState(() => _marking.remove(id));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not mark this notification as read.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final visible = _unreadOnly
        ? _items.where((item) => item['read_at'] == null).toList()
        : _items;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          IconButton(
            tooltip: 'Refresh notifications',
            onPressed: _loading ? null : _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    '$_unreadCount unread',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                ),
                FilterChip(
                  label: const Text('Unread only'),
                  selected: _unreadOnly,
                  onSelected: (value) => setState(() => _unreadOnly = value),
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(_error!),
                            const SizedBox(height: 12),
                            OutlinedButton(
                              onPressed: _load,
                              child: const Text('Retry'),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _load,
                        child: visible.isEmpty
                            ? ListView(
                                children: [
                                  const SizedBox(height: 110),
                                  Icon(
                                    Icons.notifications_none_rounded,
                                    size: 44,
                                    color: Theme.of(context).colorScheme.outline,
                                  ),
                                  const SizedBox(height: 12),
                                  Center(
                                    child: Text(_unreadOnly
                                        ? 'You are all caught up.'
                                        : 'No notifications yet.'),
                                  ),
                                ],
                              )
                            : ListView.separated(
                                padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
                                itemCount: visible.length,
                                separatorBuilder: (_, __) =>
                                    const SizedBox(height: 8),
                                itemBuilder: (context, index) {
                                  final item = visible[index];
                                  final isUnread = item['read_at'] == null;
                                  final id = item['id']?.toString() ?? '';
                                  final createdAt = DateTime.tryParse(
                                    item['created_at']?.toString() ?? '',
                                  );
                                  final marking = _marking.contains(id);
                                  return Card(
                                    child: ListTile(
                                      contentPadding:
                                          const EdgeInsets.symmetric(
                                        horizontal: 16,
                                        vertical: 8,
                                      ),
                                      leading: CircleAvatar(
                                        backgroundColor: isUnread
                                            ? Theme.of(context)
                                                .colorScheme
                                                .primaryContainer
                                            : Theme.of(context)
                                                .colorScheme
                                                .surfaceContainerHighest,
                                        child: Icon(
                                          isUnread
                                              ? Icons.notifications_active_outlined
                                              : Icons.notifications_none_rounded,
                                        ),
                                      ),
                                      title: Text(
                                        item['title']?.toString() ??
                                            'Estate update',
                                        style: TextStyle(
                                          fontWeight: isUnread
                                              ? FontWeight.w800
                                              : FontWeight.w500,
                                        ),
                                      ),
                                      subtitle: Padding(
                                        padding: const EdgeInsets.only(top: 5),
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Text(item['body']?.toString() ?? ''),
                                            const SizedBox(height: 5),
                                            Text(
                                              createdAt == null
                                                  ? 'Date unavailable'
                                                  : DateFormat(
                                                      'd MMM yyyy · h:mm a',
                                                    ).format(createdAt.toLocal()),
                                              style: Theme.of(context)
                                                  .textTheme
                                                  .labelSmall,
                                            ),
                                          ],
                                        ),
                                      ),
                                      trailing: isUnread
                                          ? marking
                                              ? const SizedBox(
                                                  width: 22,
                                                  height: 22,
                                                  child:
                                                      CircularProgressIndicator(
                                                    strokeWidth: 2,
                                                  ),
                                                )
                                              : IconButton(
                                                  tooltip: 'Mark as read',
                                                  onPressed: () =>
                                                      _markRead(item),
                                                  icon: const Icon(
                                                    Icons.mark_email_read_outlined,
                                                  ),
                                                )
                                          : const Icon(
                                              Icons.check_circle_outline,
                                              size: 20,
                                            ),
                                      onTap: isUnread
                                          ? () => _markRead(item)
                                          : null,
                                    ),
                                  );
                                },
                              ),
                      ),
          ),
        ],
      ),
    );
  }
}
