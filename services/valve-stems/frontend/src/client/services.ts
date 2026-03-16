import type { CancelablePromise } from './core/CancelablePromise';
import { OpenAPI } from './core/OpenAPI';
import { request as __request } from './core/request';

import type { TurbineInfo,TurbineValves,TurbineWithValvesInfo,ValveCreate,ValveInfo_Input,ValveInfo_Output,CalculationResultDB,MultiCalculationParams,MultiCalculationResult,UnitsDictionaryResponse } from './models';

export type TurbinesData = {
        TurbinesSearchTurbines: {
                    factory?: string | null
q?: string | null
station?: string | null
valve?: string | null
                    
                };
TurbinesGetValvesByTurbine: {
                    turbineId: number
                    
                };
TurbinesCreateTurbine: {
                    requestBody: TurbineInfo
                    
                };
TurbinesReadTurbineById: {
                    turbineId: number
                    
                };
TurbinesDeleteTurbine: {
                    turbineId: number
                    
                };
    }

export type ValvesData = {
        ValvesCreateValve: {
                    requestBody: ValveCreate
                    
                };
ValvesUpdateValve: {
                    requestBody: ValveInfo_Input
valveId: number
                    
                };
ValvesReadValveById: {
                    valveId: number
                    
                };
ValvesDeleteValve: {
                    valveId: number
                    
                };
ValvesGetTurbineByValveName: {
                    valveName: string
                    
                };
    }

export type CalculationsData = {
        CalculationsCalculate: {
                    requestBody: MultiCalculationParams
                    
                };
CalculationsGetCalculationResults: {
                    valveName: string
                    
                };
CalculationsReadCalculationResult: {
                    resultId: number
                    
                };
CalculationsDeleteCalculationResult: {
                    resultId: number
                    
                };
    }

export type UtilsData = {
        
    }

export type DrawioData = {
        DrawioGenerateScheme: {
                    requestBody: ValveInfo_Input
                    
                };
    }

export type DiagramsData = {
        DrawioGenerateScheme: {
                    requestBody: ValveInfo_Input
                    
                };
    }

export class TurbinesService {

