class Field {
  const Field({
    required this.id,
    this.name,
    this.areaAcres,
    this.soilType,
    this.latitude,
    this.longitude,
  });

  factory Field.fromJson(Map<String, dynamic> json) => Field(
        id: (json['id'] as num).toInt(),
        name: json['field_name'] as String?,
        areaAcres: json['area_acres'] as num?,
        soilType: json['soil_type'] as String?,
        latitude: json['latitude'] as num?,
        longitude: json['longitude'] as num?,
      );

  final int id;
  final String? name;
  final num? areaAcres;
  final String? soilType;
  final num? latitude;
  final num? longitude;
}
