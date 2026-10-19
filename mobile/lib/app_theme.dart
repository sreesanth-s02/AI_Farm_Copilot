import 'package:flutter/material.dart';

const forestGreen = Color(0xFF1B4D3E);
const leafGreen = Color(0xFF3D7A57);
const pageBackground = Color(0xFFF6F8F3);
const mutedText = Color(0xFF68756B);
const apiBaseUrl = 'http://127.0.0.1:8000';
const int demoFarmId = 1;

String showValue(dynamic v, {String suffix = ''}) => v == null ? 'Unavailable' : '$v$suffix';
String fmt(dynamic v, {int digits = 1, String suffix = ''}) => v is num ? '${v.toStringAsFixed(digits)}$suffix' : 'Unavailable';
String formatDate(dynamic raw) {
  if (raw == null) return 'Unknown';
  final d = DateTime.tryParse('$raw');
  if (d == null) return '$raw';
  return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';
}
bool isSoilReadingStale(dynamic raw) {
  if (raw == null) return true;
  final recorded = DateTime.tryParse('$raw');
  if (recorded == null) return true;
  final age = DateTime.now().difference(recorded);
  return age.isNegative || age > const Duration(hours: 24);
}
dynamic nested(Map<String, dynamic>? m, List<String> keys) {
  dynamic value = m;
  for (final key in keys) {
    if (value is Map) {
      value = value[key];
    } else {
      return null;
    }
  }
  return value;
}
List<int> futureForecastIndexes(List times) {
  final now = DateTime.now();
  final indexes = <int>[];
  for (var i = 0; i < times.length; i++) {
    final time = DateTime.tryParse('${times[i]}');
    if (time != null && !time.isBefore(now.subtract(const Duration(hours: 1)))) indexes.add(i);
  }
  return indexes;
}

ThemeData farmTheme() => ThemeData(
  useMaterial3: true,
  scaffoldBackgroundColor: pageBackground,
  colorScheme: ColorScheme.fromSeed(seedColor: forestGreen),
  appBarTheme: const AppBarTheme(backgroundColor: pageBackground, foregroundColor: forestGreen),
);
