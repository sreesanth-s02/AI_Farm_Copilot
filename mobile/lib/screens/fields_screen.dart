import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../widgets/common.dart';
class FieldsPage extends StatelessWidget {
  final bool loading;
  final String? error;
  final List<Map<String, dynamic>> fields;
  final int? selectedFieldId;
  final Map<String, dynamic>? field, crop, soil;
  final ValueChanged<int?> onSelect;
  final VoidCallback onRefresh;
  const FieldsPage({super.key, required this.loading, required this.error, required this.fields, required this.selectedFieldId, required this.field, required this.crop, required this.soil, required this.onSelect, required this.onRefresh});

  @override
  Widget build(BuildContext context) => PageFrame(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const Text('Your fields', style: TextStyle(fontSize: 25, fontWeight: FontWeight.bold, color: forestGreen)),
    const SizedBox(height: 5), const Text('Information retrieved from your farm API.', style: TextStyle(color: mutedText)),
    const SizedBox(height: 12), LoadError(loading: loading, error: error, onRetry: onRefresh),
    if (!loading && fields.isEmpty && error == null) const Text('No fields found.'),
    ...fields.map((f) {
      final id = (f['id'] as num).toInt();
      final selected = id == selectedFieldId;
      return Padding(padding: const EdgeInsets.only(bottom: 10), child: Panel(child: InkWell(
        onTap: () => onSelect(id), borderRadius: BorderRadius.circular(12),
        child: Padding(padding: const EdgeInsets.all(4), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [const Icon(Icons.landscape, color: leafGreen, size: 28), const SizedBox(width: 10), Expanded(child: Text('${f['field_name'] ?? 'Field $id'}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: forestGreen))), if (selected) const Icon(Icons.check_circle, color: leafGreen)]),
          const SizedBox(height: 8), Text('Area: ${showValue(f['area_acres'])} acres'), Text('Soil: ${showValue(f['soil_type'])}'),
          Text('Latitude / longitude: ${showValue(f['latitude'])}, ${showValue(f['longitude'])}'),
          if (selected) ...[
            const Divider(height: 20), Text('Crop: ${showValue(crop?['crop_name'])} • ${showValue(crop?['growth_stage'])}'),
            Text('Soil moisture: ${fmt(soil?['moisture'], suffix: '%')}'), Text('Soil pH: ${fmt(soil?['ph'])}'),
            Text('Latest reading: ${formatDate(soil?['recorded_at'])}'),
            if (isSoilReadingStale(soil?['recorded_at'])) const Padding(padding: EdgeInsets.only(top: 8), child: Text('This soil reading is over 24 hours old. Refresh the reading before relying on irrigation guidance.', style: TextStyle(color: Color(0xFF9A5A00), fontWeight: FontWeight.w600))),
          ],
        ])),
      )));
    }),
  ]));
}
