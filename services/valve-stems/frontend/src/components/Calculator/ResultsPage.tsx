import React, { useState, useEffect } from 'react';
import * as XLSX from 'xlsx';
import {
    Box, Button, Heading, Text, VStack, Table, Thead, Tbody, Tr, Th, Td,
    TableContainer, SimpleGrid, Divider, HStack, useToast, Icon, useColorModeValue, Badge,
} from '@chakra-ui/react';
import { FiChevronLeft, FiDownload, FiSave, FiFileText } from 'react-icons/fi';
import { OpenAPI, type CalculationParams, type ValveInfo_Output as ValveInfo } from '../../client';

export interface ExpectedOutputData {
    Gi?: number[];
    Pi_in?: number[];
    Ti?: number[];
    Hi?: number[];
    deaerator_props?: number[]; // [g, t, h, p]
    ejector_props?: Array<{ g: number; t: number; h: number; p: number }>;
}

type Props = {
    stockId: string;
    stockInfo?: ValveInfo | null;
    calculationId?: number;
    inputData?: Partial<CalculationParams>;
    outputData?: Partial<ExpectedOutputData>;
    onGoBack?: () => void;
    isEmbedded?: boolean; 
    taskId?: string;
};

const roundNumber = (num: any, decimals: number = 4): string | number => {
    const parsedNum = parseFloat(num);
    if (isNaN(parsedNum)) {
        return '-';
    }
    // Если число очень маленькое, но не ноль, показываем в экспоненциальной форме или больше знаков
    if (parsedNum !== 0 && Math.abs(parsedNum) < 0.0001) {
        return parsedNum.toExponential(2);
    }
    return Number(parsedNum.toFixed(decimals));
};

