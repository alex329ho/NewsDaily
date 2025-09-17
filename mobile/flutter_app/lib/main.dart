import 'package:flutter/material.dart';

import 'api_client.dart';
import 'widgets/headline_tile.dart';

void main() {
  runApp(const DailyNewsApp());
}

class DailyNewsApp extends StatelessWidget {
  const DailyNewsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DailyNews',
      theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
      home: const DailyNewsHomePage(),
    );
  }
}

class DailyNewsHomePage extends StatefulWidget {
  const DailyNewsHomePage({super.key});

  @override
  State<DailyNewsHomePage> createState() => _DailyNewsHomePageState();
}

class _DailyNewsHomePageState extends State<DailyNewsHomePage> {
  final DailyNewsApiClient _client = DailyNewsApiClient();
  final List<String> _defaultTopics = const ['finance', 'economy', 'politics'];
  final Set<String> _selectedTopics = <String>{'finance', 'economy', 'politics'};
  final TextEditingController _customTopicController = TextEditingController();
  final TextEditingController _regionController = TextEditingController();
  final TextEditingController _languageController = TextEditingController();

  final List<int> _hourOptions = const [4, 8, 12, 24];

  int _hours = 8;
  bool _loading = false;
  String? _error;
  SummaryResponse? _summary;

  @override
  void dispose() {
    _customTopicController.dispose();
    _regionController.dispose();
    _languageController.dispose();
    super.dispose();
  }

  void _toggleTopic(String topic) {
    setState(() {
      if (_selectedTopics.contains(topic)) {
        _selectedTopics.remove(topic);
      } else {
        _selectedTopics.add(topic);
      }
    });
  }

  void _addCustomTopic() {
    final String topic = _customTopicController.text.trim();
    if (topic.isEmpty) {
      return;
    }
    setState(() {
      _selectedTopics.add(topic);
      _customTopicController.clear();
    });
  }

  Future<void> _fetchSummary() async {
    if (_selectedTopics.isEmpty) {
      setState(() {
        _error = 'Select at least one topic.';
      });
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final SummaryResponse response = await _client.fetchSummary(
        topics: _selectedTopics.toList(),
        hours: _hours,
        region: _regionController.text.trim().isEmpty ? null : _regionController.text.trim(),
        language: _languageController.text.trim().isEmpty ? null : _languageController.text.trim(),
      );
      setState(() {
        _summary = response;
      });
    } catch (error) {
      setState(() {
        _summary = null;
        _error = error.toString();
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  Widget _buildTopicChips() {
    final Iterable<Widget> chips = _defaultTopics.map((String topic) {
      final bool selected = _selectedTopics.contains(topic);
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4),
        child: FilterChip(
          label: Text(topic),
          selected: selected,
          onSelected: (_) => _toggleTopic(topic),
        ),
      );
    });
    return Wrap(children: chips.toList());
  }

  Widget _buildSummaryView() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Text(
          _error!,
          style: const TextStyle(color: Colors.red),
        ),
      );
    }
    if (_summary == null) {
      return const Center(child: Text('Tap "Fetch Summary" to load the latest news.'));
    }
    if (_summary!.headlines.isEmpty) {
      return Center(
        child: Text(
          _summary!.summary.isEmpty ? 'No news available.' : _summary!.summary,
          textAlign: TextAlign.center,
        ),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          _summary!.summary,
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        const SizedBox(height: 16),
        Text('Headlines', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        ..._summary!.headlines.map((Headline headline) => HeadlineTile(headline: headline)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('DailyNews Mobile')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text('Topics', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              _buildTopicChips(),
              const SizedBox(height: 8),
              Row(
                children: <Widget>[
                  Expanded(
                    child: TextField(
                      controller: _customTopicController,
                      decoration: const InputDecoration(
                        labelText: 'Add custom topic',
                        border: OutlineInputBorder(),
                      ),
                      onSubmitted: (_) => _addCustomTopic(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: _addCustomTopic,
                    child: const Text('Add'),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: <Widget>[
                  Expanded(
                    child: InputDecorator(
                      decoration: const InputDecoration(
                        labelText: 'Hours',
                        border: OutlineInputBorder(),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<int>(
                          value: _hours,
                          isExpanded: true,
                          items: _hourOptions
                              .map(
                                (int value) => DropdownMenuItem<int>(
                                  value: value,
                                  child: Text('$value hours'),
                                ),
                              )
                              .toList(),
                          onChanged: (int? value) {
                            if (value != null) {
                              setState(() => _hours = value);
                            }
                          },
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _regionController,
                      decoration: const InputDecoration(
                        labelText: 'Region (optional)',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _languageController,
                decoration: const InputDecoration(
                  labelText: 'Language (optional)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _loading ? null : _fetchSummary,
                  child: const Text('Fetch Summary'),
                ),
              ),
              const SizedBox(height: 24),
              _buildSummaryView(),
            ],
          ),
        ),
      ),
    );
  }
}
