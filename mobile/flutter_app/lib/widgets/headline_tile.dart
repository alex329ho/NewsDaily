import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api_client.dart';

class HeadlineTile extends StatelessWidget {
  const HeadlineTile({super.key, required this.headline});

  final Headline headline;

  Future<void> _openUrl(BuildContext context) async {
    final Uri uri = Uri.tryParse(headline.url) ?? Uri();
    if (uri.toString().isEmpty) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('No link available for this headline.')));
      return;
    }
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Could not open the link.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: ListTile(
        title: Text(headline.title.isEmpty ? 'Untitled' : headline.title),
        subtitle: Text(headline.sourceDomain.isEmpty
            ? headline.seenDate
            : '${headline.sourceDomain} • ${headline.seenDate}'),
        onTap: () => _openUrl(context),
        trailing: const Icon(Icons.open_in_new),
      ),
    );
  }
}