const ResultsPage: React.FC<Props> = ({
    stockId,
    stockInfo,
    inputData = {},
    outputData = {},
    onGoBack
}) => {
    const [isDownloadingDrawio, setIsDownloadingDrawio] = useState(false);
    const toast = useToast();
    const buttonHoverBg = useColorModeValue("gray.100", "gray.700");
    const tableHeaderBg = useColorModeValue("gray.50", "gray.700");

    // --- INTEGRATION LOGIC START ---
    const [isEmbedded, setIsEmbedded] = useState(false);

    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        setIsEmbedded(urlParams.get('embedded') === 'true');
    }, []);

    const handleSaveToIde = () => {
        const message = {
            type: 'WSA_CALCULATION_COMPLETE',
            payload: {
                input: inputData,
                output: outputData,
                stockId: stockId
            }
        };
        window.parent.postMessage(message, '*');

        toast({
            title: "Отправлено в Balance+",
            description: "Результаты переданы в IDE для сохранения в Git.",
            status: "info",
            duration: 3000
        });
    };
    // --- INTEGRATION LOGIC END ---

    const currentInputData: Partial<CalculationParams> = inputData || {};
    const currentOutputData: Partial<ExpectedOutputData> = outputData || {};

    const inputDataEntries = [
        { label: 'Название турбины', value: currentInputData.turbine_name },
        { label: 'Чертёж клапана', value: currentInputData.valve_drawing },
        { label: 'ID клапана', value: currentInputData.valve_id },
        { label: 'Начальная температура (°C)', value: currentInputData.temperature_start },
        { label: 'Температура воздуха (°C)', value: currentInputData.t_air },
        { label: 'Количество клапанов', value: currentInputData.count_valves },
        {
            label: 'Входные давления (P1...P_air, кгс/см²)',
            value: Array.isArray(currentInputData.p_values) ? currentInputData.p_values.map(p => roundNumber(p, 3)).join(' → ') : 'N/A'
        },
    ];

    // Основные данные по участкам
    const gi = Array.isArray(currentOutputData.Gi) ? currentOutputData.Gi : [];
    const pi_in = Array.isArray(currentOutputData.Pi_in) ? currentOutputData.Pi_in : [];
    const ti = Array.isArray(currentOutputData.Ti) ? currentOutputData.Ti : [];
    const hi = Array.isArray(currentOutputData.Hi) ? currentOutputData.Hi : [];

    // Данные по отсосам
    // Deaerator backend order: [g, t, h, p]
    const deaeratorProps = Array.isArray(currentOutputData.deaerator_props) ? currentOutputData.deaerator_props : [];
    const ejectorProps = Array.isArray(currentOutputData.ejector_props) ? currentOutputData.ejector_props : [];

    const handleDownloadDrawio = async () => {
        if (!stockInfo) {
            toast({ title: "Ошибка", description: "Нет данных для генерации схемы.", status: "error" });
            return;
        }
        setIsDownloadingDrawio(true);
        try {
            const url = `${OpenAPI.BASE}/api/v1/generate_scheme`;
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(stockInfo),
            });
            if (!response.ok) throw new Error("Ошибка сервера");
            
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', `схема_${stockInfo.name || stockId}.drawio`);
            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);
        } catch (error: any) {
            toast({ title: "Ошибка", description: error.message, status: "error" });
        } finally {
            setIsDownloadingDrawio(false);
        }
    };

    const handleDownloadExcel = () => {
        try {
            const wb = XLSX.utils.book_new();

            // Лист 1: Входные
            const inputSheetData = [{
                'Турбина': currentInputData.turbine_name,
                'Клапан': currentInputData.valve_drawing,
                'P свежего пара': currentInputData.p_values?.[0],
                'T свежего пара': currentInputData.temperature_start,
                'P воздуха': currentInputData.p_values?.[(currentInputData.p_values?.length || 1) - 1],
                'T воздуха': currentInputData.t_air,
                'Кол-во клапанов': currentInputData.count_valves,
            }];
            XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(inputSheetData), 'Входные данные');

            // Лист 2: По участкам
            if (gi.length > 0) {
                const mainOutputData = gi.map((_g, index) => ({
                    'Участок': index + 1,
                    'Расход (G), т/ч': roundNumber(gi[index]),
                    'Давление вх. (P), кгс/см²': roundNumber(pi_in[index]),
                    'Температура (T), °C': roundNumber(ti[index]),
                    'Энтальпия (H), кДж/кг': roundNumber(hi[index]),
                }));
                XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(mainOutputData), 'По участкам');
            }

            // Лист 3: Отсосы
            const suctionData = [];
            
            // Деаэратор: [g, t, h, p]
            if (deaeratorProps.length === 4 && deaeratorProps[0] > 0) {
                suctionData.push({
                    'Потребитель': 'Деаэратор (Камера 2)',
                    'Расход (G), т/ч': roundNumber(deaeratorProps[0]),
                    'Давление (P), кгс/см²': roundNumber(deaeratorProps[3]),
                    'Температура (T), °C': roundNumber(deaeratorProps[1]),
                    'Энтальпия (H), кДж/кг': roundNumber(deaeratorProps[2]),
                });
            }

            // Эжекторы: {g, t, h, p}
            ejectorProps.forEach((ej, idx) => {
                suctionData.push({
                    'Потребитель': `Эжектор / Отсос ${idx + 1}`,
                    'Расход (G), т/ч': roundNumber(ej.g),
                    'Давление (P), кгс/см²': roundNumber(ej.p),
                    'Температура (T), °C': roundNumber(ej.t),
                    'Энтальпия (H), кДж/кг': roundNumber(ej.h),
                });
            });

            if (suctionData.length > 0) {
                XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(suctionData), 'Отсосы');
            }

            XLSX.writeFile(wb, `Расчет_${stockId}.xlsx`);
            toast({ title: "Excel файл создан", status: "success" });
        } catch (e: any) {
            console.error(e);
            toast({ title: "Ошибка экспорта", status: "error" });
        }
    };

    return (
        <VStack spacing={8} p={5} align="stretch" w="100%" maxW="container.xl" mx="auto">
            {/* Заголовок и навигация */}
            <VStack spacing={2} w="full">
                <Heading as="h2" size="xl" textAlign="center">
                    Результаты: <Text as="span" color="teal.500">{stockId}</Text>
                </Heading>
                <Text color="gray.500" fontSize="sm">ID расчета: {inputData?.valve_id} | Турбина: {inputData?.turbine_name}</Text>

                {isEmbedded ? (
                    <Button onClick={() => window.parent.postMessage({ type: 'WSA_CLOSE' }, '*')} variant="ghost" size="sm" leftIcon={<Icon as={FiChevronLeft} />}>
                        Вернуться в Balance+
                    </Button>
                ) : onGoBack && (
                    <Button onClick={onGoBack} variant="outline" colorScheme="teal" size="sm" leftIcon={<Icon as={FiChevronLeft} />} mt={2} _hover={{ bg: buttonHoverBg }}>
                        Вернуться к вводу данных
                    </Button>
                )}
            </VStack>

            {/* Блок входных данных */}
            <Box borderWidth="1px" borderRadius="lg" p={5} boxShadow="sm" bg={useColorModeValue("white", "gray.800")}>
                <Heading as="h3" size="md" mb={4} color="teal.600">Входные параметры</Heading>
                <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                    {inputDataEntries.map((entry, i) => (
                        <Box key={i}>
                            <Text fontSize="xs" color="gray.500" textTransform="uppercase" fontWeight="bold">
                                {entry.label}
                            </Text>
                            <Text fontSize="md" fontWeight="medium">{entry.value}</Text>
                        </Box>
                    ))}
                </SimpleGrid>
            </Box>

            <Divider />

            {/* Таблица 1: По участкам */}
            <Box>
                <Heading as="h3" size="lg" mb={4} textAlign="center">Распределение по участкам уплотнения</Heading>
                {gi.length > 0 ? (
                    <TableContainer borderWidth="1px" borderRadius="lg" bg={useColorModeValue("white", "gray.800")}>
                        <Table variant="simple" size="md">
                            <Thead bg={tableHeaderBg}>
                                <Tr>
                                    <Th>№ Участка</Th>
                                    <Th isNumeric>Расход G (т/ч)</Th>
                                    <Th isNumeric>Давление P<sub>вх</sub> (кгс/см²)</Th>
                                    <Th isNumeric>Температура T (°C)</Th>
                                    <Th isNumeric>Энтальпия H (кДж/кг)</Th>
                                </Tr>
                            </Thead>
                            <Tbody>
                                {gi.map((_, index) => (
                                    <Tr key={index} _hover={{ bg: buttonHoverBg }}>
                                        <Td fontWeight="bold">Участок {index + 1}</Td>
                                        <Td isNumeric fontWeight="semibold">{roundNumber(gi[index])}</Td>
                                        <Td isNumeric>{roundNumber(pi_in[index])}</Td>
                                        <Td isNumeric>{roundNumber(ti[index])}</Td>
                                        <Td isNumeric color="gray.500">{roundNumber(hi[index])}</Td>
                                    </Tr>
                                ))}
                            </Tbody>
                        </Table>
                    </TableContainer>
                ) : (
                    <Text textAlign="center">Нет данных по участкам.</Text>
                )}
            </Box>

            {/* Таблица 2: Отсосы (Сводная) */}
            {(deaeratorProps.length > 0 || ejectorProps.length > 0) && (
                <Box>
                    <Heading as="h3" size="lg" mb={4} textAlign="center">Параметры отсосов и потребителей</Heading>
                    <TableContainer borderWidth="1px" borderRadius="lg" bg={useColorModeValue("white", "gray.800")}>
                        <Table variant="simple" size="md">
                            <Thead bg={tableHeaderBg}>
                                <Tr>
                                    <Th>Наименование потока</Th>
                                    <Th isNumeric>Расход G (т/ч)</Th>
                                    <Th isNumeric>Давление P (кгс/см²)</Th>
                                    <Th isNumeric>Температура T (°C)</Th>
                                    <Th isNumeric>Энтальпия H (кДж/кг)</Th>
                                </Tr>
                            </Thead>
                            <Tbody>
                                {/* Строка Деаэратора (если есть расход) */}
                                {deaeratorProps.length === 4 && deaeratorProps[0] > 0.000001 && (
                                    <Tr _hover={{ bg: buttonHoverBg }}>
                                        <Td>
                                            <HStack>
                                                <Badge colorScheme="purple">Деаэратор</Badge>
                                                <Text fontSize="sm">(из камеры 2)</Text>
                                            </HStack>
                                        </Td>
                                        <Td isNumeric fontWeight="bold" fontSize="lg">{roundNumber(deaeratorProps[0])}</Td>
                                        <Td isNumeric>{roundNumber(deaeratorProps[3])}</Td>
                                        <Td isNumeric>{roundNumber(deaeratorProps[1])}</Td>
                                        <Td isNumeric color="gray.500">{roundNumber(deaeratorProps[2])}</Td>
                                    </Tr>
                                )}

                                {/* Строки Эжекторов */}
                                {ejectorProps.map((ej, idx) => (
                                    <Tr key={`ej-${idx}`} _hover={{ bg: buttonHoverBg }}>
                                        <Td>
                                            <HStack>
                                                <Badge colorScheme="blue">Потребитель {idx + 1}</Badge>
                                                <Text fontSize="sm">(Эжектор / Вакуум)</Text>
                                            </HStack>
                                        </Td>
                                        <Td isNumeric fontWeight="bold" fontSize="lg">{roundNumber(ej.g)}</Td>
                                        <Td isNumeric>{roundNumber(ej.p)}</Td>
                                        <Td isNumeric>{roundNumber(ej.t)}</Td>
                                        <Td isNumeric color="gray.500">{roundNumber(ej.h)}</Td>
                                    </Tr>
                                ))}
                            </Tbody>
                        </Table>
                    </TableContainer>
                </Box>
            )}

            {/* Кнопки действий */}
            <HStack spacing={6} justifyContent="center" pt={4} pb={10}>
                {isEmbedded && (
                    <Button onClick={handleSaveToIde} colorScheme="purple" size="lg" leftIcon={<Icon as={FiSave} />}>
                        Сохранить в Balance+
                    </Button>
                )}
                <Button onClick={handleDownloadExcel} colorScheme="green" size="lg" leftIcon={<Icon as={FiFileText} />}>
                    Скачать Excel
                </Button>
                <Button onClick={handleDownloadDrawio} colorScheme="blue" size="lg" isLoading={isDownloadingDrawio} leftIcon={<Icon as={FiDownload} />}>
                    Скачать схему
                </Button>
            </HStack>
        </VStack>
    );
};

export default ResultsPage;