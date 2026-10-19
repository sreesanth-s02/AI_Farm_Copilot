class Crop {
  const Crop({this.name, this.status, this.growthStage});

  factory Crop.fromJson(Map<String, dynamic> json) => Crop(
        name: json['crop_name'] as String?,
        status: json['status'] as String?,
        growthStage: json['growth_stage'] as String?,
      );

  final String? name;
  final String? status;
  final String? growthStage;
}
