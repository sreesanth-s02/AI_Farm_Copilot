import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart';
import '../app_theme.dart';
import '../services/api_service.dart';
class DiseaseScannerPage extends StatefulWidget {
  const DiseaseScannerPage({super.key});

  @override
  State<DiseaseScannerPage> createState() => _DiseaseScannerPageState();
}

class _DiseaseScannerPageState extends State<DiseaseScannerPage> {
  // For Flutter Web on this same computer, use 127.0.0.1.
  // Android emulator/device networking will need a different base URL later.
  final ApiService _api = const ApiService();

  final ImagePicker _picker = ImagePicker();
  XFile? _selectedImage;
  bool _isLoading = false;
  String? _errorMessage;
  Map<String, dynamic>? _prediction;

  Future<void> _chooseImage() async {
    try {
      final image = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 90,
      );

      if (image == null || !mounted) return;

      setState(() {
        _selectedImage = image;
        _prediction = null;
        _errorMessage = null;
      });
    } catch (error, stackTrace) {
      debugPrint('IMAGE PICKER ERROR: $error');
      debugPrintStack(stackTrace: stackTrace);

      if (!mounted) return;

      setState(() {
        _errorMessage = 'Image selection failed: $error';
      });
    }
  }

  Future<void> _analyzeImage() async {
    final image = _selectedImage;
    if (image == null) {
      setState(() => _errorMessage = 'Choose a leaf image first.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _prediction = null;
    });

    try {
      final bytes = await image.readAsBytes();
      final filename = image.name;
      final extension = filename.contains('.')
          ? filename.split('.').last.toLowerCase()
          : '';

      final MediaType? mediaType = switch (extension) {
        'jpg' || 'jpeg' => MediaType('image', 'jpeg'),
        'png' => MediaType('image', 'png'),
        'webp' => MediaType('image', 'webp'),
        _ => null,
      };

      if (mediaType == null) {
        if (!mounted) return;
        setState(() {
          _errorMessage = 'Please choose a JPG, PNG, or WEBP image.';
        });
        return;
      }

      if (bytes.isEmpty) {
        if (!mounted) return;
        setState(() {
          _errorMessage = 'The selected image is empty. Please choose another.';
        });
        return;
      }

      if (bytes.length > 10 * 1024 * 1024) {
        if (!mounted) return;
        setState(() {
          _errorMessage = 'Image must be 10 MB or smaller.';
        });
        return;
      }

      final body = await _api.predictDisease(
        bytes: bytes,
        filename: filename,
        contentType: mediaType,
      );
      if (!mounted) return;
      setState(() => _prediction = body);
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _errorMessage =
            'Could not reach the disease prediction API. Check that the '
            'backend is running and browser access is allowed.';
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  String _formatProbability(dynamic value) {
    if (value is num) {
      final probability = value > 1 ? value / 100 : value;
      return '${(probability * 100).toStringAsFixed(2)}%';
    }
    return 'Not available';
  }

  String _prettyClassName(String value) {
    return value.replaceAll('___', ' — ').replaceAll('_', ' ');
  }

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 700;
    final predictions = _prediction?['top_predictions'];
    final topPredictions = predictions is List ? predictions : const [];

    return SingleChildScrollView(
      padding: EdgeInsets.all(wide ? 28 : 18),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 850),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Plant disease scanner',
                style: TextStyle(
                  color: forestGreen,
                  fontSize: 27,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 7),
              const Text(
                'Upload a clear photo of a plant leaf to get an AI-generated prediction.',
                style: TextStyle(color: mutedText, fontSize: 15),
              ),
              const SizedBox(height: 22),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFFE2E9E0)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (_selectedImage == null)
                      Container(
                        width: double.infinity,
                        height: 210,
                        decoration: BoxDecoration(
                          color: pageBackground,
                          borderRadius: BorderRadius.circular(15),
                        ),
                        child: const Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.add_photo_alternate_outlined,
                              color: leafGreen,
                              size: 54,
                            ),
                            SizedBox(height: 12),
                            Text(
                              'Choose a leaf photo',
                              style: TextStyle(
                                color: forestGreen,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            SizedBox(height: 5),
                            Text(
                              'JPG, PNG or WEBP · Maximum 10 MB',
                              style: TextStyle(color: mutedText, fontSize: 12),
                            ),
                          ],
                        ),
                      )
                    else
                      FutureBuilder<Uint8List>(
                        future: _selectedImage!.readAsBytes(),
                        builder: (context, snapshot) {
                          if (!snapshot.hasData) {
                            return const SizedBox(
                              height: 210,
                              child: Center(child: CircularProgressIndicator()),
                            );
                          }
                          return ClipRRect(
                            borderRadius: BorderRadius.circular(15),
                            child: Image.memory(
                              snapshot.data!,
                              width: double.infinity,
                              height: 270,
                              fit: BoxFit.contain,
                            ),
                          );
                        },
                      ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _isLoading ? null : _chooseImage,
                            icon: const Icon(Icons.photo_library_outlined),
                            label: Text(
                              _selectedImage == null
                                  ? 'Choose photo'
                                  : 'Change photo',
                            ),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: forestGreen,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              side: const BorderSide(color: forestGreen),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(13),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: FilledButton.icon(
                            onPressed: _selectedImage == null || _isLoading
                                ? null
                                : _analyzeImage,
                            icon: _isLoading
                                ? const SizedBox(
                                    width: 17,
                                    height: 17,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  )
                                : const Icon(Icons.search),
                            label: Text(_isLoading ? 'Analyzing…' : 'Analyze'),
                            style: FilledButton.styleFrom(
                              backgroundColor: forestGreen,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(13),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              if (_errorMessage != null) ...[
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFEEEE),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0xFFF2CACA)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.error_outline, color: Colors.red),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _errorMessage!,
                          style: const TextStyle(color: Color(0xFF8B2424)),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              if (_prediction != null) ...[
                const SizedBox(height: 24),
                const Text(
                  'Prediction result',
                  style: TextStyle(
                    color: forestGreen,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEAF3E9),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: const Color(0xFFD2E4D1)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'MODEL PREDICTION',
                        style: TextStyle(
                          color: leafGreen,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _prettyClassName(
                          (_prediction!['predicted_class'] ?? 'Unknown')
                              .toString(),
                        ),
                        style: const TextStyle(
                          color: forestGreen,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Model output: ${_formatProbability(_prediction!['model_probability'])}',
                        style: const TextStyle(color: mutedText),
                      ),
                    ],
                  ),
                ),
                if (topPredictions.isNotEmpty) ...[
                  const SizedBox(height: 18),
                  const Text(
                    'Other top predictions',
                    style: TextStyle(
                      color: forestGreen,
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...topPredictions.map<Widget>((item) {
                    if (item is! Map) return const SizedBox.shrink();
                    final label =
                        (item['class_name'] ??
                                item['class'] ??
                                item['predicted_class'] ??
                                item['disease'] ??
                                item['disease_name'] ??
                                item['label'] ??
                                item['name'] ??
                                'Unknown prediction')
                            .toString();
                    final probability =
                        item['probability'] ??
                        item['model_probability'] ??
                        item['confidence'] ??
                        item['score'] ??
                        item['prob'];
                    return Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.all(13),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFFE2E9E0)),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              _prettyClassName(label),
                              style: const TextStyle(
                                color: forestGreen,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Text(
                            _formatProbability(probability),
                            style: const TextStyle(
                              color: mutedText,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                ],
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF5DF),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0xFFF0DFB6)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.info_outline, color: Color(0xFF9A7136)),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          (_prediction!['disclaimer'] ??
                                  'This is an AI-generated prototype prediction, not a confirmed diagnosis. Model probabilities are not verified diagnostic confidence. Consult an agricultural expert before treatment.')
                              .toString(),
                          style: const TextStyle(
                            color: Color(0xFF725525),
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
