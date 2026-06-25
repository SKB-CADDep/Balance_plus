import type { CancelablePromise } from './core/CancelablePromise';
import { OpenAPI } from './core/OpenAPI';
import { request as __request } from './core/request';

import type { CalculationInput,CalculationOutput,CondenserDetail,CondenserListItem,MaterialListItem } from './models';

export type HealthData = {
        
    }

export type CalculationsData = {
        CalculateApiV1CalculatePost: {
                    requestBody: CalculationInput
                    
                };
CalculateExcelApiV1CalculateExcelPost: {
                    requestBody: CalculationInput
                    
                };
    }

export type CondensersData = {
        ListCondensersApiV1CondensersGet: {
                    /**
 * Поиск по названию или проекту
 */
search?: string | null
                    
                };
GetCondenserApiV1CondensersCondenserIdGet: {
                    condenserId: number
                    
                };
    }

export type MaterialsData = {
        
    }

export type AsyncCalculationsData = {
        TriggerCalculationApiV1CalculateAsyncPost: {
                    requestBody: Record<string, unknown>
                    
                };
GetTaskStatusApiV1CalculateAsyncTaskIdGet: {
                    taskId: string
                    
                };
    }

export type DefaultData = {
        
    }

export class HealthService {

	/**
	 * Health Check
	 * Быстрая проверка доступности сервиса (для Docker/K8s).
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static healthCheckApiV1HealthGet(): CancelablePromise<unknown> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/health/',
		});
	}

	/**
	 * Health Check Db
	 * Глубокая проверка с подключением к PostgreSQL.
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static healthCheckDbApiV1HealthDbGet(): CancelablePromise<unknown> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/health/db',
		});
	}

}

export class CalculationsService {

	/**
	 * Расчёт конденсатора
	 * Выполняет расчёт по методике Бермана или Метро-Виккерса и возвращает матрицы результатов.
	 * @returns CalculationOutput Успешный расчёт
	 * @throws ApiError
	 */
	public static calculateApiV1CalculatePost(data: CalculationsData['CalculateApiV1CalculatePost']): CancelablePromise<CalculationOutput> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/calculate',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				400: `Ошибка валидации или расчёта`,
				404: `Конденсатор или материал не найден`,
				422: `Ошибка бизнес-валидации`,
			},
		});
	}

	/**
	 * Расчёт конденсатора с выгрузкой в Excel (PoC)
	 * Выполняет расчёт и возвращает результаты в формате XLSX. Матрицы и скаляры разбиты по листам.
	 * @returns unknown Успешный расчёт, возвращается файл
	 * @throws ApiError
	 */
	public static calculateExcelApiV1CalculateExcelPost(data: CalculationsData['CalculateExcelApiV1CalculateExcelPost']): CancelablePromise<unknown> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/calculate/excel',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				400: `Ошибка валидации или расчёта`,
				404: `Конденсатор или материал не найден`,
				422: `Ошибка бизнес-валидации`,
			},
		});
	}

}

export class CondensersService {

	/**
	 * Список конденсаторов
	 * @returns CondenserListItem Successful Response
	 * @throws ApiError
	 */
	public static listCondensersApiV1CondensersGet(data: CondensersData['ListCondensersApiV1CondensersGet'] = {}): CancelablePromise<Array<CondenserListItem>> {
		const {
search,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/condensers',
			query: {
				search
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Получить конденсатор по ID
	 * @returns CondenserDetail Successful Response
	 * @throws ApiError
	 */
	public static getCondenserApiV1CondensersCondenserIdGet(data: CondensersData['GetCondenserApiV1CondensersCondenserIdGet']): CancelablePromise<CondenserDetail> {
		const {
condenserId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/condensers/{condenser_id}',
			path: {
				condenser_id: condenserId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class MaterialsService {

	/**
	 * Список материалов
	 * @returns MaterialListItem Successful Response
	 * @throws ApiError
	 */
	public static listMaterialsApiV1MaterialsGet(): CancelablePromise<Array<MaterialListItem>> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/materials',
		});
	}

}

export class AsyncCalculationsService {

	/**
	 * Trigger Calculation
	 * Отправляет задачу на расчет в очередь (Redis) через Celery.
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static triggerCalculationApiV1CalculateAsyncPost(data: AsyncCalculationsData['TriggerCalculationApiV1CalculateAsyncPost']): CancelablePromise<unknown> {
		const {
requestBody,
} = data;
		return __request(OpenAPI, {
			method: 'POST',
			url: '/api/v1/calculate-async',
			body: requestBody,
			mediaType: 'application/json',
			errors: {
				422: `Validation Error`,
			},
		});
	}

	/**
	 * Get Task Status
	 * Проверяет статус асинхронной задачи по её ID.
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static getTaskStatusApiV1CalculateAsyncTaskIdGet(data: AsyncCalculationsData['GetTaskStatusApiV1CalculateAsyncTaskIdGet']): CancelablePromise<unknown> {
		const {
taskId,
} = data;
		return __request(OpenAPI, {
			method: 'GET',
			url: '/api/v1/calculate-async/{task_id}',
			path: {
				task_id: taskId
			},
			errors: {
				422: `Validation Error`,
			},
		});
	}

}

export class DefaultService {

	/**
	 * Root
	 * @returns unknown Successful Response
	 * @throws ApiError
	 */
	public static rootGet(): CancelablePromise<unknown> {
				return __request(OpenAPI, {
			method: 'GET',
			url: '/',
		});
	}

}