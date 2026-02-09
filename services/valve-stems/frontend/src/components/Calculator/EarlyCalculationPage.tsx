import React from 'react';
import {
    Box,
    Button,
    Heading,
    Text,
    VStack,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    TableContainer,
    SimpleGrid,
    Divider,
    HStack,
    Icon,
} from '@chakra-ui/react';

import {type CalculationResultDB as CalculationDataType} from '../../client';
import {FiChevronLeft} from "react-icons/fi";

type Props = {
    stockId: string;
    lastCalculation: CalculationDataType | null;
    onRecalculate: (recalculate: boolean) => void;
    onGoBack?: () => void;
};

const roundNumber = (num: any, decimals: number = 4): string | number => {
    const parsedNum = parseFloat(num);
    if (isNaN(parsedNum)) {
        return 'N/A';
    }
    return Number(parsedNum.toFixed(decimals));
};

const EarlyCalculationPage: React.FC<Props> = ({stockId, lastCalculation, onRecalculate, onGoBack}) => {
    if (!lastCalculation) {
        return (
            <VStack spacing={4} p={5} align="center" justify="center" minH="200px">
                <Text color="orange.500">Данные о предыдущем расчете отсутствуют или не загружены.</Text>
                {onGoBack && <Button onClick={onGoBack} colorScheme="teal" variant="outline" mt={4}>Вернуться к выбору
                    клапана</Button>}
                <Button onClick={() => onRecalculate(true)} colorScheme="teal" mt={2}>Продолжить с новым
                    расчетом</Button>
            </VStack>
        );
    }

    interface ExpectedInputData {
        turbine_name?: string;
        valve_drawing?: string;
        valve_id?: number;
        temperature_start?: number;
        t_air?: number;
        count_valves?: number;
        p_values?: number[];
        p_ejector?: number[];
    }

    interface ExpectedOutputData {
        Gi?: number[];
        Pi_in?: number[];
        Ti?: number[];
        Hi?: number[];
        deaerator_props?: any[];
        ejector_props?: Array<Record<string, number>>;
    }

    const inputData: ExpectedInputData = (lastCalculation.input_data || {}) as ExpectedInputData;
    const outputData: ExpectedOutputData = (lastCalculation.output_data || {}) as ExpectedOutputData;

    const gi = Array.isArray(outputData.Gi) ? outputData.Gi : [];
    const pi_in = Array.isArray(outputData.Pi_in) ? outputData.Pi_in : [];
    const ti = Array.isArray(outputData.Ti) ? outputData.Ti : [];
    const hi = Array.isArray(outputData.Hi) ? outputData.Hi : [];
    const deaeratorProps = Array.isArray(outputData.deaerator_props) ? outputData.deaerator_props : [];
    const ejectorProps = Array.isArray(outputData.ejector_props) ? outputData.ejector_props : [];

    const inputDataEntries = [
        {label: 'Название турбины', value: inputData.turbine_name},
        {label: 'Чертёж клапана', value: inputData.valve_drawing},
        {label: 'ID клапана', value: inputData.valve_id},
        {label: 'Начальная температура (°C)', value: inputData.temperature_start},
        {label: 'Температура воздуха (°C)', value: inputData.t_air},
        {label: 'Количество клапанов', value: inputData.count_valves},
        {
            label: 'Входные давления (P1-P5, МПа)',
            value: Array.isArray(inputData.p_values) ? inputData.p_values.join(', ') : 'N/A'
        },
        {
            label: 'Давления потребителей (МПа)',
            value: Array.isArray(inputData.p_ejector) ? inputData.p_ejector.join(', ') : 'N/A'
        },
    ];

    return (
        <VStack spacing={6} p={5} align="stretch" w="100%" maxW="container.lg" mx="auto">
            <Heading as="h2" size="xl" textAlign="center">
                Клапан: <Text as="span" color="teal.500">{stockId}</Text>
            </Heading>

            {onGoBack && (
                <Box width="100%" textAlign="center" my={2}>
                    <Button
                        onClick={onGoBack}
                        variant="outline"
                        colorScheme="teal"
                        size="sm"
                        leftIcon={<Icon as={FiChevronLeft}/>}
                    >
                        Изменить клапан
                    </Button>
                </Box>
            )}

            <Heading as="h3" size="lg" textAlign="center" color="orange.400">
                Обнаружен предыдущий расчет
            </Heading>

            <Box borderWidth="1px" borderRadius="md" p={4}>
                <Heading as="h4" size="md" mb={3}>
                    Входные данные предыдущего расчета:
                </Heading>
                {Object.keys(inputData).length > 0 ? (
                    <SimpleGrid columns={{base: 1, md: 2}} spacing={3}>
                        {inputDataEntries.map(entry => (
                            (entry.value !== undefined && entry.value !== null && entry.value !== '') &&
                            <HStack key={entry.label} justify="space-between">
                                <Text fontWeight="medium">{entry.label}:</Text>
                                <Text>{String(entry.value)}</Text>
                            </HStack>
                        ))}
                    </SimpleGrid>
                ) : (
                    <Text color="gray.500">Нет доступных входных данных для предыдущего расчета.</Text>
                )}
            </Box>

            <Divider my={6}/>

            <Heading as="h4" size="md" mb={3} textAlign="center">
                Выходные данные предыдущего расчета:
            </Heading>

            {gi.length > 0 ? (
                <TableContainer borderWidth="1px" borderRadius="md">
                    <Table variant="striped" colorScheme="gray" size="sm">
                        <Thead>
                            <Tr>
                                <Th>Расход, т/ч (G<sub>i</sub>)</Th>
                                <Th>Давление, МПа (P<sub>вхi</sub>)</Th>
                                <Th>Температура, °C (T<sub>i</sub>)</Th>
                                <Th>Энтальпия, кДж/кг (H<sub>i</sub>)</Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {gi.map((_value, index) => (
                                <Tr key={`gi-${index}`}>
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
                <Text color="gray.500" textAlign="center">Нет основных выходных данных.</Text>
            )}

            {ejectorProps.length > 0 && (
                <Box mt={6}>
                    <Heading as="h5" size="sm" mb={2}>Параметры потребителей (эжекторы):</Heading>
                    <TableContainer borderWidth="1px" borderRadius="md">
                        <Table variant="simple" size="sm">
                            <Thead>
                                <Tr>
                                    {ejectorProps[0] && typeof ejectorProps[0] === 'object' && Object.keys(ejectorProps[0]).map(key =>
                                        <Th key={key}>{key}</Th>)}
                                </Tr>
                            </Thead>
                            <Tbody>
                                {ejectorProps.map((prop, index) => (
                                    <Tr key={`ejector-${index}`}>
                                        {typeof prop === 'object' && prop !== null && Object.values(prop).map((val, idx) => (
                                            <Td key={idx}>{roundNumber(val)}</Td>
                                        ))}
                                    </Tr>
                                ))}
                            </Tbody>
                        </Table>
                    </TableContainer>
                </Box>
            )}

            {deaeratorProps.length > 0 && (
                <Box mt={4}>
                    <Heading as="h5" size="sm" mb={2}>Потребитель 1 (деаэратор):</Heading>
                    <SimpleGrid columns={{base: 2, md: deaeratorProps.length || 1}} spacing={2} borderWidth="1px"
                                borderRadius="md" p={3}>
                        {deaeratorProps.map((value, index) => (
                            <Box key={`deaerator-val-${index}`} textAlign="center">
                                <Text fontWeight="medium">Параметр {index + 1}:</Text>
                                <Text>{roundNumber(value)}</Text>
                            </Box>
                        ))}
                    </SimpleGrid>
                </Box>
            )}

            <VStack spacing={3} mt={8} align="center">
                <Heading as="h3" size="md">
                    Желаете провести перерасчет?
                </Heading>
                <HStack spacing={4} mt={2}>
                    <Button onClick={() => onRecalculate(true)} colorScheme="teal" variant="solid" size="lg"
                            minW="160px">
                        Да, пересчитать
                    </Button>
                    <Button onClick={() => onRecalculate(false)} colorScheme="gray" variant="outline" size="lg"
                            minW="160px">
                        Нет, использовать эти
                    </Button>
                </HStack>
            </VStack>
        </VStack>
    );
};

export default EarlyCalculationPage;