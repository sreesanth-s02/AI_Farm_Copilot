class IrrigationRecommendation {
  const IrrigationRecommendation({
    this.advisory,
    this.message,
    this.reasons,
    this.warnings,
  });

  factory IrrigationRecommendation.fromJson(Map<String, dynamic> json) =>
      IrrigationRecommendation(
        advisory: json['advisory'] as String?,
        message: json['message'] as String?,
        reasons: json['reasons'] as List?,
        warnings: json['warnings'] as List?,
      );

  final String? advisory;
  final String? message;
  final List? reasons;
  final List? warnings;
}
