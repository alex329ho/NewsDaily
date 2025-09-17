import 'dart:convert';

import 'package:http/http.dart' as http;

import 'config.dart';

class Headline {
  Headline({
    required this.title,
    required this.url,
    required this.sourceDomain,
    required this.seenDate,
  });

  final String title;
  final String url;
  final String sourceDomain;
  final String seenDate;

  factory Headline.fromJson(Map<String, dynamic> json) {
    return Headline(
      title: json['title']?.toString() ?? '',
      url: json['url']?.toString() ?? '',
      sourceDomain: json['source_domain']?.toString() ?? '',
      seenDate: json['seendate']?.toString() ?? '',
    );
  }
}

class SummaryResponse {
  SummaryResponse({
    required this.topics,
    required this.hours,
    required this.summary,
    required this.headlines,
    required this.region,
    required this.language,
  });

  final List<String> topics;
  final int hours;
  final String summary;
  final List<Headline> headlines;
  final String? region;
  final String? language;

  factory SummaryResponse.fromJson(Map<String, dynamic> json) {
    final dynamic topicsValue = json['topics'];
    final List<String> topics = topicsValue is List
        ? topicsValue.map((e) => e.toString()).toList()
        : topicsValue.toString().split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();
    final List<dynamic> rawHeadlines = (json['headlines'] as List<dynamic>? ?? <dynamic>[]);
    return SummaryResponse(
      topics: topics,
      hours: int.tryParse(json['hours']?.toString() ?? '0') ?? 0,
      summary: json['summary']?.toString() ?? 'No news available.',
      region: json['region']?.toString(),
      language: json['language']?.toString(),
      headlines: rawHeadlines
          .map((dynamic item) => Headline.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}

class DailyNewsApiClient {
  DailyNewsApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Future<SummaryResponse> fetchSummary({
    required List<String> topics,
    required int hours,
    String? region,
    String? language,
  }) async {
    final Uri uri = Uri.parse('$baseUrl/summary').replace(queryParameters: <String, String?>{
      'topics': topics.join(','),
      'hours': hours.toString(),
      'region': region,
      'language': language,
    });

    final http.Response response = await _client.get(uri).timeout(const Duration(seconds: 15));
    if (response.statusCode != 200) {
      throw Exception('Backend returned ${response.statusCode}');
    }

    final Map<String, dynamic> data = json.decode(response.body) as Map<String, dynamic>;
    return SummaryResponse.fromJson(data);
  }
}
