import 'package:flutter/material.dart';

import 'features/home/home_screen.dart';

class FoodLensApp extends StatelessWidget {
  const FoodLensApp({super.key});

  @override
  Widget build(BuildContext context) {
    const ink = Color(0xFF17201B);
    const canvas = Color(0xFFF4F1E9);
    final textTheme = ThemeData.light().textTheme.apply(
      fontFamily: 'Vazirmatn',
      bodyColor: ink,
      displayColor: ink,
    );

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'FoodLens',
      locale: const Locale('fa'),
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF237A57),
          surface: canvas,
        ),
        fontFamily: 'Vazirmatn',
        scaffoldBackgroundColor: canvas,
        textTheme: textTheme,
        appBarTheme: AppBarTheme(
          backgroundColor: canvas,
          foregroundColor: ink,
          elevation: 0,
          titleTextStyle: textTheme.titleLarge?.copyWith(
            color: ink,
            fontWeight: FontWeight.w800,
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            minimumSize: const Size.fromHeight(54),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            textStyle: const TextStyle(fontWeight: FontWeight.w700),
          ),
        ),
        cardTheme: CardThemeData(
          margin: EdgeInsets.zero,
          elevation: 0,
          color: Colors.white.withValues(alpha: 0.72),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
            side: const BorderSide(color: Color(0xFFE1DDD2)),
          ),
        ),
        useMaterial3: true,
      ),
      home: const Directionality(
        textDirection: TextDirection.rtl,
        child: HomeScreen(),
      ),
    );
  }
}
