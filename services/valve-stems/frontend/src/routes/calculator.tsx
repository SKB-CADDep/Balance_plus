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
    CalculationsService,
    TurbinesService,
    ApiError,
    type TurbineInfo,
    type CalculationResultDB as ClientCalculationResult,
    type MultiCalculationParams,
    type MultiCalculationResult,
} from '../client';

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
    if (error instanceof ApiError && error.body) {
        let body = error.body;
        if (typeof body === 'string') {
            try { body = JSON.parse(body); } catch (e) {}
        }
        
        if (typeof body === 'object' && body !== null) {
            const detail = (body as any).detail;
            if (typeof detail === 'string') {
                return detail;
            }
            if (Array.isArray(detail)) {
                return detail.map((err: any) => {
                    const loc = err.loc ? err.loc.join('.') : '';
                    return `${loc}: ${err.msg}`;
                }).join('\n');
            }
            if ((body as any).message && typeof (body as any).message === 'string') {
                return (body as any).message;
            }
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
    const [calculationData, setCalculationData] = useState<ClientCalculationResult | null>(null);

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
            const result = await CalculationsService.calculationsReadCalculationResult({ resultId: id });
            return {
                ...result,
                input_data: typeof result.input_data === 'string' ? JSON.parse(result.input_data) : result.input_data,
                output_data: typeof result.output_data === 'string' ? JSON.parse(result.output_data) : result.output_data,
            } as ClientCalculationResult;
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
                title: "Ошибка загрузки из истории", 
                description: getApiErrorDetail(errorResultFromHistory) || "Не удалось загрузить расчет",
                status: "error" 
            });
            setCurrentStep('turbineSearch');
        } else {
            setCalculationData(loadedResultDataFromHistory);
            setSelectedTurbine(loadedTurbineFromHistory || null);
            setCurrentStep('results');
            toast({ title: `Расчет "${loadedResultDataFromHistory.stock_name}" загружен`, status: "success" });
        }

        // Очищаем URL параметры после обработки
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
    const calculationMutation = useMutation<MultiCalculationResult, ApiError, MultiCalculationParams>({
        mutationFn: (params: MultiCalculationParams) => CalculationsService.calculationsCalculate({ requestBody: params }),
        onSuccess: (data, variables) => {
            // Формируем красивое имя для отображения (как в БД)
            const stockName = variables.groups.map(g => `${g.type}(${g.quantity}шт)`).join(" + ");
            
            // Оборачиваем ответ бэкенда в формат БД для компонента ResultsPage
            const mockDbResult: ClientCalculationResult = {
                id: Date.now(), // Fallback ID для UI
                user_name: "Engineer",
                stock_name: stockName,
                turbine_name: selectedTurbine?.name || "Unknown",
                calc_timestamp: new Date().toISOString(),
                input_data: variables as any,
                output_data: data as any,
            };

            setCalculationData(mockDbResult);
            setCurrentStep('results');
            toast({ title: "Расчет выполнен успешно!", status: "success" });

            // Сохранение в историю (Sidebar)
            if (selectedTurbine?.id !== undefined) {
                const newHistoryEntry: HistoryEntry = {
                    id: String(mockDbResult.id),
                    stockName: stockName,
                    stockId: selectedStocks[0]?.valve?.id || 0, // Сохраняем ID первого клапана группы
                    turbineName: selectedTurbine.name,
                    turbineId: selectedTurbine.id ?? 0,
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
        onError: (error: ApiError) => {
            const detail = getApiErrorDetail(error);
            toast({ 
                title: "Ошибка при выполнении расчета", 
                description: detail || error.message || "Неизвестная ошибка", 
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

    const handleStockInputSubmit = useCallback((payload: MultiCalculationParams) => {
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
                    turbine={selectedTurbine as any}
                    onSelectValves={handleValvesSelect as any}
                    onGoBack={() => setCurrentStep('turbineSearch')}
                />;
            case 'stockInput':
                return <StockInputPage
                    selectedStocks={selectedStocks}
                    turbine={selectedTurbine!}
                    onSubmit={handleStockInputSubmit as any}
                    onGoBack={() => setCurrentStep('stockSelection')}
                />;
            case 'results':
                if (calculationData) {
                    return <ResultsPage
                        stockId={calculationData.stock_name}
                        inputData={calculationData.input_data as any}
                        outputData={calculationData.output_data as any}
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

export default CalculatorPage;