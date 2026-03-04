import { useState, useCallback, useEffect } from 'react';
import { createFileRoute, useSearch, useNavigate } from '@tanstack/react-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Box, Spinner, Text, VStack, useToast } from '@chakra-ui/react';

import TurbineSearch from '../components/Calculator/TurbineSearch';
import StockSelection from '../components/Calculator/StockSelection';
import EarlyCalculationPage from '../components/Calculator/EarlyCalculationPage';
import StockInputPage from '../components/Calculator/StockInputPage';
import ResultsPage from '../components/Calculator/ResultsPage';
import { type HistoryEntry, LOCAL_STORAGE_HISTORY_KEY } from '../components/Common/Sidebar';

import {
    ResultsService,
    CalculationsService,
    TurbinesService,
    ValvesService,
    ApiError,
    type TurbineInfo,
    type ValveInfo_Output as ValveInfo,
    type CalculationResultDB as ClientCalculationResult,
    type MultiCalculationParams, // НОВЫЙ ТИП
    type MultiCalculationResult, // НОВЫЙ ТИП
} from '../client';

type CalculatorStep =
    | 'turbineSearch'
    | 'stockSelection'
    | 'loadingPreviousCalculation'
    | 'earlyCalculation'
    | 'stockInput'
    | 'loadingHistoryResult'
    | 'results';

