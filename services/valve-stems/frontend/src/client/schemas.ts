export const $CalculationGlobals = {
	description: `Глобальные параметры расчета для всей турбины/группы.`,
	properties: {
		P_fresh: {
	type: 'number',
	isRequired: true,
},
		P_fresh_unit: {
	type: 'string',
	default: 'кгс/см²',
},
		T_fresh: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		T_fresh_unit: {
	type: 'string',
	default: '°C',
},
		H_fresh: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		H_fresh_unit: {
	type: 'string',
	default: 'ккал/кг',
},
		P_air: {
	type: 'number',
	default: 1.033,
},
		P_air_unit: {
	type: 'string',
	default: 'кгс/см²',
},
		T_air: {
	type: 'number',
	default: 27,
},
		T_air_unit: {
	type: 'string',
	default: '°C',
},
		P_lst_leak_off: {
	type: 'number',
	default: 0.97,
},
		P_lst_leak_off_unit: {
	type: 'string',
	default: 'кгс/см²',
},
	},
} as const;

export const $CalculationResultDB = {
	properties: {
		id: {
	type: 'number',
	isRequired: true,
},
		user_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		stock_name: {
	type: 'string',
	isRequired: true,
},
		turbine_name: {
	type: 'string',
	isRequired: true,
},
		calc_timestamp: {
	type: 'string',
	isRequired: true,
	format: 'date-time',
},
		input_data: {
	type: 'dictionary',
	contains: {
	properties: {
	},
},
	isRequired: true,
},
		output_data: {
	type: 'dictionary',
	contains: {
	properties: {
	},
},
	isRequired: true,
},
	},
} as const;

export const $CalculationSummary = {
	description: `Главный объект сводных таблиц.`,
	properties: {
		sk: {
	type: 'TypeSummary',
	isRequired: true,
},
		rk: {
	type: 'TypeSummary',
	isRequired: true,
},
		srk: {
	type: 'TypeSummary',
	isRequired: true,
},
	},
} as const;

export const $GroupCalculationDetails = {
	description: `Детализация результатов для одной конкретной группы.`,
	properties: {
		valve_id: {
	type: 'number',
	isRequired: true,
},
		type: {
	type: 'string',
	isRequired: true,
},
		valve_names: {
	type: 'array',
	contains: {
	type: 'string',
},
	isRequired: true,
},
		quantity: {
	type: 'number',
	isRequired: true,
},
		Gi: {
	type: 'array',
	contains: {
	type: 'number',
},
	isRequired: true,
},
		Pi_in: {
	type: 'array',
	contains: {
	type: 'number',
},
	isRequired: true,
},
		Ti: {
	type: 'array',
	contains: {
	type: 'number',
},
	isRequired: true,
},
		Hi: {
	type: 'array',
	contains: {
	type: 'number',
},
	isRequired: true,
},
		deaerator_props: {
	type: 'array',
	contains: {
	type: 'number',
},
	isRequired: true,
},
		ejector_props: {
	type: 'array',
	contains: {
	type: 'dictionary',
	contains: {
	type: 'number',
},
},
	isRequired: true,
},
		group_total_g: {
	type: 'number',
	isRequired: true,
},
	},
} as const;

export const $HTTPValidationError = {
	properties: {
		detail: {
	type: 'array',
	contains: {
		type: 'ValidationError',
	},
},
	},
} as const;

export const $MultiCalculationParams = {
	description: `Главная схема входящего запроса на мульти-расчет.`,
	properties: {
		turbine_id: {
	type: 'number',
	isRequired: true,
},
		globals: {
	type: 'CalculationGlobals',
	isRequired: true,
},
		groups: {
	type: 'array',
	contains: {
		type: 'ValveGroupInput',
	},
	isRequired: true,
},
	},
} as const;

export const $MultiCalculationResult = {
	description: `Главная схема ответа на мульти-расчет.`,
	properties: {
		details: {
	type: 'array',
	contains: {
		type: 'GroupCalculationDetails',
	},
	isRequired: true,
},
		summary: {
	type: 'CalculationSummary',
	isRequired: true,
},
	},
} as const;

