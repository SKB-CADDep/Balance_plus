import React, { useState, useEffect } from 'react';
import * as XLSX from 'xlsx';
import {
    Box, Button, Heading, Text, VStack, Table, Thead, Tbody, Tr, Th, Td,
    TableContainer, SimpleGrid, Divider, HStack, useToast, Icon, useColorModeValue, Badge,
} from '@chakra-ui/react';
import { FiChevronLeft, FiSave, FiFileText } from 'react-icons/fi';

type Props = {
    stockId: string;
    inputData?: any;
    outputData?: any;
    onGoBack?: () => void;
};

const roundNumber = (num: any, decimals: number = 4): string | number => {
    const parsed = parseFloat(num);
    if (isNaN(parsed)) return '-';
    if (parsed !== 0 && Math.abs(parsed) < 0.0001) return parsed.toExponential(2);
    return Number(parsed.toFixed(decimals));
};

const ResultsPage: React.FC<Props> = ({ stockId, inputData = {}, outputData = {}, onGoBack }) => {
    const toast = useToast();
    const tableHeaderBg = useColorModeValue("gray.50", "gray.700");
    const buttonHoverBg = useColorModeValue("gray.100", "gray.700");

    const details = outputData?.details || [];
    const summary = outputData?.summary;

    // --- ИНТЕГРАЦИЯ С BALANCE+ (IDE) ---
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

    // --- ЭКСПОРТ В EXCEL (Адаптировано под мульти-расчет) ---
    const handleDownloadExcel = () => {
        try {
            const wb = XLSX.utils.book_new();

            // Лист 1: Глобальные параметры
            const globalsData = [{
                'Турбина': inputData?.turbine_name,
                'P свежего пара': inputData?.globals?.P_fresh,
                'T свежего пара': inputData?.globals?.T_fresh,
                'P воздуха': inputData?.globals?.P_air,
                'T воздуха': inputData?.globals?.T_air,
                'Вакуум': inputData?.globals?.P_lst_leak_off,
            }];
            XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(globalsData), 'Глобальные параметры');

            // Лист 2: По участкам
            const sectionsData: any[] = [];
            details.forEach((group: any) => {
                group.Gi.forEach((g: number, i: number) => {
                    sectionsData.push({
                        'Группа клапанов': `${group.valve_names.join(', ')} (${group.quantity} шт)`,
                        'Участок': i + 1,
                        'Расход 1 шт (G), т/ч': roundNumber(g),
                        'Давление вх. (P), кгс/см²': roundNumber(group.Pi_in[i]),
                        'Температура (T), °C': roundNumber(group.Ti[i]),
                        'Энтальпия (H), кДж/кг': roundNumber(group.Hi[i]),
                    });
                });
            });
            if (sectionsData.length > 0) {
                XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(sectionsData), 'По участкам');
            }

            // Лист 3: Отсосы
            const suctionData: any[] = [];
            details.forEach((group: any) => {
                if (group.deaerator_props && group.deaerator_props[0] > 0.000001) {
                    suctionData.push({
                        'Группа клапанов': `${group.valve_names.join(', ')} (${group.quantity} шт)`,
                        'Потребитель': 'Деаэратор (Камера 2)',
                        'Расход ΣG, т/ч': roundNumber(group.deaerator_props[0]),
                        'Давление (P), кгс/см²': roundNumber(group.deaerator_props[3]),
                        'Температура (T), °C': roundNumber(group.deaerator_props[1]),
                    });
                }
                group.ejector_props.forEach((ej: any, idx: number) => {
                    suctionData.push({
                        'Группа клапанов': `${group.valve_names.join(', ')} (${group.quantity} шт)`,
                        'Потребитель': `Эжектор / Отсос ${idx + 1}`,
                        'Расход ΣG, т/ч': roundNumber(ej.g),
                        'Давление (P), кгс/см²': roundNumber(ej.p),
                        'Температура (T), °C': roundNumber(ej.t),
                    });
                });
            });
            if (suctionData.length > 0) {
                XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(suctionData), 'Отсосы');
            }

            // Лист 4: Итоги (Суммы)
            if (summary) {
                const summaryData = [
                    { 'Тип клапанов': 'Стопорные (СК)', 'Суммарный расход ΣG, т/ч': roundNumber(summary.sk.total_g) },
                    { 'Тип клапанов': 'Регулирующие (РК)', 'Суммарный расход ΣG, т/ч': roundNumber(summary.rk.total_g) },
                    { 'Тип клапанов': 'Стопорно-регулирующие (СРК)', 'Суммарный расход ΣG, т/ч': roundNumber(summary.srk.total_g) },
                ];
                XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(summaryData), 'Итоги');
            }

            XLSX.writeFile(wb, `Расчет_${inputData?.turbine_name || 'WSA'}.xlsx`);
            toast({ title: "Excel файл успешно создан", status: "success" });
        } catch (e: any) {
            console.error(e);
            toast({ title: "Ошибка экспорта", status: "error" });
        }
    };

    return (
        <VStack spacing={8} p={5} align="stretch" w="100%" maxW="container.xl" mx="auto">
            <VStack spacing={2} w="full">
                <Heading as="h2" size="xl" textAlign="center">
                    Результаты: <Text as="span" color="teal.500">{inputData?.turbine_name}</Text>
                </Heading>
                
                {isEmbedded ? (
                    <Button onClick={() => window.parent.postMessage({ type: 'WSA_CLOSE' }, '*')} variant="ghost" size="sm" leftIcon={<Icon as={FiChevronLeft} />}>
                        Вернуться в Balance+
                    </Button>
                ) : onGoBack && (
                    <Button onClick={onGoBack} variant="outline" colorScheme="teal" size="sm" leftIcon={<Icon as={FiChevronLeft} />} mt={2} _hover={{ bg: buttonHoverBg }}>
                        Изменить параметры расчета
                    </Button>
                )}
            </VStack>

            {/* ДЕТАЛИЗАЦИЯ ПО КАЖДОЙ ГРУППЕ КЛАПАНОВ */}
            {details.map((group: any, idx: number) => (
                <Box key={idx} borderWidth="1px" borderRadius="lg" p={5} bg={useColorModeValue("white", "gray.800")} shadow="sm">
                    <HStack mb={4} justify="space-between" wrap="wrap">
                        <Heading as="h3" size="md" color="teal.600">
                            {group.valve_names.join(', ')} ({group.quantity} шт.)
                        </Heading>
                        <Badge colorScheme="purple" fontSize="sm">Тип: {group.type}</Badge>
                    </HStack>

                    <TableContainer mb={6}>
                        <Table variant="simple" size="sm">
                            <Thead bg={tableHeaderBg}>
                                <Tr>
                                    <Th>Участок</Th>
                                    <Th isNumeric>Расход 1 шт. G (т/ч)</Th>
                                    <Th isNumeric>Давление P (кгс/см²)</Th>
                                    <Th isNumeric>Температура T (°C)</Th>
                                    <Th isNumeric>Энтальпия H (кДж/кг)</Th>
                                </Tr>
                            </Thead>
                            <Tbody>
                                {group.Gi.map((_: any, i: number) => (
                                    <Tr key={i} _hover={{ bg: buttonHoverBg }}>
                                        <Td fontWeight="bold">Участок {i + 1}</Td>
                                        <Td isNumeric>{roundNumber(group.Gi[i])}</Td>
                                        <Td isNumeric>{roundNumber(group.Pi_in[i])}</Td>
                                        <Td isNumeric>{roundNumber(group.Ti[i])}</Td>
                                        <Td isNumeric color="gray.500">{roundNumber(group.Hi[i])}</Td>
                                    </Tr>
                                ))}
                            </Tbody>
                        </Table>
                    </TableContainer>

                    {/* Отсосы этой группы */}
                    <Text fontWeight="bold" mb={2} fontSize="sm" color="gray.500">
                        Потребители (суммарно для {group.quantity} шт.):
                    </Text>
                    <TableContainer>
                        <Table variant="simple" size="sm">
                            <Thead bg={tableHeaderBg}>
                                <Tr>
                                    <Th>Потребитель</Th>
                                    <Th isNumeric>Расход ΣG (т/ч)</Th>
                                    <Th isNumeric>Давление P (кгс/см²)</Th>
                                    <Th isNumeric>Температура T (°C)</Th>
                                </Tr>
                            </Thead>
                            <Tbody>
                                {group.deaerator_props && group.deaerator_props[0] > 0.000001 && (
                                    <Tr _hover={{ bg: buttonHoverBg }}>
                                        <Td><Badge colorScheme="blue">Деаэратор</Badge></Td>
                                        <Td isNumeric fontWeight="bold">{roundNumber(group.deaerator_props[0])}</Td>
                                        <Td isNumeric>{roundNumber(group.deaerator_props[3])}</Td>
                                        <Td isNumeric>{roundNumber(group.deaerator_props[1])}</Td>
                                    </Tr>
                                )}
                                {group.ejector_props.map((ej: any, e_idx: number) => (
                                    <Tr key={`ej-${e_idx}`} _hover={{ bg: buttonHoverBg }}>
                                        <Td><Badge colorScheme="gray">Эжектор {e_idx + 1}</Badge></Td>
                                        <Td isNumeric fontWeight="bold">{roundNumber(ej.g)}</Td>
                                        <Td isNumeric>{roundNumber(ej.p)}</Td>
                                        <Td isNumeric>{roundNumber(ej.t)}</Td>
                                    </Tr>
                                ))}
                            </Tbody>
                        </Table>
                    </TableContainer>
                </Box>
            ))}

            <Divider />

            {/* СВОДНЫЕ ТАБЛИЦЫ ПО ТУРБИНЕ */}
            {summary && (
                <Box borderWidth="1px" borderRadius="lg" p={5} bg={useColorModeValue("teal.50", "gray.700")} shadow="sm">
                    <Heading as="h3" size="md" mb={6} textAlign="center">Итоговые сводные расходы по проекту</Heading>
                    <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6} textAlign="center">
                        <Box p={4} bg={useColorModeValue("white", "gray.800")} borderRadius="md" shadow="sm">
                            <Text fontSize="sm" fontWeight="bold" color="gray.500">Сумма стопорных (СК)</Text>
                            <Text fontSize="2xl" fontWeight="black" color="teal.600">{roundNumber(summary.sk.total_g)} т/ч</Text>
                        </Box>
                        <Box p={4} bg={useColorModeValue("white", "gray.800")} borderRadius="md" shadow="sm">
                            <Text fontSize="sm" fontWeight="bold" color="gray.500">Сумма регулирующих (РК)</Text>
                            <Text fontSize="2xl" fontWeight="black" color="teal.600">{roundNumber(summary.rk.total_g)} т/ч</Text>
                        </Box>
                        <Box p={4} bg={useColorModeValue("white", "gray.800")} borderRadius="md" shadow="sm">
                            <Text fontSize="sm" fontWeight="bold" color="gray.500">Сумма стоп-рег (СРК)</Text>
                            <Text fontSize="2xl" fontWeight="black" color="teal.600">{roundNumber(summary.srk.total_g)} т/ч</Text>
                        </Box>
                    </SimpleGrid>
                </Box>
            )}

            {/* КНОПКИ ДЕЙСТВИЙ */}
            <HStack spacing={6} justifyContent="center" pt={4} pb={10}>
                {isEmbedded && (
                    <Button onClick={handleSaveToIde} colorScheme="purple" size="lg" leftIcon={<Icon as={FiSave} />}>
                        Сохранить в Balance+
                    </Button>
                )}
                <Button onClick={handleDownloadExcel} colorScheme="green" size="lg" leftIcon={<Icon as={FiFileText} />}>
                    Скачать Excel
                </Button>
            </HStack>
        </VStack>
    );
};

export default ResultsPage;