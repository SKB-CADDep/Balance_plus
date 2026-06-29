import React, { useState, useEffect, useMemo } from 'react';
import * as XLSX from 'xlsx';
import {
    Box, Button, Heading, Text, VStack, Table, Thead, Tbody, Tr, Th, Td,
    TableContainer, Divider, HStack, useToast, Icon, useColorModeValue, Badge,
} from '@chakra-ui/react';
import { FiChevronLeft, FiDownload, FiSave, FiFileText } from 'react-icons/fi';

import { 
    type MultiCalculationParams, 
    type MultiCalculationResult,
    type GroupCalculationDetails,
} from '../../client';

type Props = {
    stockId: string;
    inputData?: MultiCalculationParams;
    outputData?: MultiCalculationResult;
    onGoBack?: () => void;
};

// Реализация BR-06 (если округляется до 0.00, но число не 0, показываем целиком)
const roundNumber = (num: any, decimals: number = 4): string | number => {
    const parsed = parseFloat(num);
    if (isNaN(parsed)) return '-';
    if (parsed === 0) return 0;
    
    const rounded = Number(parsed.toFixed(decimals));
    if (rounded === 0) {
        return parsed.toString();
    }
    return rounded;
};

const ResultsPage: React.FC<Props> = ({ stockId, inputData, outputData, onGoBack }) => {
    const toast = useToast();
    const tableHeaderBg = useColorModeValue("gray.50", "gray.700");
    const buttonHoverBg = useColorModeValue("gray.100", "gray.700");

    const [isDownloadingDrawio, setIsDownloadingDrawio] = useState<Record<number, boolean>>({});

    const details = outputData?.details || [];
    const pUnit = inputData?.globals?.P_fresh_unit || "кгс/см²";

    const [isEmbedded, setIsEmbedded] = useState(false);

    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        setIsEmbedded(urlParams.get('embedded') === 'true');
    }, []);

    // Сбор всех отсосов для новой итоговой таблицы
    const allSuctions = useMemo(() => {
        const suctions: any[] = [];
        details.forEach(group => {
            const groupName = `${group.valve_names.join(', ')} (${group.quantity} шт.)`;
            
            if (group.deaerator_props && group.deaerator_props[0] > 0.000001) {
                suctions.push({
                    groupName,
                    type: 'Деаэратор',
                    g: group.deaerator_props[0],
                    p: group.deaerator_props[3],
                    t: group.deaerator_props[1],
                    h: group.deaerator_props[2]
                });
            }
            if (group.ejector_props) {
                group.ejector_props.forEach((ej, idx) => {
                    suctions.push({
                        groupName,
                        type: `Отсос №${idx + 1}`,
                        g: ej.g,
                        p: ej.p,
                        t: ej.t,
                        h: ej.h
                    });
                });
            }
        });
        return suctions;
    }, [details]);

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

    const handleDownloadDrawio = async (groupDetail: GroupCalculationDetails) => {
        const groupInput = inputData?.groups.find(g => g.valve_id === groupDetail.valve_id);
        
        if (!groupInput) {
            toast({ title: "Ошибка", description: "Нет данных геометрии для генерации схемы.", status: "error" });
            return;
        }

        setIsDownloadingDrawio(prev => ({ ...prev, [groupDetail.valve_id]: true }));
        try {
            const baseUrl = import.meta.env.VITE_API_URL || '';
            const cleanBaseUrl = baseUrl.replace(/\/$/, '');
            const url = `${cleanBaseUrl}/api/v1/generate_scheme`;
            
            const mockValveInfo = {
                id: groupDetail.valve_id,
                name: groupDetail.valve_names[0],
                count_parts: groupDetail.Gi.length, 
            };

            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(mockValveInfo), 
            });
            
            if (!response.ok) throw new Error("Ошибка сервера при генерации схемы.");
            
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', `схема_${groupDetail.valve_names[0]}.drawio`);
            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);
        } catch (error: any) {
            toast({ title: "Ошибка", description: error.message, status: "error" });
        } finally {
            setIsDownloadingDrawio(prev => ({ ...prev, [groupDetail.valve_id]: false }));
        }
    };

    const handleDownloadExcel = () => {
        try {
            const excelData: any[][] = [];

            // Блок 1: Данные по каждой группе клапанов (Таблица 1 и 2)
            details.forEach((group) => {
                const partsCount = group.Gi.length;
                
                // ТАБЛИЦА 1
                excelData.push([`Таблица 1 - Вывод результатов по участкам. Группа: ${group.valve_names.join(', ')}`]);
                const headerRow1 = ['Обозначение', 'Размерность', ...Array.from({length: partsCount}, (_, i) => i + 1)];
                excelData.push(headerRow1);

                excelData.push(['P0', pUnit, ...group.Pi_in.map(v => roundNumber(v))]);
                excelData.push(['T0', '°C', ...group.Ti.map(v => roundNumber(v))]);
                excelData.push(['H', 'ккал/кг', ...group.Hi.map(v => roundNumber(v))]);
                excelData.push(['G', 'т/ч', ...group.Gi.map(v => roundNumber(v))]);
                excelData.push([]); 

                // ТАБЛИЦА 2
                excelData.push([`Таблица 2 - Вывод результатов по отсосам. Группа: ${group.valve_names.join(', ')}`]);
                excelData.push([' ', 'Расход', 'Давление', 'Температура', 'Энтальпия']);
                excelData.push([' ', 'т/ч', pUnit, '°C', 'ккал/кг']);

                let hasSuctions = false;

                if (group.deaerator_props && group.deaerator_props[0] > 0.000001) {
                    excelData.push([
                        'Деаэратор',
                        roundNumber(group.deaerator_props[0]),
                        roundNumber(group.deaerator_props[3]),
                        roundNumber(group.deaerator_props[1]),
                        roundNumber(group.deaerator_props[2])
                    ]);
                    hasSuctions = true;
                }

                if (group.ejector_props) {
                    group.ejector_props.forEach((ej, idx) => {
                        excelData.push([
                            `Отсос №${idx + 1}`,
                            roundNumber(ej.g),
                            roundNumber(ej.p),
                            roundNumber(ej.t),
                            roundNumber(ej.h)
                        ]);
                        hasSuctions = true;
                    });
                }

                if (!hasSuctions) {
                    excelData.push(['Нет отсосов', '-', '-', '-', '-']);
                }

                excelData.push([]); 
                excelData.push([]); 
            });

            // Блок 2: Итоговая сводная таблица по всем отсосам
            excelData.push(['Итоговая сводная таблица отсосов (по чертежам/группам)']);
            excelData.push(['Группа клапанов', 'Потребитель', 'Расход (т/ч)', `Давление (${pUnit})`, 'Температура (°C)', 'Энтальпия (ккал/кг)']);
            
            if (allSuctions.length > 0) {
                allSuctions.forEach(s => {
                    excelData.push([
                        s.groupName, 
                        s.type, 
                        roundNumber(s.g), 
                        roundNumber(s.p), 
                        roundNumber(s.t), 
                        roundNumber(s.h)
                    ]);
                });
            } else {
                excelData.push(['Отсосы отсутствуют', '-', '-', '-', '-', '-']);
            }

            // Создаем лист
            const wb = XLSX.utils.book_new();
            const ws = XLSX.utils.aoa_to_sheet(excelData);
            
            // Настройка ширины колонок
            ws['!cols'] = [{ wch: 30 }, { wch: 15 }, { wch: 15 }, { wch: 15 }, { wch: 15 }, { wch: 15 }];

            XLSX.utils.book_append_sheet(wb, ws, 'Результаты');
            XLSX.writeFile(wb, `Расчет_${stockId}.xlsx`);
            
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
                    Результаты расчета: <Text as="span" color="teal.500">{stockId}</Text>
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
            {details.map((group, idx) => {
                return (
                    <Box key={idx} borderWidth="1px" borderRadius="lg" p={5} bg={useColorModeValue("white", "gray.800")} shadow="sm">
                        <HStack mb={4} justify="space-between" wrap="wrap">
                            <Heading as="h3" size="md" color="teal.600">
                                {group.valve_names.join(', ')} ({group.quantity} шт.)
                            </Heading>
                            <HStack>
                                <Badge colorScheme="purple" fontSize="sm">Тип: {group.type}</Badge>
                                <Button 
                                    size="sm" 
                                    colorScheme="blue" 
                                    variant="outline"
                                    isLoading={isDownloadingDrawio[group.valve_id]} 
                                    leftIcon={<Icon as={FiDownload} />}
                                    onClick={() => handleDownloadDrawio(group)}
                                >
                                    Схема
                                </Button>
                            </HStack>
                        </HStack>

                        <Text fontWeight="bold" mb={2} fontSize="sm" color="gray.500">
                            Таблица 1 - Основные параметры участков
                        </Text>
                        <TableContainer mb={6}>
                            <Table variant="simple" size="sm">
                                <Thead bg={tableHeaderBg}>
                                    <Tr>
                                        <Th>Участок</Th>
                                        <Th isNumeric>Расход 1 шт. G (т/ч)</Th>
                                        <Th isNumeric>Давление P ({pUnit})</Th>
                                        <Th isNumeric>Температура T (°C)</Th>
                                        <Th isNumeric>Энтальпия H (ккал/кг)</Th>
                                    </Tr>
                                </Thead>
                                <Tbody>
                                    {group.Gi.map((g, i) => (
                                        <Tr key={i} _hover={{ bg: buttonHoverBg }}>
                                            <Td fontWeight="bold">Участок {i + 1}</Td>
                                            <Td isNumeric>{roundNumber(g)}</Td>
                                            <Td isNumeric>{roundNumber(group.Pi_in[i])}</Td>
                                            <Td isNumeric>{roundNumber(group.Ti[i])}</Td>
                                            <Td isNumeric color="gray.500">{roundNumber(group.Hi[i])}</Td>
                                        </Tr>
                                    ))}
                                </Tbody>
                            </Table>
                        </TableContainer>

                        <Text fontWeight="bold" mb={2} fontSize="sm" color="gray.500">
                            Таблица 2 - Потребители (суммарно для {group.quantity} шт.)
                        </Text>
                        <TableContainer>
                            <Table variant="simple" size="sm">
                                <Thead bg={tableHeaderBg}>
                                    <Tr>
                                        <Th>Потребитель</Th>
                                        <Th isNumeric>Расход ΣG (т/ч)</Th>
                                        <Th isNumeric>Давление P ({pUnit})</Th>
                                        <Th isNumeric>Температура T (°C)</Th>
                                        <Th isNumeric>Энтальпия H (ккал/кг)</Th>
                                    </Tr>
                                </Thead>
                                <Tbody>
                                    {group.deaerator_props && group.deaerator_props[0] > 0.000001 && (
                                        <Tr _hover={{ bg: buttonHoverBg }}>
                                            <Td><Badge colorScheme="blue">Деаэратор</Badge></Td>
                                            <Td isNumeric fontWeight="bold">{roundNumber(group.deaerator_props[0])}</Td>
                                            <Td isNumeric>{roundNumber(group.deaerator_props[3])}</Td>
                                            <Td isNumeric>{roundNumber(group.deaerator_props[1])}</Td>
                                            <Td isNumeric color="gray.500">{roundNumber(group.deaerator_props[2])}</Td>
                                        </Tr>
                                    )}
                                    {group.ejector_props && group.ejector_props.map((ej, e_idx) => (
                                        <Tr key={`ej-${e_idx}`} _hover={{ bg: buttonHoverBg }}>
                                            <Td><Badge colorScheme="gray">Отсос №{e_idx + 1}</Badge></Td>
                                            <Td isNumeric fontWeight="bold">{roundNumber(ej.g)}</Td>
                                            <Td isNumeric>{roundNumber(ej.p)}</Td>
                                            <Td isNumeric>{roundNumber(ej.t)}</Td>
                                            <Td isNumeric color="gray.500">{roundNumber(ej.h)}</Td>
                                        </Tr>
                                    ))}
                                </Tbody>
                            </Table>
                        </TableContainer>
                    </Box>
                );
            })}

            <Divider />

            {/* НОВАЯ СВОДНАЯ ТАБЛИЦА ПО ОТСОСАМ (ВМЕСТО СТАРОЙ) */}
            <Box borderWidth="1px" borderRadius="lg" p={5} bg={useColorModeValue("white", "gray.800")} shadow="sm" borderTopWidth="4px" borderTopColor="teal.500">
                <Heading as="h3" size="md" mb={4} textAlign="center">
                    Итоговая сводная таблица отсосов
                </Heading>
                
                {allSuctions.length > 0 ? (
                    <TableContainer>
                        <Table variant="simple" size="md">
                            <Thead bg={tableHeaderBg}>
                                <Tr>
                                    <Th>Группа клапанов (Чертеж)</Th>
                                    <Th>Потребитель</Th>
                                    <Th isNumeric>Расход ΣG (т/ч)</Th>
                                    <Th isNumeric>Давление ({pUnit})</Th>
                                    <Th isNumeric>Температура (°C)</Th>
                                    <Th isNumeric>Энтальпия (ккал/кг)</Th>
                                </Tr>
                            </Thead>
                            <Tbody>
                                {allSuctions.map((s, idx) => (
                                    <Tr key={idx} _hover={{ bg: buttonHoverBg }}>
                                        <Td fontWeight="medium">{s.groupName}</Td>
                                        <Td>{s.type}</Td>
                                        <Td isNumeric fontWeight="bold" color="teal.600">{roundNumber(s.g)}</Td>
                                        <Td isNumeric>{roundNumber(s.p)}</Td>
                                        <Td isNumeric>{roundNumber(s.t)}</Td>
                                        <Td isNumeric color="gray.500">{roundNumber(s.h)}</Td>
                                    </Tr>
                                ))}
                            </Tbody>
                        </Table>
                    </TableContainer>
                ) : (
                    <Text textAlign="center" color="gray.500">Отсосы в данной схеме отсутствуют.</Text>
                )}
            </Box>

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