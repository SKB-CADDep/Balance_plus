export type CalculationParams = {
	turbine_name?: string | null;
	valve_drawing?: string | null;
	valve_id?: number | null;
	temperature_start: number;
	t_air: number;
	count_valves: number;
	p_ejector: Array<number>;
	p_values: Array<number>;
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



export type HTTPValidationError = {
	detail?: Array<ValidationError>;
};



export type SimpleValveInfo = {
	id: number;
	name: string;
};



export type TurbineInfo = {
	id: number;
	name: string;
};



export type TurbineValves = {
	count: number;
	valves: Array<ValveInfo_Output>;
};



export type TurbineWithValvesInfo = {
	id: number;
	name: string;
	valves?: Array<SimpleValveInfo>;
};



export type ValidationError = {
	loc: Array<string | number>;
	msg: string;
	type: string;
};



export type ValveCreate = {
	name: string;
	type: string | null;
	diameter: number | null;
	clearance: number | null;
	count_parts: number | null;
	len_part1: number | null;
	len_part2: number | null;
	len_part3: number | null;
	len_part4: number | null;
	len_part5: number | null;
	round_radius: number | null;
	turbine_id: number | null;
};



export type ValveInfo_Input = {
	id?: number | null;
	name?: string | null;
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



export type ValveInfo_Output = {
	id: number;
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
	readonly section_lengths: Array<number | null>;
};