export const Route = createFileRoute('/calculator')({
    component: CalculatorPage,
    validateSearch: (search: Record<string, unknown>) => ({
        resultId: search.resultId ? String(search.resultId) : undefined,
        stockIdToLoad: search.stockIdToLoad ? String(search.stockIdToLoad) : undefined,
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
    const queryClient = useQueryClient();
    const toast = useToast();
    const searchParams = useSearch({from: Route.fullPath});

    const [currentStep, setCurrentStep] = useState<CalculatorStep>('turbineSearch');
    const [selectedTurbine, setSelectedTurbine] = useState<TurbineInfo | null>(null);
    const [selectedStock, setSelectedStock] = useState<ValveInfo | null>(null);
    const [calculationData, setCalculationData] = useState<ClientCalculationResult | null>(null);

    const isLoadingFromHistory = !!searchParams.resultId;

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
        isError: isErrorTurbineFromHistory,
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

    const {
        data: loadedStockFromHistory,
        isLoading: isLoadingStockFromHistory,
        isError: isErrorStockFromHistory,
    } = useQuery({
        queryKey: ['stockByIdForHistory', searchParams.stockIdToLoad],
        queryFn: async () => {
            if (!searchParams.stockIdToLoad) throw new Error("ID штока не предоставлен");
            const id = parseInt(searchParams.stockIdToLoad, 10);
            return ValvesService.valvesReadValveById({ valveId: id });
        },
        enabled: !!searchParams.stockIdToLoad && !!searchParams.resultId,
        retry: 1,
    });

    const {
        data: latestPreviousResultData,
        isLoading: isLoadingLatestPrevious,
        isError: isErrorLatestPrevious,
        error: errorLatestPrevious,
    } = useQuery({
        queryKey: ['valveResults', selectedStock?.name],
        queryFn: async () => {
            if (!selectedStock?.name) return [];
            const encodedStockName = encodeURIComponent(selectedStock.name);
            const results = await ResultsService.resultsGetCalculationResults({ valveName: encodedStockName });
            return results.map(r => ({
                ...r,
                input_data: typeof r.input_data === 'string' ? JSON.parse(r.input_data) : r.input_data,
                output_data: typeof r.output_data === 'string' ? JSON.parse(r.output_data) : r.output_data,
            }));
        },
        enabled: !!selectedStock?.name && !isLoadingFromHistory,
        select: (data) => (data && data.length > 0 ? data[0] : null),
        retry: (failureCount, error) => (error as ApiError)?.status !== 404 && failureCount < 1,
    });

    useEffect(() => {
        if (!searchParams.resultId) {
            if (currentStep === 'loadingHistoryResult') setCurrentStep('turbineSearch');
            return;
        }

        if (isLoadingResultFromHistory || (searchParams.turbineIdToLoad && isLoadingTurbineFromHistory) || (searchParams.stockIdToLoad && isLoadingStockFromHistory)) {
            if (currentStep !== 'loadingHistoryResult') setCurrentStep('loadingHistoryResult');
            return;
        }

        if (isErrorResultFromHistory || !loadedResultDataFromHistory) {
            toast({ title: "Ошибка загрузки из истории", status: "error" });
            setCurrentStep('turbineSearch');
        } else {
            setCalculationData(loadedResultDataFromHistory);
            setSelectedTurbine(loadedTurbineFromHistory || null);
            setSelectedStock(loadedStockFromHistory || null);
            setCurrentStep('results');
        }

        navigate({ search: (prev: any) => ({ ...prev, resultId: undefined, stockIdToLoad: undefined, turbineIdToLoad: undefined }), replace: true });
    }, [searchParams.resultId, loadedResultDataFromHistory, isLoadingResultFromHistory, isErrorResultFromHistory, navigate, toast]);

    useEffect(() => {
        if (!selectedStock || searchParams.resultId || calculationData || currentStep === 'loadingHistoryResult') return;

        if (isLoadingLatestPrevious) {
            if (currentStep !== 'loadingPreviousCalculation') setCurrentStep('loadingPreviousCalculation');
            return;
        }

        if (currentStep === 'loadingPreviousCalculation' && selectedStock) {
            if (isErrorLatestPrevious || !latestPreviousResultData) {
                setCalculationData(null);
                setCurrentStep('stockInput');
            } else {
                setCalculationData(latestPreviousResultData);
                setCurrentStep('earlyCalculation');
            }
        }
    }, [latestPreviousResultData, isLoadingLatestPrevious, isErrorLatestPrevious, selectedStock, searchParams.resultId, calculationData, currentStep]);

    const handleStockSelect = useCallback((stock: ValveInfo) => {
        navigate({ search: (p: any) => ({ ...p, resultId: undefined, stockIdToLoad: undefined, turbineIdToLoad: undefined }), replace: true });
        setSelectedStock(stock);
        setCalculationData(null);
        queryClient.invalidateQueries({queryKey: ['valveResults', stock.id]});
        setCurrentStep('loadingPreviousCalculation');
    }, [navigate, queryClient]);

    // ИСПОЛЬЗУЕМ НОВЫЕ ТИПЫ ДЛЯ МУТАЦИИ
    const calculationMutation = useMutation<MultiCalculationResult, ApiError, MultiCalculationParams>({
        mutationFn: (params: MultiCalculationParams) => CalculationsService.calculationsCalculate({requestBody: params}),
        onSuccess: (data, variables) => {
            // Для совместимости с ResultsPage "упаковываем" ответ в формат истории
            const mockDbResult: ClientCalculationResult = {
                id: Date.now(), // Fake ID
                user_name: "Current User",
                stock_name: variables.groups.map(g => `${g.type}(${g.quantity}шт)`).join(" + "),
                turbine_name: selectedTurbine?.name || "Unknown",
                calc_timestamp: new Date().toISOString(),
                input_data: variables as any,
                output_data: data as any,
            };

            setCalculationData(mockDbResult);
            setCurrentStep('results');
            toast({title: "Расчет выполнен успешно!", status: "success"});

            if (selectedStock?.id !== undefined && selectedTurbine?.id !== undefined) {
                const newHistoryEntry: HistoryEntry = {
                    id: String(mockDbResult.id),
                    stockName: mockDbResult.stock_name,
                    stockId: selectedStock.id,
                    turbineName: selectedTurbine.name,
                    turbineId: selectedTurbine.id,
                    timestamp: Date.now(),
                };
                const storedHistory = localStorage.getItem(LOCAL_STORAGE_HISTORY_KEY);
                let currentHistory: HistoryEntry[] = [];
                if (storedHistory) {
                    try { currentHistory = JSON.parse(storedHistory); } catch (e) {}
                }
                const updatedHistory = [newHistoryEntry, ...currentHistory].slice(0, 20);
                localStorage.setItem(LOCAL_STORAGE_HISTORY_KEY, JSON.stringify(updatedHistory));
                window.dispatchEvent(new Event('wsaHistoryUpdated'));
            }
        },
        onError: (error: ApiError) => {
            const detail = getApiErrorDetail(error);
            toast({ title: "Ошибка при выполнении расчета", description: detail || error.message, status: "error" });
        },
    });

    const handleTurbineSelect = useCallback((turbine: TurbineInfo) => {
        navigate({ search: (p: any) => ({ ...p, resultId: undefined, stockIdToLoad: undefined, turbineIdToLoad: undefined }), replace: true });
        setSelectedTurbine(turbine);
        setSelectedStock(null);
        setCalculationData(null);
        setCurrentStep('stockSelection');
    }, [navigate]);

    const handleRecalculateDecision = useCallback((recalculate: boolean) => {
        if (!recalculate && calculationData) setCurrentStep('results');
        else setCurrentStep('stockInput');
    }, [calculationData]);

    const handleStockInputSubmit = useCallback((inputData: MultiCalculationParams) => {
        calculationMutation.mutate(inputData);
    }, [calculationMutation]);

    const handleGoBackToTurbineSearch = useCallback(() => {
        setSelectedTurbine(null);
        setSelectedStock(null);
        setCalculationData(null);
        setCurrentStep('turbineSearch');
    }, []);

    const handleGoBackToStockSelection = useCallback(() => {
        setSelectedStock(null);
        setCalculationData(null);
        setCurrentStep('stockSelection');
    }, []);

    const renderContent = () => {
        if (currentStep === 'loadingHistoryResult' || calculationMutation.isPending || (isLoadingResultFromHistory && searchParams.resultId)) {
            return (
                <VStack spacing={4} align="center" justify="center" minH="calc(100vh - 200px)">
                    <Spinner size="xl" color="teal.500"/>
                    <Text>{calculationMutation.isPending ? "Выполняется расчет..." : "Загрузка..."}</Text>
                </VStack>
            );
        }

        switch (currentStep) {
            case 'turbineSearch': return <TurbineSearch onSelectTurbine={handleTurbineSelect}/>;
            case 'stockSelection': return <StockSelection turbine={selectedTurbine} onSelectValve={handleStockSelect} onGoBack={handleGoBackToTurbineSearch} />;
            case 'earlyCalculation': return <EarlyCalculationPage stockId={selectedStock?.name || 'N/A'} lastCalculation={calculationData!} onRecalculate={handleRecalculateDecision} onGoBack={handleGoBackToStockSelection} />;
            case 'stockInput': return <StockInputPage stock={selectedStock!} turbine={selectedTurbine!} onSubmit={handleStockInputSubmit} initialData={calculationData?.input_data} onGoBack={handleGoBackToStockSelection} />;
            case 'results': return <ResultsPage stockId={calculationData!.stock_name} stockInfo={selectedStock} calculationId={calculationData!.id} inputData={calculationData!.input_data as any} outputData={calculationData!.output_data as any} onGoBack={handleGoBackToStockSelection} />;
            default: return null;
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