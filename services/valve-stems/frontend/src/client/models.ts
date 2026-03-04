/**
 * Глобальные параметры расчета для всей турбины/группы.
 */
export type CalculationGlobals = {
	P_fresh: number;
	P_fresh_unit?: string;
	T_fresh?: number | null;
	T_fresh_unit?: string;
	H_fresh?: number | null;
	H_fresh_unit?: string;
	P_air?: number;
	P_air_unit?: string;
	T_air?: number;
	T_air_unit?: string;
	P_lst_leak_off?: number;
	P_lst_leak_off_unit?: string;
};



export type CalculationResultDB = {
	id: number;
	user_name?: string | null;
	stock_name: string;
	turbine_name: string;
	calc_timestamp: string;
	input_data: Record<string, unknown>;
	output_data: Record<string, unknown>;
};



/**
 * Главный объект сводных таблиц.
 */
export type CalculationSummary = {
	sk: TypeSummary;
	rk: TypeSummary;
	srk: TypeSummary;
};



/**
 * Детализация результатов для одной конкретной группы.
 */
export type GroupCalculationDetails = {
	valve_id: number;
	type: string;
	valve_names: Array<string>;
	quantity: number;
	Gi: Array<number>;
	Pi_in: Array<number>;
	Ti: Array<number>;
	Hi: Array<number>;
	deaerator_props: Array<number>;
	ejector_props: Array<Record<string, number>>;
	group_total_g: number;
};



export type HTTPValidationError = {
	detail?: Array<ValidationError>;
};



/**
 * Главная схема входящего запроса на мульти-расчет.
 */
export type MultiCalculationParams = {
	turbine_id: number;
	globals: CalculationGlobals;
	groups: Array<ValveGroupInput>;
};



/**
 * Главная схема ответа на мульти-расчет.
 */
export type MultiCalculationResult = {
	details: Array<GroupCalculationDetails>;
	summary: CalculationSummary;
};



export type SimpleValveInfo = {
	id: number;
	name: string;
};



export type TurbineInfo = {
	id: number;
	name: string;
	station_name?: string | null;
	station_number?: string | null;
	factory_number?: string | null;
};



export type TurbineValves = {
	count: number;
	valves: Array<ValveInfo_Output>;
};



export type TurbineWithValvesInfo = {
	id: number;
	name: string;
	station_name?: string | null;
	station_number?: string | null;
	factory_number?: string | null;
	valves?: Array<SimpleValveInfo>;
	matched_valve_id?: number | null;
};



/**
 * Сводные агрегированные данные для конкретного типа (Σ СК или Σ РК).
 */
export type TypeSummary = {
	total_g: number;
	mixed_h: number;
};



export type UnitsDictionaryResponse = {
	parameters: Record<string, Array<string>>;
};



export type ValidationError = {
	loc: Array<string | number>;
	msg: string;
	type: string;
	input?: unknown;
	ctx?: Record<string, unknown>;
};



export type ValveCreate = {
	name: string;
	type?: string | null;
	diameter?: number | null;
	clearance?: number | null;
	count_parts?: number | null;
	len_part1?: number | null;
	len_part2?: number | null;
	len_part3?: number | null;
	len_part4?: number | null;
	len_part5?: number | null;
	round_radius?: number | null;
	turbine_id?: number | null;
};



/**
 * Описание одной группы клапанов (с одинаковой геометрией).
 */
export type ValveGroupInput = {
	/**
	 * ID клапана, чью геометрию берем за основу
	 */
	valve_id: number;
	/**
	 * Тип группы: 'СК' или 'РК'
	 */
	type: string;
	/**
	 * Список имен клапанов
	 */
	valve_names: Array<string>;
	/**
	 * Количество клапанов в группе
	 */
	quantity: number;
	/**
	 * Давления перед участками
	 */
	p_values?: Array<number>;
	p_values_unit?: string;
	/**
	 * Промежуточные отсосы
	 */
	p_leak_offs?: Array<number>;
	p_leak_offs_unit?: string;
};



/**
 * Наследуемся от ValveCreate, добавляя ID и вычисляемое поле.
 */
export type ValveInfo_Input = {
	name: string;
	type?: string | null;
	diameter?: number | null;
	clearance?: number | null;
	count_parts?: number | null;
	len_part1?: number | null;
	len_part2?: number | null;
	len_part3?: number | null;
	len_part4?: number | null;
	len_part5?: number | null;
	round_radius?: number | null;
	turbine_id?: number | null;
	id?: number | null;
};



/**
 * Наследуемся от ValveCreate, добавляя ID и вычисляемое поле.
 */
export type ValveInfo_Output = {
	name: string;
	type?: string | null;
	diameter?: number | null;
	clearance?: number | null;
	count_parts?: number | null;
	len_part1?: number | null;
	len_part2?: number | null;
	len_part3?: number | null;
	len_part4?: number | null;
	len_part5?: number | null;
	round_radius?: number | null;
	turbine_id?: number | null;
	id?: number | null;
	readonly section_lengths: Array<number | null>;
};