export const $SimpleValveInfo = {
	properties: {
		id: {
	type: 'number',
	isRequired: true,
},
		name: {
	type: 'string',
	isRequired: true,
},
	},
} as const;

export const $TurbineInfo = {
	properties: {
		id: {
	type: 'number',
	isRequired: true,
},
		name: {
	type: 'string',
	isRequired: true,
},
		station_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		station_number: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		factory_number: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $TurbineValves = {
	properties: {
		count: {
	type: 'number',
	isRequired: true,
},
		valves: {
	type: 'array',
	contains: {
		type: 'ValveInfo_Output',
	},
	isRequired: true,
},
	},
} as const;

export const $TurbineWithValvesInfo = {
	properties: {
		id: {
	type: 'number',
	isRequired: true,
},
		name: {
	type: 'string',
	isRequired: true,
},
		station_name: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		station_number: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		factory_number: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		valves: {
	type: 'array',
	contains: {
		type: 'SimpleValveInfo',
	},
	default: [],
},
		matched_valve_id: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $TypeSummary = {
	description: `Сводные агрегированные данные для конкретного типа (Σ СК или Σ РК).`,
	properties: {
		total_g: {
	type: 'number',
	isRequired: true,
},
		mixed_h: {
	type: 'number',
	isRequired: true,
},
	},
} as const;

export const $UnitsDictionaryResponse = {
	properties: {
		parameters: {
	type: 'dictionary',
	contains: {
	type: 'array',
	contains: {
	type: 'string',
},
},
	isRequired: true,
},
	},
} as const;

export const $ValidationError = {
	properties: {
		loc: {
	type: 'array',
	contains: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'number',
}],
},
	isRequired: true,
},
		msg: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'string',
	isRequired: true,
},
		input: {
	properties: {
	},
},
		ctx: {
	type: 'dictionary',
	contains: {
	properties: {
	},
},
},
	},
} as const;

export const $ValveCreate = {
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		diameter: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		clearance: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		count_parts: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part1: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part2: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part3: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part4: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part5: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		round_radius: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		turbine_id: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $ValveGroupInput = {
	description: `Описание одной группы клапанов (с одинаковой геометрией).`,
	properties: {
		valve_id: {
	type: 'number',
	description: `ID клапана, чью геометрию берем за основу`,
	isRequired: true,
},
		type: {
	type: 'string',
	description: `Тип группы: 'СК' или 'РК'`,
	isRequired: true,
},
		valve_names: {
	type: 'array',
	contains: {
	type: 'string',
},
	isRequired: true,
},
		quantity: {
	type: 'number',
	description: `Количество клапанов в группе`,
	isRequired: true,
	minimum: 1,
},
		p_values: {
	type: 'array',
	contains: {
	type: 'number',
},
},
		p_values_unit: {
	type: 'string',
	default: 'кгс/см²',
},
		p_leak_offs: {
	type: 'array',
	contains: {
	type: 'number',
},
},
		p_leak_offs_unit: {
	type: 'string',
	default: 'кгс/см²',
},
	},
} as const;

export const $ValveInfo_Input = {
	description: `Наследуемся от ValveCreate, добавляя ID и вычисляемое поле.`,
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		diameter: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		clearance: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		count_parts: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part1: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part2: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part3: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part4: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part5: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		round_radius: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		turbine_id: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		id: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
	},
} as const;

export const $ValveInfo_Output = {
	description: `Наследуемся от ValveCreate, добавляя ID и вычисляемое поле.`,
	properties: {
		name: {
	type: 'string',
	isRequired: true,
},
		type: {
	type: 'any-of',
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		diameter: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		clearance: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		count_parts: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part1: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part2: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part3: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part4: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		len_part5: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		round_radius: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		turbine_id: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		id: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		section_lengths: {
	type: 'array',
	contains: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
	isReadOnly: true,
	isRequired: true,
},
	},
} as const;