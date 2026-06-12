export const $CalculationInput = {
	description: `Входные данные для расчета матрицы режимов конденсатора.`,
	properties: {
		condenser_id: {
	type: 'number',
	description: `ID конденсатора из БД оборудования (DB-EQUIP-CONDENSER)`,
	isRequired: true,
},
		material_id: {
	type: 'number',
	description: `ID материала трубок из БД материалов (BR-12)`,
	isRequired: true,
},
		method: {
	type: 'Enum',
	enum: ['berman','metro-vickers',],
	isRequired: true,
},
		coefficient_b: {
	type: 'any-of',
	description: `Коэффициент чистоты (от 0 до 1)`,
	contains: [{
	type: 'string',
}, {
	type: 'array',
	contains: {
	type: 'number',
	maximum: 1,
	minimum: 0,
},
}],
},
		G_steam: {
	type: 'any-of',
	description: `Массив расходов пара (Ось X)`,
	contains: [{
	type: 'string',
}, {
	type: 'array',
	contains: {
	type: 'number',
},
}],
	isRequired: true,
},
		W_main: {
	type: 'any-of',
	description: `Массив расходов основной охл. воды`,
	contains: [{
	type: 'string',
}, {
	type: 'array',
	contains: {
	type: 'number',
},
}],
	isRequired: true,
},
		W_builtin: {
	type: 'any-of',
	description: `Массив расходов воды встроенного пучка`,
	contains: [{
	type: 'string',
}, {
	type: 'array',
	contains: {
	type: 'number',
},
}, {
	type: 'null',
}],
},
		t1_main: {
	type: 'any-of',
	description: `Массив температур воды на входе (Ось Y)`,
	contains: [{
	type: 'string',
}, {
	type: 'array',
	contains: {
	type: 'number',
},
}],
	isRequired: true,
},
		t1_builtin: {
	type: 'any-of',
	description: `Температуры встроенного пучка`,
	contains: [{
	type: 'string',
}, {
	type: 'array',
	contains: {
	type: 'number',
},
}, {
	type: 'null',
}],
},
		Z_ejectors: {
	type: 'number',
	description: `Количество рабочих эжекторов`,
	default: 1,
	minimum: 0,
},
		Z_main: {
	type: 'number',
	description: `Число ходов основной воды`,
	default: 2,
	minimum: 1,
},
		Z_builtin: {
	type: 'any-of',
	description: `Число ходов встроенного пучка`,
	contains: [{
	type: 'number',
	minimum: 1,
}, {
	type: 'null',
}],
},
		H_steam: {
	type: 'any-of',
	description: `Энтальпия пара (Обязательно для Бермана)`,
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
},
		X_steam: {
	type: 'number',
	description: `Степень сухости пара (Метро-Виккерс)`,
	default: 0.95,
	maximum: 1,
},
		G_steam_unit: {
	type: 'Enum',
	enum: ['т/ч','кг/с',],
	default: 'т/ч',
},
		W_main_unit: {
	type: 'Enum',
	enum: ['т/ч','кг/с','м3/ч','т/с',],
	default: 'т/ч',
},
		t1_main_unit: {
	type: 'Enum',
	enum: ['°C','K',],
	default: '°C',
},
		H_steam_unit: {
	type: 'Enum',
	enum: ['ккал/кг','кДж/кг',],
	default: 'ккал/кг',
},
	},
} as const;

export const $CalculationOutput = {
	description: `Главная схема ответа (Результаты расчета).`,
	properties: {
		condenser_id: {
	type: 'number',
	isRequired: true,
},
		condenser_name: {
	type: 'string',
	isRequired: true,
},
		method: {
	type: 'Enum',
	enum: ['berman','metro-vickers',],
	isRequired: true,
},
		tables: {
	type: 'array',
	contains: {
		type: 'MatrixResult',
	},
	isRequired: true,
},
		ejector_results: {
	type: 'array',
	contains: {
		type: 'EjectorResult',
	},
},
		total_tables: {
	type: 'number',
	description: `Общее количество сгенерированных матриц`,
	isRequired: true,
},
		calculation_time_ms: {
	type: 'number',
	description: `Время расчета в миллисекундах`,
	isRequired: true,
},
	},
} as const;

export const $CondenserDetail = {
	properties: {
		name_condenser: {
	type: 'string',
	description: `Наименование конденсатора`,
	isRequired: true,
},
		project_name: {
	type: 'any-of',
	description: `Название проекта`,
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		id: {
	type: 'number',
	isRequired: true,
},
		diameter_internal: {
	type: 'number',
	isRequired: true,
},
		wall_thickness: {
	type: 'number',
	isRequired: true,
},
		main_length: {
	type: 'number',
	isRequired: true,
},
		main_count: {
	type: 'number',
	isRequired: true,
},
		builtin_length: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
	isRequired: true,
},
		builtin_count: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
	isRequired: true,
},
		aircooler_count: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
	isRequired: true,
},
		passes_main: {
	type: 'number',
	isRequired: true,
},
		passes_builtin: {
	type: 'any-of',
	contains: [{
	type: 'number',
}, {
	type: 'null',
}],
	isRequired: true,
},
		ejectors_count: {
	type: 'number',
	isRequired: true,
},
		mass_flow_steam_nom: {
	type: 'number',
	isRequired: true,
},
		mass_flow_air: {
	type: 'number',
	isRequired: true,
},
		water_flow_limits: {
	type: 'any-of',
	contains: [{
	type: 'dictionary',
	contains: {
	properties: {
	},
},
}, {
	type: 'null',
}],
	isRequired: true,
},
	},
} as const;

export const $CondenserListItem = {
	properties: {
		name_condenser: {
	type: 'string',
	description: `Наименование конденсатора`,
	isRequired: true,
},
		project_name: {
	type: 'any-of',
	description: `Название проекта`,
	contains: [{
	type: 'string',
}, {
	type: 'null',
}],
},
		id: {
	type: 'number',
	isRequired: true,
},
	},
} as const;

export const $EjectorResult = {
	description: `Результаты расчета эжекторов (Только для метода Бермана).`,
	properties: {
		number_of_ejectors: {
	type: 'number',
	isRequired: true,
},
		P_ejector_kPa: {
	type: 'number',
	isRequired: true,
},
		P_ejector_atm: {
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

export const $MaterialListItem = {
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

export const $MatrixResult = {
	description: `Схема одной таблицы (матрицы) результатов для конкретной комбинации b и W.`,
	properties: {
		meta: {
	type: 'dictionary',
	contains: {
	properties: {
	},
},
	isRequired: true,
},
		columns: {
	type: 'array',
	contains: {
	type: 'number',
},
	isRequired: true,
},
		rows: {
	type: 'array',
	contains: {
	type: 'number',
},
	isRequired: true,
},
		values: {
	type: 'array',
	contains: {
	type: 'array',
	contains: {
	type: 'number',
},
},
	isRequired: true,
},
		warnings: {
	type: 'array',
	contains: {
	type: 'string',
},
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