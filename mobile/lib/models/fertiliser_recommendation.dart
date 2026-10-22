class FertiliserMeasurement {
  const FertiliserMeasurement({this.value, this.unit, this.recordedAt});

  factory FertiliserMeasurement.fromJson(Map<String, dynamic> json) =>
      FertiliserMeasurement(
        value: json['value'] as num?,
        unit: json['unit'] as String?,
        recordedAt: json['recorded_at'] as String?,
      );

  final num? value;
  final String? unit;
  final String? recordedAt;
}

class FertiliserSoil {
  const FertiliserSoil({this.recordedAt, this.measurements = const {}});

  factory FertiliserSoil.fromJson(Map<String, dynamic> json) {
    final rawMeasurements = json['measurements'];
    final measurements = <String, FertiliserMeasurement>{};
    if (rawMeasurements is Map) {
      for (final entry in rawMeasurements.entries) {
        if (entry.key is String && entry.value is Map) {
          measurements[entry.key as String] =
              FertiliserMeasurement.fromJson(
            Map<String, dynamic>.from(entry.value as Map),
          );
        }
      }
    }
    return FertiliserSoil(
      recordedAt: json['recorded_at'] as String?,
      measurements: measurements,
    );
  }

  final String? recordedAt;
  final Map<String, FertiliserMeasurement> measurements;
}

class FertiliserRecommendation {
  const FertiliserRecommendation({
    this.field,
    this.crop,
    this.soil,
    this.advisory,
    this.reasons = const [],
    this.warnings = const [],
    this.nextSteps = const [],
    this.disclaimer,
  });

  factory FertiliserRecommendation.fromJson(Map<String, dynamic> json) {
    final rawReasons = json['reasons'];
    final reasons = rawReasons is List
        ? rawReasons.whereType<Map>().map(Map<String, dynamic>.from).toList()
        : <Map<String, dynamic>>[];
    final rawWarnings = json['warnings'];
    final warnings = rawWarnings is List
        ? rawWarnings.whereType<String>().toList()
        : <String>[];
    final rawNextSteps = json['next_steps'];
    final nextSteps = rawNextSteps is List
        ? rawNextSteps.whereType<String>().toList()
        : <String>[];
    final rawSoil = json['soil'];
    return FertiliserRecommendation(
      field: json['field'] is Map
          ? Map<String, dynamic>.from(json['field'] as Map)
          : null,
      crop: json['crop'] is Map
          ? Map<String, dynamic>.from(json['crop'] as Map)
          : null,
      soil: rawSoil is Map
          ? FertiliserSoil.fromJson(Map<String, dynamic>.from(rawSoil))
          : null,
      advisory: json['advisory'] as String?,
      reasons: reasons,
      warnings: warnings,
      nextSteps: nextSteps,
      disclaimer: json['disclaimer'] as String?,
    );
  }

  final Map<String, dynamic>? field;
  final Map<String, dynamic>? crop;
  final FertiliserSoil? soil;
  final String? advisory;
  final List<Map<String, dynamic>> reasons;
  final List<String> warnings;
  final List<String> nextSteps;
  final String? disclaimer;
}
