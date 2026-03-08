import { useState, useCallback, useEffect } from 'react';
import { createFileRoute, useSearch, useNavigate } from '@tanstack/react-router';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Box, Spinner, Text, VStack, useToast } from '@chakra-ui/react';

import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection, { type SelectedStock } from '../components/Calculator/StockSelection';
import StockInputPage from '../components/Calculator/StockInputPage';
import ResultsPage from '../components/Calculator/ResultsPage';
import { type HistoryEntry, LOCAL_STORAGE_HISTORY_KEY } from '../components/Common/Sidebar';

import {
    ResultsService,
    TurbinesService,
    ApiError,
    type TurbineInfo,
} from '../client';

// Используем прямой запрос, так как OpenAPI клиент еще не обновлен под новые схемы
import { request as __request } from '../client/core/request';
import { OpenAPI } from '../client/core/OpenAPI';

type CalculatorStep =
    | 'turbineSearch'
    | 'stockSelection'
    | 'stockInput'
    | 'loadingHistoryResult'
    | 'results';

export const Route = createFileRoute('/calculator')({
    component: CalculatorPage,
    validateSearch: (search: Record<string, unknown>) => ({
        resultId: search.resultId ? String(search.resultId) : undefined,
        turbineIdToLoad: search.turbineIdToLoad ? String(search.turbineIdToLoad) : undefined,
    }),
});

export function getApiErrorDetail(error: any): string | undefined {
    if (error instanceof ApiError && error.body && typeof error.body === 'object') {
        if ('detail' in error.body && typeof (error.body as any).detail === 'string') {
            return (error.body as any).detail;
        }
    }
    return undefined;
}

