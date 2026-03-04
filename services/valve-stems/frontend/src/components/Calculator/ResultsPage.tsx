import React, { useState, useEffect } from 'react';
import * as XLSX from 'xlsx';
import {
    Box, Button, Heading, Text, VStack, Table, Thead, Tbody, Tr, Th, Td,
    TableContainer, SimpleGrid, Divider, HStack, useToast, Icon, useColorModeValue, Badge,
} from '@chakra-ui/react';
import { FiChevronLeft, FiDownload, FiSave, FiFileText } from 'react-icons/fi';

import { 
    type MultiCalculationParams, 
    type MultiCalculationResult,
    type ValveInfo_Output as ValveInfo 
} from '../../client';

type Props = {
    stockId: string;
    stockInfo?: ValveInfo | null;
    calculationId?: number;
    inputData?: Partial<MultiCalculationParams>;
    outputData?: Partial<MultiCalculationResult>;
    onGoBack?: () => void;
    isEmbedded?: boolean; 
    taskId?: string;
};

const roundNumber = (num: any, decimals: number = 4): string | number => {
    const parsedNum = parseFloat(num);
    if (isNaN(parsedNum)) {
        return '-';
    }
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

    // Достаем данные первого клапана из нового массива details для старой отрисовки
    const currentInputData = inputData || {};
    const firstGroupInput = currentInputData.groups?.[0];
    const firstGroupOutput = outputData?.details?.[0] || {} as any;

    const inputDataEntries = [
        { label: 'ID турбины', value: currentInputData.turbine_id },
        { label: 'Группа', value: stockId },
        { label: 'Кол-во', value: firstGroupInput?.quantity || 1 },
        { label: 'Температура пара', value: currentInputData.globals?.T_fresh ? `${currentInputData.globals.T_fresh} ${currentInputData.globals.T_fresh_unit}` : 'N/A' },
        { label: 'Энтальпия пара', value: currentInputData.globals?.H_fresh ? `${currentInputData.globals.H_fresh} ${currentInputData.globals.H_fresh_unit}` : 'N/A' },
        { label: 'Воздух', value: `${currentInputData.globals?.T_air}°C, ${currentInputData.globals?.P_air}` },
        {
            label: 'Входные давления (кгс/см²)',
            value: Array.isArray(firstGroupInput?.p_values) ? firstGroupInput.p_values.map((p: any) => roundNumber(p, 3)).join(' → ') : 'N/A'
        },
    ];

    const gi = Array.isArray(firstGroupOutput.Gi) ? firstGroupOutput.Gi : [];
    const pi_in = Array.isArray(firstGroupOutput.Pi_in) ? firstGroupOutput.Pi_in : [];
    const ti = Array.isArray(firstGroupOutput.Ti) ? firstGroupOutput.Ti : [];
    const hi = Array.isArray(firstGroupOutput.Hi) ? firstGroupOutput.Hi : [];

    const deaeratorProps = Array.isArray(firstGroupOutput.deaerator_props) ? firstGroupOutput.deaerator_props : [];
    const ejectorProps = Array.isArray(firstGroupOutput.ejector_props) ? firstGroupOutput.ejector_props : [];

    const handleDownloadDrawio = async () => {
        if (!stockInfo) {
            toast({ title: "Ошибка", description: "Нет данных для генерации схемы.", status: "error" });
            return;
        }
        setIsDownloadingDrawio(true);
        try {
            const baseUrl = import.meta.env.VITE_API_URL || '';
            const cleanBaseUrl = baseUrl.replace(/\/$/, '');
            const url = `${cleanBaseUrl}/api/v1/generate_scheme`;
            
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

            const inputSheetData = [{
                'ID Турбины': currentInputData.turbine_id,
                'Группа': stockId,
                'Кол-во клапанов': firstGroupInput?.quantity,
            }];
            XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(inputSheetData), 'Входные данные');

            if (gi.length > 0) {
                const mainOutputData = gi.map((_g: any, index: number) => ({
                    'Участок': index + 1,
                    'Расход (G), т/ч': roundNumber(gi[index]),
                    'Давление вх. (P), кгс/см²': roundNumber(pi_in[index]),
                    'Температура (T), °C': roundNumber(ti[index]),
                    'Энтальпия (H), кДж/кг': roundNumber(hi[index]),
                }));
                XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(mainOutputData), 'По участкам');
            }

            const suctionData: any[] = [];
            
            if (deaeratorProps.length === 4 && deaeratorProps[0] > 0) {
                suctionData.push({
                    'Потребитель': 'Деаэратор (Камера 2)',
                    'Расход (G), т/ч': roundNumber(deaeratorProps[0]),
                    'Давление (P), кгс/см²': roundNumber(deaeratorProps[3]),
                    'Температура (T), °C': roundNumber(deaeratorProps[1]),
                    'Энтальпия (H), кДж/кг': roundNumber(deaeratorProps[2]),
                });
            }

            ejectorProps.forEach((ej: any, idx: number) => {
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
            <VStack spacing={2} w="full">
                <Heading as="h2" size="xl" textAlign="center">
                    Результаты: <Text as="span" color="teal.500">{stockId}</Text>
                </Heading>

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

            <Box>
                <Heading as="h3" size="lg" mb={4} textAlign="center">Распределение по участкам (Для группы клапанов)</Heading>
                {gi.length > 0 ? (
                    <TableContainer borderWidth="1px" borderRadius="lg" bg={useColorModeValue("white", "gray.800")}>
                        <Table variant="simple" size="md">
                            <Thead bg={tableHeaderBg}>
                                <Tr>
                                    <Th>№ Участка</Th>
                                    <Th isNumeric>Расход G (т/ч)</Th>
                                    <Th isNumeric>Давление P<sub>вх</sub></Th>
                                    <Th isNumeric>Температура T (°C)</Th>
                                    <Th isNumeric>Энтальпия H</Th>
                                </Tr>
                            </Thead>
                            <Tbody>
                                {gi.map((_: any, index: number) => (
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

            {(deaeratorProps.length > 0 || ejectorProps.length > 0) && (
                <Box>
                    <Heading as="h3" size="lg" mb={4} textAlign="center">Параметры отсосов и потребителей</Heading>
                    <TableContainer borderWidth="1px" borderRadius="lg" bg={useColorModeValue("white", "gray.800")}>
                        <Table variant="simple" size="md">
                            <Thead bg={tableHeaderBg}>
                                <Tr>
                                    <Th>Наименование потока</Th>
                                    <Th isNumeric>Расход G (т/ч)</Th>
                                    <Th isNumeric>Давление P</Th>
                                    <Th isNumeric>Температура T (°C)</Th>
                                    <Th isNumeric>Энтальпия H</Th>
                                </Tr>
                            </Thead>
                            <Tbody>
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

                                {ejectorProps.map((ej: any, idx: number) => (
                                    <Tr key={`ej-${idx}`} _hover={{ bg: buttonHoverBg }}>
                                        <Td>
                                            <HStack>
                                                <Badge colorScheme="blue">Потребитель {idx + 1}</Badge>
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

            <HStack spacing={6} justifyContent="center" pt={4} pb={10}>
                {isEmbedded && (
                    <Button onClick={handleSaveToIde} colorScheme="purple" size="lg" leftIcon={<Icon as={FiSave} />}>
                        Сохранить
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