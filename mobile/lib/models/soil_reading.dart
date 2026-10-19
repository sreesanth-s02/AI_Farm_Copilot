class SoilReading {
  const SoilReading({this.moisture, this.ph, this.recordedAt});

  factory SoilReading.fromJson(Map<String, dynamic> json) => SoilReading(
        moisture: json['moisture'] as num?,
        ph: json['ph'] as num?,
        recordedAt: json['recorded_at'] as String?,
      );

  final num? moisture;
  final num? ph;
  final String? recordedAt;
}
