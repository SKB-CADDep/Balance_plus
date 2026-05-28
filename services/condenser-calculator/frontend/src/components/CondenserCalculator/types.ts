export type CondenserMethod = 'berman' | 'metro-vickers';

/**
 * UI-значения: пользователь вводит диапазоны/списки строкой (BR-08),
 * поэтому числовые поля на уровне формы — string.
 */
export interface CondenserFormValues {
  method: CondenserMethod;

  coefficient_b: string;
  G_steam: string;
  W_main: string;
  W_builtin: string;

  t1_main: string;
  t1_builtin: string;

  Z_ejectors: string;
  Z_main: string;
  Z_builtin: string;

  H_steam: string;
  X_steam: string;

  // Units (не числовые, но удобно держать рядом с данными формы)
  G_steam_unit: string;
  W_main_unit: string;
  W_builtin_unit: string;
  t1_main_unit: string;
  t1_builtin_unit: string;
  H_steam_unit: string;
}

