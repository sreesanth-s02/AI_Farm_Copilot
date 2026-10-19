class Weather {
  const Weather({this.current, this.hourly});

  factory Weather.fromJson(
    Map<String, dynamic> current,
    Map<String, dynamic> hourly,
  ) =>
      Weather(current: current, hourly: hourly);

  final Map<String, dynamic>? current;
  final Map<String, dynamic>? hourly;
}
