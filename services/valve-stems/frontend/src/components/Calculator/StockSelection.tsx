import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    Box, Button, Flex, Heading, Icon, List, ListItem, Spinner, Tag, Text,
    useColorModeValue, VStack, NumberInput, NumberInputField, NumberInputStepper,
    NumberIncrementStepper, NumberDecrementStepper, HStack
} from '@chakra-ui/react';
import { FiChevronLeft, FiArrowRight } from "react-icons/fi";

import { type TurbineInfo, TurbinesService, type TurbineValves as ClientTurbineValvesResponse, type ValveInfo_Output as ClientValveInfo } from '../../client';

export type SelectedStock = { valve: ClientValveInfo; quantity: number };

type Props = {
    turbine: (TurbineInfo & { station_name?: string; station_number?: string; factory_number?: string }) | null;
    onSelectValves: (selections: SelectedStock[]) => void;
    onGoBack?: () => void;
};

const fetchValvesForTurbineAPI = async (turbineId: number) => {
    if (!turbineId) return { count: 0, valves: [] };
    return TurbinesService.turbinesGetValvesByTurbineEndpoint({ turbineName: turbineId.toString() as any });
};

const StockSelection: React.FC<Props> = ({ turbine, onSelectValves, onGoBack }) => {
    const turbineId = turbine?.id;

    const { data: turbineValvesResponse, isLoading, isError, error } = useQuery<ClientTurbineValvesResponse, Error>({
        queryKey: ['valvesForTurbine', turbineId],
        queryFn: () => fetchValvesForTurbineAPI(turbineId!),
        enabled: !!turbineId,
    });

    const [counts, setCounts] = useState<Record<number, number>>({});

    const valves = turbineValvesResponse?.valves || [];
    const totalSelected = Object.values(counts).reduce((a, b) => a + b, 0);

    const handleCountChange = (id: number, valString: string) => {
        const val = parseInt(valString, 10);
        setCounts(prev => ({ ...prev, [id]: isNaN(val) ? 0 : val }));
    };

    const handleNext = () => {
        const selections = valves
            .filter(v => (counts[v.id] || 0) > 0)
            .map(v => ({ valve: v, quantity: counts[v.id] }));
        onSelectValves(selections);
    };

    const listItemHoverBg = useColorModeValue('teal.50', 'gray.700');
    const listItemHoverBorderColor = useColorModeValue('teal.300', 'teal.500');

    if (!turbine) {
        return (
            <VStack spacing={4} p={5} align="center" justify="center" minH="200px">
                <Text>Турбина не выбрана.</Text>
                {onGoBack && <Button onClick={onGoBack} colorScheme="teal">Вернуться к выбору проекта</Button>}
            </VStack>
        );
    }

    return (
        <VStack spacing={6} p={5} align="stretch" w="100%" maxW="container.md" mx="auto">
            <VStack spacing={1}>
                <Heading as="h2" size="lg" textAlign="center">
                    Выбранный проект: <Text as="span" color="teal.500">{turbine.name}</Text>
                </Heading>
                <Text fontSize="md" color="gray.500">
                    {turbine.station_name || "Станция не указана"} {turbine.station_number ? `(Ст. №${turbine.station_number})` : ''} 
                    {turbine.factory_number ? ` | Зав. №${turbine.factory_number}` : ''}
                </Text>
            </VStack>

            {onGoBack && (
                <Box width="100%" textAlign="center" mb={2}>
                    <Button onClick={onGoBack} variant="outline" colorScheme="teal" size="sm" leftIcon={<Icon as={FiChevronLeft} />}>
                        Изменить проект
                    </Button>
                </Box>
            )}

            <Heading as="h3" size="md" textAlign="center" mt={4}>
                Укажите количество для необходимых клапанов
            </Heading>

            {isLoading ? (
                <VStack spacing={4} align="center" justify="center" minH="150px">
                    <Spinner size="xl" color="teal.500" />
                    <Text>Загрузка клапанов...</Text>
                </VStack>
            ) : isError ? (
                <VStack spacing={4} align="center" justify="center" minH="150px" color="red.500">
                    <Text>Ошибка при загрузке клапанов: {error?.message}</Text>
                </VStack>
            ) : valves.length > 0 ? (
                <List spacing={3} w="100%" mt={4}>
                    {valves.map((valve) => (
                        <ListItem
                            key={valve.id}
                            p={4}
                            borderWidth="1px"
                            borderRadius="lg"
                            borderColor={counts[valve.id] > 0 ? listItemHoverBorderColor : undefined}
                            bg={counts[valve.id] > 0 ? listItemHoverBg : undefined}
                            transition="all 0.2s"
                        >
                            <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
                                <Box>
                                    <Text fontSize="lg" fontWeight="medium">{valve.name}</Text>
                                    <HStack mt={1}>
                                        {valve.type && <Tag size="sm" colorScheme="cyan">{valve.type}</Tag>}
                                        <Text fontSize="xs" color="gray.500">Участков: {valve.count_parts || 3}</Text>
                                    </HStack>
                                </Box>
                                <HStack>
                                    <Text fontWeight="medium" fontSize="sm">Количество:</Text>
                                    <NumberInput 
                                        min={0} max={20} 
                                        value={counts[valve.id] || 0} 
                                        onChange={(valueAsString) => handleCountChange(valve.id, valueAsString)}
                                        w="100px"
                                        bg={useColorModeValue('white', 'gray.800')}
                                    >
                                        <NumberInputField />
                                        <NumberInputStepper>
                                            <NumberIncrementStepper />
                                            <NumberDecrementStepper />
                                        </NumberInputStepper>
                                    </NumberInput>
                                </HStack>
                            </Flex>
                        </ListItem>
                    ))}
                </List>
            ) : (
                <Text textAlign="center" color="gray.500" p={4} borderWidth="1px" borderRadius="md" borderStyle="dashed">
                    Для данного проекта клапаны не найдены.
                </Text>
            )}

            <Button 
                colorScheme="teal" 
                size="lg" 
                mt={6} 
                isDisabled={totalSelected === 0}
                onClick={handleNext}
                rightIcon={<Icon as={FiArrowRight} />}
            >
                Далее (Выбрано: {totalSelected})
            </Button>
        </VStack>
    );
};

export default StockSelection;