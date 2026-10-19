import 'package:flutter/material.dart';

import 'app_shell.dart';
import 'app_theme.dart';

void main() => runApp(const AIFarmCopilotApp());

class AIFarmCopilotApp extends StatelessWidget {
  const AIFarmCopilotApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'AI Farm Copilot',
        debugShowCheckedModeBanner: false,
        theme: farmTheme(),
        home: const FarmDashboard(),
      );
}