function CalculatorPage() {
    const navigate = useNavigate();
    const toast = useToast();
    const searchParams = useSearch({ from: Route.fullPath });

    const [currentStep, setCurrentStep] = useState<CalculatorStep>('turbineSearch');
    const [selectedTurbine, setSelectedTurbine] = useState<TurbineInfo | null>(null);
    const [selectedStocks, setSelectedStocks] = useState<SelectedStock[]>([]);
    const [calculationData, setCalculationData] = useState<any>(null);

    // ==========================================
    // ЛОГИКА ЗАГРУЗКИ ИЗ ИСТОРИИ (SIDEBAR)
    // ==========================================
    const {
        data: loadedResultDataFromHistory,
        isLoading: isLoadingResultFromHistory,
        isError: isErrorResultFromHistory,
        error: errorResultFromHistory,
    } = useQuery({
        queryKey: ['calculationResultById', searchParams.resultId],
        queryFn: async () => {
            if (!searchParams.resultId) throw new Error("ID результата не предоставлен");
            const id = parseInt(searchParams.resultId, 10);
            if (isNaN(id)) throw new Error("Неверный ID результата");
            const result = await ResultsService.resultsReadCalculationResult({ resultId: id });
            return {
                ...result,
                input_data: typeof result.input_data === 'string' ? JSON.parse(result.input_data) : result.input_data,
                output_data: typeof result.output_data === 'string' ? JSON.parse(result.output_data) : result.output_data,
            };
        },
        enabled: !!searchParams.resultId,
        retry: 1,
    });

    const {
        data: loadedTurbineFromHistory,
        isLoading: isLoadingTurbineFromHistory,
    } = useQuery({
        queryKey: ['turbineByIdForHistory', searchParams.turbineIdToLoad],
        queryFn: async () => {
            if (!searchParams.turbineIdToLoad) throw new Error("ID турбины не предоставлен");
            const id = parseInt(searchParams.turbineIdToLoad, 10);
            return TurbinesService.turbinesReadTurbineById({ turbineId: id });
        },
        enabled: !!searchParams.turbineIdToLoad && !!searchParams.resultId,
        retry: 1,
    });

    useEffect(() => {
        if (!searchParams.resultId) {
            if (currentStep === 'loadingHistoryResult') setCurrentStep('turbineSearch');
            return;
        }

        if (isLoadingResultFromHistory || (searchParams.turbineIdToLoad && isLoadingTurbineFromHistory)) {
            if (currentStep !== 'loadingHistoryResult') setCurrentStep('loadingHistoryResult');
            return;
        }

        if (isErrorResultFromHistory || !loadedResultDataFromHistory) {
            toast({
                title: "Ошибка загрузки данных расчета из истории",
                description: getApiErrorDetail(errorResultFromHistory) || (errorResultFromHistory as Error)?.message,
                status: "error"
            });
            setCurrentStep('turbineSearch');
        } else {
            setCalculationData(loadedResultDataFromHistory);
            setSelectedTurbine(loadedTurbineFromHistory || null);
            setCurrentStep('results');
            toast({ title: `Расчет "${loadedResultDataFromHistory.stock_name}" загружен`, status: "success" });
        }

        // Очищаем URL
        navigate({
            search: (prev: any) => ({ ...prev, resultId: undefined, turbineIdToLoad: undefined }),
            replace: true
        });
    }, [
        searchParams.resultId, searchParams.turbineIdToLoad,
        loadedResultDataFromHistory, isLoadingResultFromHistory, isErrorResultFromHistory,
        loadedTurbineFromHistory, isLoadingTurbineFromHistory,
        navigate, toast, currentStep, errorResultFromHistory
    ]);

    // ==========================================
    // ЛОГИКА НОВОГО МУЛЬТИ-РАСЧЕТА
    // ==========================================
    const calculationMutation = useMutation<any, any, any>({
        mutationFn: async (payload: any) => {
            return await __request(OpenAPI, {
                method: 'POST',
                url: '/api/v1/calculate',
                body: payload,
            });
        },
        onSuccess: (data, variables) => {
            // Бэкенд теперь сам возвращает схему CalculationResultDB, 
            // но на всякий случай парсим JSON, если он пришел строкой
            const stockName = data.stock_name || "Групповой расчёт штоков";
            const parsedData = {
                id: data.id, // Бэкенд должен вернуть ID сохраненного расчета
                stock_name: stockName,
                turbine_name: selectedTurbine?.name || "",
                input_data: variables,
                output_data: data.output_data || data, // Зависит от того, как бэк отдает ответ
            };
            
            setCalculationData(parsedData);
            setCurrentStep('results');
            toast({ title: "Расчет выполнен успешно!", status: "success" });

            // Сохранение в историю Sidebar
            if (selectedTurbine?.id !== undefined && data.id !== undefined) {
                const newHistoryEntry: HistoryEntry = {
                    id: String(data.id),
                    stockName: stockName,
                    stockId: selectedStocks[0]?.valve?.id || 0, // Берем ID первого клапана для совместимости
                    turbineName: selectedTurbine.name,
                    turbineId: selectedTurbine.id,
                    timestamp: Date.now(),
                };
                
                const storedHistory = localStorage.getItem(LOCAL_STORAGE_HISTORY_KEY);
                let currentHistory: HistoryEntry[] = [];
                if (storedHistory) {
                    try { currentHistory = JSON.parse(storedHistory); } catch (e) { console.error(e); }
                }
                const updatedHistory = [newHistoryEntry, ...currentHistory].slice(0, 20);
                localStorage.setItem(LOCAL_STORAGE_HISTORY_KEY, JSON.stringify(updatedHistory));
                window.dispatchEvent(new Event('wsaHistoryUpdated')); // Триггер для Sidebar
            }
        },
        onError: (error: any) => {
            toast({
                title: "Ошибка при выполнении расчета",
                description: error?.body?.detail || error.message || "Неизвестная ошибка",
                status: "error"
            });
        },
    });

    // ==========================================
    // ОБРАБОТЧИКИ НАВИГАЦИИ МЕЖДУ ШАГАМИ
    // ==========================================
    const handleTurbineSelect = useCallback((turbine: TurbineInfo) => {
        setSelectedTurbine(turbine);
        setSelectedStocks([]);
        setCalculationData(null);
        setCurrentStep('stockSelection');
    }, []);

    const handleValvesSelect = useCallback((selections: SelectedStock[]) => {
        setSelectedStocks(selections);
        setCalculationData(null);
        setCurrentStep('stockInput');
    }, []);

    const handleStockInputSubmit = useCallback((payload: any) => {
        if (!selectedTurbine?.id || selectedStocks.length === 0) {
            toast({ title: "Ошибка", description: "Турбина или клапаны не выбраны.", status: "error" });
            setCurrentStep('turbineSearch');
            return;
        }
        calculationMutation.mutate(payload);
    }, [calculationMutation, selectedTurbine, selectedStocks, toast]);

    const renderContent = () => {
        if (currentStep === 'loadingHistoryResult' || calculationMutation.isPending || (isLoadingResultFromHistory && searchParams.resultId)) {
            const loadingText = calculationMutation.isPending ? "Выполняется расчет..." : "Загрузка из истории...";
            return (
                <VStack spacing={4} align="center" justify="center" minH="calc(100vh - 200px)">
                    <Spinner size="xl" color="teal.500" />
                    <Text>{loadingText}</Text>
                </VStack>
            );
        }

        switch (currentStep) {
            case 'turbineSearch':
                return <TurbineSearch onSelectTurbine={handleTurbineSelect} />;
            case 'stockSelection':
                return <StockSelection
                    turbine={selectedTurbine}
                    onSelectValves={handleValvesSelect}
                    onGoBack={() => setCurrentStep('turbineSearch')}
                />;
            case 'stockInput':
                return <StockInputPage
                    selectedStocks={selectedStocks}
                    turbine={selectedTurbine!}
                    onSubmit={handleStockInputSubmit}
                    onGoBack={() => setCurrentStep('stockSelection')}
                />;
            case 'results':
                if (calculationData) {
                    return <ResultsPage
                        stockId={calculationData.stock_name}
                        inputData={calculationData.input_data}
                        outputData={calculationData.output_data}
                        onGoBack={() => {
                            setCalculationData(null);
                            if (selectedStocks.length > 0) setCurrentStep('stockInput');
                            else if (selectedTurbine) setCurrentStep('stockSelection');
                            else setCurrentStep('turbineSearch');
                        }}
                    />;
                }
                setCurrentStep('turbineSearch');
                return null;
            default:
                if (currentStep !== 'turbineSearch') setCurrentStep('turbineSearch');
                return null;
        }
    };

    return (
        <Box w="100%">
            <Box display="flex" justifyContent="center" alignItems="flex-start" minH="calc(100vh - 150px)">
                {renderContent()}
            </Box>
        </Box>
    );
}