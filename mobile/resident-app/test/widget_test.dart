import 'package:estate_resident_app/core/theme/app_theme.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('resident theme uses the approved estate brand palette', () {
    expect(AppTheme.light.colorScheme.primary, AppColors.forest);
    expect(AppTheme.light.scaffoldBackgroundColor, AppColors.canvas);
  });
}
