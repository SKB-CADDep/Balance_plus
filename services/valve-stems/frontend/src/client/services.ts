import type { CancelablePromise } from './core/CancelablePromise';
import { OpenAPI } from './core/OpenAPI';
import { request as __request } from './core/request';

import type { TurbineInfo,TurbineValves,TurbineWithValvesInfo,ValveCreate,ValveInfo_Input,ValveInfo_Output,CalculationParams,CalculationResultDB } from './models';

export type TurbinesData = {
        TurbinesGetValvesByTurbineEndpoint: {
                    turbineName: string
                    
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
                    requestBody: CalculationParams
                    
                };
    }

export type ResultsData = {
        ResultsGetCalculationResults: {
                    valveName: string
                    
                };
ResultsReadCalculationResult: {
                    resultId: number
                    
                };
ResultsDeleteCalculationResult: {
                    resultId: number
                    
                };
    }

export type DiagramsData = {
        DiagramsGenerateScheme: {
                    requestBody: ValveInfo_Input
                    
                };
    }

export class TurbinesService {

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
	 * Получить клапаны по имени турбины
	 * Получить список клапанов для заданной турбины.
	 * @returns TurbineValves Successful Response
	 * @throws ApiError
	 */
	public static turbinesGetValvesByTurbineEndpoint(data: TurbinesData['TurbinesGetValvesByTurbineEndpoint']): CancelablePromise<TurbineValves> {
		const {
turbineName,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/turbines/{turbine_name}/valves/',
			path: {
				turbine_name: turbineName
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Создать турбину
	 * Создать новую турбину.
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
	 * Получить информацию о конкретной турбине по её ID.
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
	 * Удалить турбину по ID.
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
	 * Получить список всех клапанов.
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
	 * Создать новый клапан.
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
	 * Обновить данные о клапане.
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
	 * Получить информацию о конкретном клапане (штоке) по его ID.
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
	 * Удалить клапан по ID.
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
	 * Получить турбину по имени клапана.
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
	 * Выполнить расчет
	 * Выполнить расчет на основе параметров.
	 * @returns CalculationResultDB Successful Response
	 * @throws ApiError
	 */
	public static calculationsCalculate(data: CalculationsData['CalculationsCalculate']): CancelablePromise<CalculationResultDB> {
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

}

export class ResultsService {

	/**
	 * Получить результаты расчётов
	 * Получить список результатов расчётов для заданного клапана.
	 * @returns CalculationResultDB Successful Response
	 * @throws ApiError
	 */
	public static resultsGetCalculationResults(data: ResultsData['ResultsGetCalculationResults']): CancelablePromise<Array<CalculationResultDB>> {
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
	 * Получить конкретный результат расчёта по его ID.
	 * @returns CalculationResultDB Successful Response
	 * @throws ApiError
	 */
	public static resultsReadCalculationResult(data: ResultsData['ResultsReadCalculationResult']): CancelablePromise<CalculationResultDB> {
		const {
resultId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/results/{result_id}',
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
	 * Удалить результат расчёта по ID.
	 * @returns void Successful Response
	 * @throws ApiError
	 */
	public static resultsDeleteCalculationResult(data: ResultsData['ResultsDeleteCalculationResult']): CancelablePromise<void> {
		const {
resultId,
} = data;
		return __request(OpenAPI, {
			method: 'DELETE',
			url: '/api/v1/results/{result_id}',
			path: {
				result_id: resultId
			},
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
	public static diagramsGenerateScheme(data: DiagramsData['DiagramsGenerateScheme']): CancelablePromise<any> {
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