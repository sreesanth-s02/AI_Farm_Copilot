import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app_theme.dart';
import 'package:mobile/app_shell.dart';
import 'package:mobile/services/api_service.dart';

void main() {
  testWidgets('AI Farm Copilot dashboard loads', (WidgetTester tester) async {
    final api = _FakeApiService();
    await tester.pumpWidget(
      MaterialApp(
        theme: farmTheme(),
        home: FarmDashboard(api: api),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('AI Farm Copilot'), findsOneWidget);
    expect(find.text('Good day, Farmer'), findsOneWidget);
    expect(find.text('Your farm today'), findsOneWidget);
    expect(find.text('Selected field'), findsOneWidget);
    expect(find.text('North Field'), findsWidgets);
    expect(find.text('Irrigation recommendation'), findsOneWidget);
    expect(find.text('Scan a plant leaf'), findsOneWidget);
  });

  testWidgets('shows review-required fertiliser assessment with partial NPK',
      (WidgetTester tester) async {
    await tester.pumpWidget(MaterialApp(
      theme: farmTheme(),
      home: FarmDashboard(api: _FakeApiService(advisory: 'REVIEW_REQUIRED')),
    ));
    await tester.pumpAndSettle();

    expect(find.text('Fertiliser assessment'), findsOneWidget);
    expect(find.text('REVIEW REQUIRED'), findsOneWidget);
    expect(find.text('Nitrogen: 40 unknown'), findsOneWidget);
    expect(find.text('Phosphorus: Unavailable'), findsOneWidget);
    expect(find.text('Potassium: 30 unknown'), findsOneWidget);
    expect(find.textContaining('The NPK record is partial.'), findsOneWidget);
    expect(find.textContaining('Confirm the soil test details.'), findsOneWidget);
    expect(find.textContaining('Test disclaimer.'), findsOneWidget);
  });

  testWidgets('shows insufficient-data fertiliser assessment honestly',
      (WidgetTester tester) async {
    await tester.pumpWidget(MaterialApp(
      theme: farmTheme(),
      home: FarmDashboard(api: _FakeApiService(advisory: 'INSUFFICIENT_DATA')),
    ));
    await tester.pumpAndSettle();

    expect(find.text('INSUFFICIENT DATA'), findsOneWidget);
    expect(find.text('Phosphorus: Unavailable'), findsOneWidget);
    expect(find.text('Unavailable'), findsWidgets);
  });
}

class _FakeApiService extends ApiService {
  _FakeApiService({this.advisory = 'REVIEW_REQUIRED'})
      : super(baseUrl: 'http://fake.test');

  final String advisory;

  static const _field = <String, dynamic>{
    'id': 1,
    'field_name': 'North Field',
    'area_acres': 12.5,
    'soil_type': 'Loam',
    'latitude': 10.123,
    'longitude': 76.456,
  };

  @override
  Future<List<Map<String, dynamic>>> getList(String path) async {
    switch (path) {
      case '/api/v1/fields/farm/1':
        return [_field];
      case '/api/v1/crops/field/1':
        return [
          {
            'crop_name': 'Tomato',
            'status': 'ACTIVE',
            'growth_stage': 'Flowering',
          },
        ];
      case '/api/v1/soil/field/1':
        return [
          {
            'moisture': 42.0,
            'ph': 6.5,
            'recorded_at': '2099-01-01T08:00:00Z',
          },
        ];
      default:
        throw ApiException('Unexpected fake list path: $path');
    }
  }

  @override
  Future<Map<String, dynamic>> getObject(String path) async {
    switch (path) {
      case '/api/v1/fields/1':
        return _field;
      case '/api/v1/weather/current?latitude=10.123&longitude=76.456':
        return {
          'current': {
            'time': '2099-01-01T09:00:00Z',
            'data': {
              'temperature_2m': {'value': 28.5},
              'relative_humidity_2m': {'value': 70},
              'wind_speed_10m': {'value': 8.0},
            },
          },
          'fetched_at': '2099-01-01T09:00:00Z',
          'cache': 'test',
        };
      case '/api/v1/weather/hourly?latitude=10.123&longitude=76.456':
        return {
          'hourly': {
            'times': ['2099-01-01T10:00:00Z'],
            'data': {
              'precipitation': {'values': [0.0]},
              'temperature_2m': {'values': [29.0]},
            },
          },
        };
      case '/api/v1/recommendations/irrigation/1':
        return {
          'advisory': 'IRRIGATION_REVIEW',
          'message': 'Review irrigation based on current field conditions.',
          'reasons': [
            {'factor': 'Soil moisture', 'value': 42.0, 'unit': '%'},
          ],
          'warnings': <String>[],
          'decision_basis': 'Test recommendation',
        };
      case '/api/v1/recommendations/fertiliser/1':
        return {
          'field': _field,
          'crop': {'name': 'Tomato'},
          'soil': {
            'recorded_at': '2099-01-01T08:00:00Z',
            'measurements': {
              'nitrogen': {'value': 40, 'unit': 'unknown'},
              'phosphorus': {'value': null, 'unit': null},
              'potassium': {'value': 30, 'unit': 'unknown'},
            },
          },
          'advisory': advisory,
          'warnings': ['The NPK record is partial.'],
          'next_steps': ['Confirm the soil test details.'],
          'disclaimer': 'Test disclaimer.',
        };
      default:
        throw ApiException('Unexpected fake object path: $path');
    }
  }
}
