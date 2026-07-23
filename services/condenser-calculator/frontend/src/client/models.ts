/**
 * Входные данные для расчета матрицы режимов конденсатора.
 */
export type CalculationInput = {
	/**
	 * ID конденсатора из БД оборудования (DB-EQUIP-CONDENSER)
	 */
	condenser_id: number;
	/**
	 * ID материала трубок из БД материалов (BR-12)
	 */
	material_id: number;
	/**
	 * Методика расчета (BR-01)
	 */
	method: 'berman' | 'metro-vickers';
	/**
	 * Коэффициент чистоты (от 0 до 1)
	 */
	coefficient_b?: string | Array<number>;
	/**
	 * Массив расходов пара (Ось X)
	 */
	G_steam: string | Array<number>;
	/**
	 * Массив расходов основной охл. воды
	 */
	W_main: string | Array<number>;
	/**
	 * Массив расходов воды встроенного пучка
	 */
	W_builtin?: string | Array<number> | null;
	/**
	 * Массив температур воды на входе (Ось Y)
	 */
	t1_main: string | Array<number>;
	/**
	 * Температуры встроенного пучка
	 */
	t1_builtin?: string | Array<number> | null;
	/**
	 * Количество рабочих эжекторов
	 */
	Z_ejectors?: number;
	/**
	 * Число ходов основной воды
	 */
	Z_main?: number;
	/**
	 * Число ходов встроенного пучка
	 */
	Z_builtin?: number | null;
	/**
	 * Энтальпия пара (Обязательно для Бермана)
	 */
	H_steam?: number | null;
	/**
	 * Степень сухости пара (Метро-Виккерс)
	 */
	X_steam?: number;
	G_steam_unit?: 'т/ч' | 'кг/с';
	W_main_unit?: 'т/ч' | 'кг/с' | 'м3/ч' | 'т/с';
	t1_main_unit?: '°C' | 'K';
	H_steam_unit?: 'ккал/кг' | 'кДж/кг';
};








/**
 * Главная схема ответа (Результаты расчета).
 */
export type CalculationOutput = {
	condenser_id: number;
	condenser_name: string;
	method: 'berman' | 'metro-vickers';
	/**
	 * Сгенерированные матрицы P_steam
	 */
	tables: Array<MatrixResult>;
	/**
	 * Данные эжекторов
	 */
	ejector_results?: Array<EjectorResult>;
	/**
	 * Общее количество сгенерированных матриц
	 */
	total_tables: number;
	/**
	 * Время расчета в миллисекундах
	 */
	calculation_time_ms: number;
};




export type CondenserDetail = {
	/**
	 * Наименование конденсатора
	 */
	name_condenser: string;
	/**
	 * Название проекта
	 */
	project_name?: string | null;
	id: number;
	diameter_internal: number;
	wall_thickness: number;
	main_length: number;
	main_count: number;
	builtin_length: number | null;
	builtin_count: number | null;
	aircooler_count: number | null;
	passes_main: number;
	passes_builtin: number | null;
	ejectors_count: number;
	mass_flow_steam_nom: number;
	mass_flow_air: number;
	water_flow_limits: Record<string, unknown> | null;
	materials?: Array<MaterialListItem>;
};



export type CondenserListItem = {
	/**
	 * Наименование конденсатора
	 */
	name_condenser: string;
	/**
	 * Название проекта
	 */
	project_name?: string | null;
	id: number;
};



/**
 * Результаты расчета эжекторов (Только для метода Бермана).
 */
export type EjectorResult = {
	number_of_ejectors: number;
	P_ejector_kPa: number;
	P_ejector_atm: number;
};



export type HTTPValidationError = {
	detail?: Array<ValidationError>;
};



export type MaterialListItem = {
	id: number;
	name: string;
};



/**
 * Схема одной таблицы (матрицы) результатов для конкретной комбинации b и W.
 */
export type MatrixResult = {
	/**
	 * Метаданные (какие W и b использовались для этой матрицы)
	 */
	meta: Record<string, unknown>;
	/**
	 * Заголовки столбцов (G_steam)
	 */
	columns: Array<number>;
	/**
	 * Заголовки строк (t1_main)
	 */
	rows: Array<number>;
	/**
	 * Матрица значений давления (P_steam)
	 */
	values: Array<Array<number>>;
	/**
	 * Предупреждения (выход за диапазоны, экстраполяция)
	 */
	warnings?: Array<string>;
};



export type ValidationError = {
	loc: Array<string | number>;
	msg: string;
	type: string;
	input?: unknown;
	ctx?: Record<string, unknown>;
};