	/**
	 * Search Turbines
	 * Поиск проектов по множеству критериев.
	 * @returns TurbineWithValvesInfo Successful Response
	 * @throws ApiError
	 */
	public static turbinesSearchTurbines(data: TurbinesData['TurbinesSearchTurbines'] = {}): CancelablePromise<Array<TurbineWithValvesInfo>> {
		const {
q,
station,
factory,
valve,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/turbines/search',
			query: {
				q, station, factory, valve
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get Valves By Turbine
	 * @returns TurbineValves Successful Response
	 * @throws ApiError
	 */
	public static turbinesGetValvesByTurbine(data: TurbinesData['TurbinesGetValvesByTurbine']): CancelablePromise<TurbineValves> {
		const {
turbineId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/turbines/{turbine_id}/valves/',
			path: {
				turbine_id: turbineId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Получить все турбины с клапанами
	 * Получить список всех турбин вместе с их клапанами.
	 * @returns TurbineWithValvesInfo Successful Response
	 * @throws ApiError
	 */
	public static turbinesGetAllTurbinesWithValves(): CancelablePromise<Array<TurbineWithValvesInfo>> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/turbines/',
		});
	}

	/**
	 * Создать турбину
	 * @returns TurbineInfo Successful Response
	 * @throws ApiError
	 */
	public static turbinesCreateTurbine(data: TurbinesData['TurbinesCreateTurbine']): CancelablePromise<TurbineInfo> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/turbines',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Получить турбину по ID
	 * @returns TurbineInfo Successful Response
	 * @throws ApiError
	 */
	public static turbinesReadTurbineById(data: TurbinesData['TurbinesReadTurbineById']): CancelablePromise<TurbineInfo> {
		const {
turbineId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/turbines/{turbine_id}',
			path: {
				turbine_id: turbineId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Удалить турбину
	 * @returns void Successful Response
	 * @throws ApiError
	 */
	public static turbinesDeleteTurbine(data: TurbinesData['TurbinesDeleteTurbine']): CancelablePromise<void> {
		const {
turbineId,
} = data;
		return __request(OpenAPI, {
			method: 'DELETE',
			url: '/api/v1/turbines/{turbine_id}',
			path: {
				turbine_id: turbineId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class ValvesService {

	/**
	 * Получить все клапаны
	 * @returns ValveInfo_Output Successful Response
	 * @throws ApiError
	 */
	public static valvesGetValves(): CancelablePromise<Array<ValveInfo_Output>> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/valves',
		});
	}

	/**
	 * Создать клапан
	 * @returns ValveInfo_Output Successful Response
	 * @throws ApiError
	 */
	public static valvesCreateValve(data: ValvesData['ValvesCreateValve']): CancelablePromise<ValveInfo_Output> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/valves/',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Обновить клапан
	 * @returns ValveInfo_Output Successful Response
	 * @throws ApiError
	 */
	public static valvesUpdateValve(data: ValvesData['ValvesUpdateValve']): CancelablePromise<ValveInfo_Output> {
		const {
valveId,
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'PUT',
			url: '/api/v1/valves/{valve_id}',
			path: {
				valve_id: valveId
			},
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Получить клапан по ID
	 * @returns ValveInfo_Output Successful Response
	 * @throws ApiError
	 */
	public static valvesReadValveById(data: ValvesData['ValvesReadValveById']): CancelablePromise<ValveInfo_Output> {
		const {
valveId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/valves/{valve_id}',
			path: {
				valve_id: valveId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Удалить клапан
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static valvesDeleteValve(data: ValvesData['ValvesDeleteValve']): CancelablePromise<Record<string, unknown>> {
		const {
valveId,
} = data;
		return __request(OpenAPI, {
			method: 'DELETE',
			url: '/api/v1/valves/{valve_id}',
			path: {
				valve_id: valveId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Получить турбину по имени клапана
	 * @returns TurbineInfo Successful Response
	 * @throws ApiError
	 */
	public static valvesGetTurbineByValveName(data: ValvesData['ValvesGetTurbineByValveName']): CancelablePromise<TurbineInfo> {
		const {
valveName,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/valves/{valve_name}/turbine',
			path: {
				valve_name: valveName
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class CalculationsService {

	/**
	 * Выполнить мульти-расчет
	 * @returns MultiCalculationResult Successful Response
	 * @throws ApiError
	 */
	public static calculationsCalculate(data: CalculationsData['CalculationsCalculate']): CancelablePromise<MultiCalculationResult> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/calculate',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Получить результаты расчётов
	 * @returns CalculationResultDB Successful Response
	 * @throws ApiError
	 */
	public static calculationsGetCalculationResults(data: CalculationsData['CalculationsGetCalculationResults']): CancelablePromise<Array<CalculationResultDB>> {
		const {
valveName,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/valves/{valve_name}/results/',
			path: {
				valve_name: valveName
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Получить результат расчета по ID
	 * @returns CalculationResultDB Successful Response
	 * @throws ApiError
	 */
	public static calculationsReadCalculationResult(data: CalculationsData['CalculationsReadCalculationResult']): CancelablePromise<CalculationResultDB> {
		const {
resultId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/{result_id}',
			path: {
				result_id: resultId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Удалить результат расчёта
	 * @returns void Successful Response
	 * @throws ApiError
	 */
	public static calculationsDeleteCalculationResult(data: CalculationsData['CalculationsDeleteCalculationResult']): CancelablePromise<void> {
		const {
resultId,
} = data;
		return __request(OpenAPI, {
			method: 'DELETE',
			url: '/api/v1/{result_id}',
			path: {
				result_id: resultId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class UtilsService {

	/**
	 * Получить справочник единиц измерения
	 * Возвращает доступные физические параметры и их единицы измерения.
 * Фронтенд использует этот эндпоинт для рендера выпадающих списков (Select).
	 * @returns UnitsDictionaryResponse Successful Response
	 * @throws ApiError
	 */
	public static utilsGetAvailableUnits(): CancelablePromise<UnitsDictionaryResponse> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/utils/units',
		});
	}

}

export class DrawioService {

	/**
	 * Сгенерировать схему Draw.io
	 * Эндпоинт для генерации XML-схемы с обновлёнными параметрами.
 * 
 * Args:
 * valve_info (ValveInfo): Объект с параметрами клапана.
 * 
 * Returns:
 * FileResponse: Сгенерированный XML-файл для скачивания.
 * 
 * Raises:
 * HTTPException: Если произошла ошибка при генерации файла.
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static drawioGenerateScheme(data: DrawioData['DrawioGenerateScheme']): CancelablePromise<any> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/generate_scheme',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class DiagramsService {

	/**
	 * Сгенерировать схему Draw.io
	 * Эндпоинт для генерации XML-схемы с обновлёнными параметрами.
 * 
 * Args:
 * valve_info (ValveInfo): Объект с параметрами клапана.
 * 
 * Returns:
 * FileResponse: Сгенерированный XML-файл для скачивания.
 * 
 * Raises:
 * HTTPException: Если произошла ошибка при генерации файла.
	 * @returns any Successful Response
	 * @throws ApiError
	 */
	public static drawioGenerateScheme(data: DiagramsData['DrawioGenerateScheme']): CancelablePromise<any> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/generate_scheme',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

}