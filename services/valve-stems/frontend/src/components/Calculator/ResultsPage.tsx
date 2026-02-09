import React, {useState, useEffect} from 'react';
import * as XLSX from 'xlsx';
import {
    Box, Button, Heading, Text, VStack, Table, Thead, Tbody, Tr, Th, Td,
    TableContainer, SimpleGrid, Divider, HStack, useToast, Icon, useColorModeValue, Flex,
} from '@chakra-ui/react';
// Убрали FiChevronLeft из импорта, если он не используется в этом файле (или добавьте, если нужен для навигации)
// В вашем коде он используется в кнопках "Назад", так что оставляем.
import {FiChevronLeft, FiDownload, FiSave} from 'react-icons/fi';
import { OpenAPI, type CalculationParams, type ValveInfo_Output as ValveInfo } from '../../client';

export interface ExpectedOutputData {
    Gi?: number[];
    Pi_in?: number[];
    Ti?: number[];
    Hi?: number[];
    deaerator_props?: any[];
    ejector_props?: Array<Record<string, number>>;
}

type Props = {
    stockId: string;
    stockInfo?: ValveInfo | null;
    calculationId?: number;
    inputData?: Partial<CalculationParams>;
    outputData?: Partial<ExpectedOutputData>;
    onGoBack?: () => void;
};

