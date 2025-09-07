class NewsItem {
  final String videoId;
  final String title;
  final String? description;
  final String? transcript;
  final String? summary;
  final String? thumbnailUrl;
  final String? videoUrl;
  final String channelId;
  final String channelName;
  final String? channelUrl;
  final DateTime? publishedAt;
  final DateTime? cachedAt;
  final DateTime? summaryCreatedAt;
  final String? summaryCreatedBy;

  NewsItem({
    required this.videoId,
    required this.title,
    this.description,
    this.transcript,
    this.summary,
    this.thumbnailUrl,
    this.videoUrl,
    required this.channelId,
    required this.channelName,
    this.channelUrl,
    this.publishedAt,
    this.cachedAt,
    this.summaryCreatedAt,
    this.summaryCreatedBy,
  });

  factory NewsItem.fromJson(Map<String, dynamic> json) {
    return NewsItem(
      videoId: json['video_id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'],
      transcript: json['transcript'],
      summary: json['summary'],
      thumbnailUrl: json['thumbnail_url'],
      videoUrl: json['video_url'],
      channelId: json['channel_id'] ?? '',
      channelName: json['channel_name'] ?? '',
      channelUrl: json['channel_url'],
      publishedAt: json['published_at'] != null 
          ? DateTime.tryParse(json['published_at']) 
          : null,
      cachedAt: json['cached_at'] != null 
          ? DateTime.tryParse(json['cached_at']) 
          : null,
      summaryCreatedAt: json['summary_created_at'] != null 
          ? DateTime.tryParse(json['summary_created_at']) 
          : null,
      summaryCreatedBy: json['summary_created_by'],
    );
  }

  bool get hasSummary => summary != null && summary!.isNotEmpty;
  bool get hasTranscript => transcript != null && transcript!.isNotEmpty;
}
