export type CondenserMethod = 'berman' | 'metro-vickers';

/**
 * Все числовые поля типизируем как string, потому что пользователь может вводить
 * диапазоны вида "10-50-5", а парсинг делает бэкенд.
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

export type CondenserMatrix = {
  columns: Array<number | string>; // G_steam
  rows: Array<number | string>; // t1
  values: Array<Array<number | string | null>>;
};

export type CondenserMatrixResult = {
  meta?: Record<string, unknown>;
  matrix?: CondenserMatrix;

  // поддержка формата, где матрица "расплющена" (как MatrixResult в текущем клиенте)
  columns?: CondenserMatrix['columns'];
  rows?: CondenserMatrix['rows'];
  values?: CondenserMatrix['values'];

  warnings?: string[];
};