const roundNumber = (num: any, decimals: number = 4): string | number => {
    const parsedNum = parseFloat(num);
    if (isNaN(parsedNum)) {
        return 'N/A';
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
    // УДАЛЕНО: const [isSavedMessageVisible, setIsSavedMessageVisible] = useState(false);
    
    const toast = useToast();
    const buttonHoverBg = useColorModeValue("gray.100", "gray.700");

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
        {label: 'Название турбины', value: currentInputData.turbine_name},
        {label: 'Чертёж клапана', value: currentInputData.valve_drawing},
        {label: 'ID клапана', value: currentInputData.valve_id},
        {label: 'Начальная температура (°C)', value: currentInputData.temperature_start},
        {label: 'Температура воздуха (°C)', value: currentInputData.t_air},
        {label: 'Количество клапанов', value: currentInputData.count_valves},
        {
            label: 'Входные давления (P1-P..., МПа)',
            value: Array.isArray(currentInputData.p_values) ? currentInputData.p_values.map(p => roundNumber(p, 3)).join('; ') : 'N/A'
        },
        {
            label: 'Давления потребителей (МПа)',
            value: Array.isArray(currentInputData.p_ejector) ? currentInputData.p_ejector.map(p => roundNumber(p, 3)).join('; ') : 'N/A'
        },
    ];

    const gi = Array.isArray(currentOutputData.Gi) ? currentOutputData.Gi : [];
    const pi_in = Array.isArray(currentOutputData.Pi_in) ? currentOutputData.Pi_in : [];
    const ti = Array.isArray(currentOutputData.Ti) ? currentOutputData.Ti : [];
    const hi = Array.isArray(currentOutputData.Hi) ? currentOutputData.Hi : [];
    const deaeratorProps = Array.isArray(currentOutputData.deaerator_props) ? currentOutputData.deaerator_props : [];
    const ejectorProps = Array.isArray(currentOutputData.ejector_props) ? currentOutputData.ejector_props : [];

    const handleDownloadDrawio = async () => {
        if (!stockInfo) {
            toast({
                title: "Ошибка",
                description: "Полная информация о штоке недоступна для генерации схемы.",
                status: "error"
            });
            return;
        }

        setIsDownloadingDrawio(true);
        try {
            const url = `${OpenAPI.BASE}/api/v1/generate_scheme`;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/vnd.jgraph.mxfile, */*',
                },
                body: JSON.stringify(stockInfo),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                throw new Error(errorData?.detail || `Ошибка сервера: ${response.status} ${response.statusText}`);
            }

            const disposition = response.headers.get('content-disposition');
            let filename = `схема_${stockInfo.name || stockId}.drawio`;
            if (disposition && disposition.includes('attachment')) {
                const filenameMatch = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);

            toast({ title: "Схема Draw.io успешно загружена!", status: "success" });

        } catch (error: any) {
            console.error("Ошибка при скачивании Draw.io:", error);
            toast({
                title: "Ошибка при скачивании схемы",
                description: error?.message || "Произошла неизвестная ошибка.",
                status: "error",
            });
        } finally {
            setIsDownloadingDrawio(false);
        }
    };

    const handleDownloadExcel = () => {
        try {
            const wb = XLSX.utils.book_new();
            if (Object.keys(currentInputData).length > 0) {
                const inputSheetData = [{
                    'Название турбины': currentInputData.turbine_name,
                    'Чертёж клапана': currentInputData.valve_drawing,
                    'ID клапана': currentInputData.valve_id,
                    'Начальная температура': currentInputData.temperature_start,
                    'Температура воздуха': currentInputData.t_air,
                    'Количество клапанов': currentInputData.count_valves,
                    'Выходные давления (P_ejector)': Array.isArray(currentInputData.p_ejector) ? currentInputData.p_ejector.join(', ') : '',
                    'Входные давления (P_values)': Array.isArray(currentInputData.p_values) ? currentInputData.p_values.join(', ') : '',
                }];
                const inputWs = XLSX.utils.json_to_sheet(inputSheetData);
                XLSX.utils.book_append_sheet(wb, inputWs, 'Входные данные');
            }

            if (gi.length > 0) {
                const mainOutputData = gi.map((_g: number, index: number) => ({
                    'Расход, т/ч': roundNumber(gi[index]),
                    'Давление, МПа': roundNumber(pi_in[index]),
                    'Температура, °C': roundNumber(ti[index]),
                    'Энтальпия, кДж/кг': roundNumber(hi[index]),
                }));
                const mainOutputWs = XLSX.utils.json_to_sheet(mainOutputData);
                XLSX.utils.book_append_sheet(wb, mainOutputWs, 'Основные выходные');
            }

            if (ejectorProps.length > 0) {
                const ejectorSheetData = ejectorProps.map(prop => {
                    const row: { [key: string]: string | number } = {};
                    if (prop && typeof prop === 'object') {
                        for (const key in prop) {
                            row[key.toUpperCase()] = roundNumber(prop[key]);
                        }
                    }
                    return row;
                });
                const ejectorWs = XLSX.utils.json_to_sheet(ejectorSheetData);
                XLSX.utils.book_append_sheet(wb, ejectorWs, 'Параметры эжекторов');
            }

            if (deaeratorProps.length > 0) {
                const deaeratorSheetData = deaeratorProps.map((val, idx) => ({
                    [`Параметр ${idx + 1}`]: roundNumber(val)
                }));
                const deaeratorWs = XLSX.utils.json_to_sheet(deaeratorSheetData);
                XLSX.utils.book_append_sheet(wb, deaeratorWs, 'Параметры деаэратора');
            }

            XLSX.writeFile(wb, `Расчет_${stockId || 'клапана'}.xlsx`);
            toast({title: "Excel файл успешно создан!", status: "success", duration: 3000, isClosable: true});
        } catch (e: any) {
            console.error("Ошибка при создании Excel:", e);
            toast({
                title: "Ошибка при создании Excel",
                description: e?.message || String(e),
                status: "error",
                duration: 5000,
                isClosable: true
            });
        }
    };

    // УДАЛЕНО: const handleShowSavedMessage = ...

    return (
        <VStack spacing={8} p={5} align="stretch" w="100%" maxW="container.xl" mx="auto">
            <VStack spacing={2} w="full">
                <Heading as="h2" size="xl" textAlign="center">
                    Результаты расчётов для клапана: <Text as="span" color="teal.500">{stockId}</Text>
                </Heading>
                
                {isEmbedded && (
                   <Button
                        onClick={() => window.parent.postMessage({ type: 'WSA_CLOSE' }, '*')}
                        variant="ghost"
                        size="sm"
                        leftIcon={<Icon as={FiChevronLeft}/>}
                    >
                        Вернуться в Balance+
                    </Button>
                )}

                {!isEmbedded && onGoBack && (
                    <Button
                        onClick={onGoBack}
                        variant="outline"
                        colorScheme="teal"
                        size="sm"
                        leftIcon={<Icon as={FiChevronLeft}/>}
                        alignSelf="center"
                        mt={2}
                        _hover={{bg: buttonHoverBg}}
                    >
                        Вернуться к вводу данных
                    </Button>
                )}
            </VStack>

            <Box borderWidth="1px" borderRadius="lg" p={5} boxShadow="base">
                <Heading as="h3" size="lg" mb={4} color={useColorModeValue("gray.700", "whiteAlpha.800")}>
                    Входные данные:
                </Heading>
                {Object.keys(currentInputData).length > 0 ? (
                    <SimpleGrid columns={{base: 1, md: 2}} spacingX={8} spacingY={3}>
                        {inputDataEntries.map(entry => (
                            (entry.value !== undefined && entry.value !== null && String(entry.value).trim() !== '' && entry.value !== 'N/A') &&
                            <Flex key={entry.label} justify="space-between" py={1}>
                                <Text fontWeight="medium"
                                      color={useColorModeValue("gray.600", "gray.300")}>{entry.label}:</Text>
                                <Text fontWeight="semibold">{String(entry.value)}</Text>
                            </Flex>
                        ))}
                    </SimpleGrid>
                ) : (
                    <Text color="gray.500">Нет доступных входных данных.</Text>
                )}
            </Box>

            <Divider my={6} borderColor={useColorModeValue("gray.300", "gray.600")}/>

            <Heading as="h3" size="lg" mb={4} textAlign="center"
                     color={useColorModeValue("gray.700", "whiteAlpha.800")}>
                Выходные данные:
            </Heading>

            {gi.length > 0 ? (
                <TableContainer borderWidth="1px" borderRadius="md" mb={6}>
                    <Table variant="striped" colorScheme="gray" size="md">
                        <Thead>
                            <Tr>
                                <Th>Расход, т/ч (G<sub>i</sub>)</Th>
                                <Th>Давление, МПа (P<sub>вхi</sub>)</Th>
                                <Th>Температура, °C (T<sub>i</sub>)</Th>
                                <Th>Энтальпия, кДж/кг (H<sub>i</sub>)</Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {gi.map((_value: number, index: number) => (
                                <Tr key={`gi-res-${index}`}>
                                    <Td>{roundNumber(gi[index])}</Td>
                                    <Td>{roundNumber(pi_in[index])}</Td>
                                    <Td>{roundNumber(ti[index])}</Td>
                                    <Td>{roundNumber(hi[index])}</Td>
                                </Tr>
                            ))}
                        </Tbody>
                    </Table>
                </TableContainer>
            ) : (
                <Text color="gray.500" textAlign="center" mb={6}>Нет основных выходных данных.</Text>
            )}

            {ejectorProps.length > 0 && (
                <Box mb={6}>
                    <Heading as="h4" size="md" mb={3} color={useColorModeValue("gray.700", "whiteAlpha.800")}>
                        Параметры потребителей (эжекторы):
                    </Heading>
                    <TableContainer borderWidth="1px" borderRadius="lg" boxShadow="base"
                                    bg={useColorModeValue("white", "gray.750")}>
                        <Table variant="simple" size="md">
                            <Thead>
                                <Tr>
                                    {ejectorProps[0] && typeof ejectorProps[0] === 'object'
                                        ? Object.keys(ejectorProps[0]).map(key => (
                                            <Th key={`th-ejector-${key}`} textTransform="uppercase"
                                                letterSpacing="wider">
                                                {key}
                                            </Th>
                                        ))
                                        : <Th>Данные</Th>
                                    }
                                </Tr>
                            </Thead>
                            <Tbody>
                                {ejectorProps.map((prop, index: number) => (
                                    <Tr key={`ejector-res-${index}`}
                                        _hover={{bg: useColorModeValue("gray.50", "gray.650")}}>
                                        {typeof prop === 'object' && prop !== null
                                            ? Object.values(prop).map((val, idx: number) => (
                                                <Td key={`td-ejector-${index}-${idx}`}>{roundNumber(val)}</Td>
                                            ))
                                            : <Td colSpan={Object.keys(ejectorProps[0] || {}).length || 1}
                                                  textAlign="center">Данные отсутствуют</Td>
                                        }
                                    </Tr>
                                ))}
                            </Tbody>
                        </Table>
                    </TableContainer>
                </Box>
            )}

            {deaeratorProps.length > 0 && (
                <Box mb={6}>
                    <Heading as="h4" size="md" mb={3} color={useColorModeValue("gray.700", "whiteAlpha.800")}>
                        Потребитель 1 (деаэратор):
                    </Heading>
                    <SimpleGrid
                        columns={{base: 2, sm: Math.min(4, deaeratorProps.length) || 1}}
                        spacing={4}
                        borderWidth="1px"
                        borderRadius="lg"
                        p={4}
                        boxShadow="base"
                        bg={useColorModeValue("white", "gray.750")}
                    >
                        {deaeratorProps.map((value: any, idx: number) => (
                            <Box key={`deaerator-item-${idx}`} textAlign="center" p={2}>
                                <Text fontWeight="medium" color={useColorModeValue("gray.500", "gray.400")}
                                      fontSize="sm">
                                    Параметр {idx + 1}
                                </Text>
                                <Text fontSize="xl" fontWeight="bold">{roundNumber(value)}</Text>
                            </Box>
                        ))}
                    </SimpleGrid>
                </Box>
            )}

            <HStack spacing={6} justifyContent="center" mt={8} mb={4}>
                
                {isEmbedded && (
                    <Button
                        onClick={handleSaveToIde}
                        colorScheme="purple"
                        variant="solid"
                        size="lg"
                        minW="240px"
                        leftIcon={<Icon as={FiSave}/>}
                        boxShadow="md"
                        _hover={{boxShadow: "lg", bg: "purple.600"}}
                    >
                        Сохранить в Balance+
                    </Button>
                )}
                
                <Button onClick={handleDownloadExcel} colorScheme="green" variant="solid" size="lg">
                    Сохранить в Excel
                </Button>
                
                {/* Кнопка использует FiDownload, поэтому импорт нужен */}
                <Button 
                    onClick={handleDownloadDrawio} 
                    colorScheme="blue" 
                    size="lg" 
                    isLoading={isDownloadingDrawio}
                    leftIcon={<Icon as={FiDownload}/>}
                >
                    Скачать схему .vsdx
                </Button>

            </HStack>
        </VStack>
    );
};

export default ResultsPage;