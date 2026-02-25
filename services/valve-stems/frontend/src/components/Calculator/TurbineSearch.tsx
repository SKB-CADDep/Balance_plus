import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    Box, Button, Card, CardBody, Flex, FormControl, FormLabel,
    Heading, Icon, Input, List, ListItem, Spinner, Stack, Tag, Text,
    useColorModeValue, VStack, Wrap, WrapItem, InputGroup, InputRightElement
} from '@chakra-ui/react';
import { FiSearch, FiChevronRight, FiX } from 'react-icons/fi';

import { type TurbineWithValvesInfo } from '../../client';
import { request as __request } from '../../client/core/request';
import { OpenAPI } from '../../client/core/OpenAPI';

function useDebounce<T>(value: T, delay: number): [T] {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);
        return () => clearTimeout(handler);
    }, [value, delay]);
    return [debouncedValue];
}

interface ExtendedTurbine extends TurbineWithValvesInfo {
    station_name?: string;
    station_number?: string;
    factory_number?: string;
    matched_valve_id?: number;
}

type Props = {
    onSelectTurbine: (turbine: ExtendedTurbine, autoSelectValveId?: number) => void;
};

// ИСПОЛЬЗУЕМ ВНУТРЕННИЙ КЛИЕНТ ПРИЛОЖЕНИЯ (ОБХОДИТ ВСЕ ПРОБЛЕМЫ С CORS!)
const searchTurbinesAPI = async (filters: {
    q: string;
    station: string;
    factory: string;
    valve: string;
}): Promise<ExtendedTurbine[]> => {
    const queryParams: Record<string, string> = {};
    if (filters.q) queryParams.q = filters.q;
    if (filters.station) queryParams.station = filters.station;
    if (filters.factory) queryParams.factory = filters.factory;
    if (filters.valve) queryParams.valve = filters.valve;

    try {
        const result = await __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/turbines/search',
            query: queryParams
        });
        return result as ExtendedTurbine[];
    } catch (err: any) {
        throw new Error(err?.body?.detail || err.message || 'Ошибка сервера');
    }
};

const TurbineSearch: React.FC<Props> = ({ onSelectTurbine }) => {
    const [filters, setFilters] = useState({
        q: '', station: '', factory: '', valve: ''
    });

    const [debouncedFilters] = useDebounce(filters, 500);

    const hasFilters = Object.values(debouncedFilters).some((v) => String(v).trim().length > 0);

    const {
        data: turbines,
        isLoading,
        isError,
        error
    } = useQuery<ExtendedTurbine[], Error>({
        queryKey: ['turbinesSearch', debouncedFilters],
        queryFn: () => searchTurbinesAPI(debouncedFilters),
        enabled: hasFilters,
        retry: false
    });

    const handleInputChange = (field: keyof typeof filters, value: string) => {
        setFilters(prev => ({ ...prev, [field]: value }));
    };

    const clearFilters = () => {
        setFilters({ q: '', station: '', factory: '', valve: '' });
    };

    const cardBg = useColorModeValue('white', 'gray.750');
    const borderColor = useColorModeValue('gray.200', 'gray.600');
    const hoverBg = useColorModeValue('teal.50', 'gray.700');

    return (
        <VStack spacing={6} p={2} align="stretch" w="100%" maxW="container.lg" mx="auto">
            <Heading as="h2" size="lg" textAlign="center" mb={2}>
                Поиск проекта
            </Heading>

            <Card variant="outline" bg={cardBg} shadow="sm">
                <CardBody>
                    <Stack spacing={4}>
                        <Flex gap={4} direction={{ base: 'column', md: 'row' }}>
                            <FormControl>
                                <FormLabel fontSize="sm" color="gray.500">Марка турбины</FormLabel>
                                <Input 
                                    placeholder="Например, Т-110" 
                                    value={filters.q}
                                    onChange={(e) => handleInputChange('q', e.target.value)}
                                />
                            </FormControl>
                            <FormControl>
                                <FormLabel fontSize="sm" color="gray.500">Название станции</FormLabel>
                                <Input 
                                    placeholder="Например, Абаканская" 
                                    value={filters.station}
                                    onChange={(e) => handleInputChange('station', e.target.value)}
                                />
                            </FormControl>
                        </Flex>
                        
                        <Flex gap={4} direction={{ base: 'column', md: 'row' }}>
                            <FormControl>
                                <FormLabel fontSize="sm" color="gray.500">Заводской номер</FormLabel>
                                <Input 
                                    placeholder="№" 
                                    value={filters.factory}
                                    onChange={(e) => handleInputChange('factory', e.target.value)}
                                />
                            </FormControl>
                            <FormControl>
                                <FormLabel fontSize="sm" color="teal.500" fontWeight="bold">Чертеж клапана</FormLabel>
                                <InputGroup>
                                    <Input 
                                        placeholder="УТЗ-304414" 
                                        value={filters.valve}
                                        borderColor={filters.valve ? "teal.400" : "inherit"}
                                        borderWidth={filters.valve ? "2px" : "1px"}
                                        onChange={(e) => handleInputChange('valve', e.target.value)}
                                    />
                                    {filters.valve && (
                                        <InputRightElement>
                                            <Icon as={FiSearch} color="teal.500" />
                                        </InputRightElement>
                                    )}
                                </InputGroup>
                            </FormControl>
                        </Flex>

                        <Flex justify="flex-end">
                            <Button size="sm" variant="ghost" onClick={clearFilters} leftIcon={<FiX />}>
                                Очистить
                            </Button>
                        </Flex>
                    </Stack>
                </CardBody>
            </Card>

            <Box minH="300px">
                {/* 1. Идет загрузка */}
                {isLoading && hasFilters && (
                    <Flex justify="center" p={10}>
                        <Spinner size="xl" color="teal.500" />
                    </Flex>
                )}

                {/* 2. Стартовый экран */}
                {!hasFilters && (
                    <Text textAlign="center" color="gray.400" mt={10}>
                        Введите параметры для поиска
                    </Text>
                )}

                {/* 3. Ошибка */}
                {isError && (
                    <Box textAlign="center" mt={10} p={4} borderWidth="1px" borderColor="red.300" borderRadius="md" bg="red.50">
                        <Text color="red.600" fontWeight="bold" fontSize="lg">Произошла ошибка при поиске!</Text>
                        <Text color="red.500" mt={2}>{error?.message}</Text>
                    </Box>
                )}

                {/* 4. Ничего не найдено */}
                {!isLoading && !isError && hasFilters && turbines && turbines.length === 0 && (
                    <Text textAlign="center" color="gray.500" mt={10}>
                        Проекты не найдены. Попробуйте изменить критерии поиска.
                    </Text>
                )}

                {/* 5. Успешно нашли данные! */}
                {!isLoading && !isError && turbines && turbines.length > 0 && (
                    <List spacing={3}>
                        {turbines.map((turbine) => (
                            <ListItem
                                key={turbine.id}
                                onClick={() => onSelectTurbine(turbine)}
                                p={4}
                                borderWidth="1px"
                                borderRadius="lg"
                                borderColor={borderColor}
                                bg={cardBg}
                                _hover={{
                                    bg: hoverBg,
                                    cursor: 'pointer',
                                    borderColor: 'teal.300',
                                    transform: 'translateY(-2px)',
                                    shadow: 'md'
                                }}
                                transition="all 0.2s"
                            >
                                <Flex justify="space-between" align="center">
                                    <VStack align="start" spacing={1}>
                                        <Flex align="center" gap={2}>
                                            <Heading size="md" color="teal.600">{turbine.name}</Heading>
                                            {turbine.factory_number && (
                                                <Tag size="sm" colorScheme="gray">Зав.№ {turbine.factory_number}</Tag>
                                            )}
                                        </Flex>
                                        <Text fontSize="md" fontWeight="medium">
                                            {turbine.station_name} {turbine.station_number ? `(Ст. №${turbine.station_number})` : ''}
                                        </Text>
                                        
                                        {turbine.valves && turbine.valves.length > 0 && (
                                            <Wrap mt={2} spacing={2}>
                                                {turbine.valves.slice(0, 5).map(v => (
                                                    <WrapItem key={v.id}>
                                                        <Tag 
                                                            size="sm" 
                                                            colorScheme={filters.valve && v.name.toLowerCase().includes(filters.valve.toLowerCase()) ? "orange" : "cyan"}
                                                            variant="subtle"
                                                        >
                                                            {v.name}
                                                        </Tag>
                                                    </WrapItem>
                                                ))}
                                                {turbine.valves.length > 5 && <Tag size="sm">+{turbine.valves.length - 5}</Tag>}
                                            </Wrap>
                                        )}
                                    </VStack>
                                    <Icon as={FiChevronRight} color="gray.400" boxSize={6} />
                                </Flex>
                            </ListItem>
                        ))}
                    </List>
                )}
            </Box>
        </VStack>
    );
};

export default TurbineSearch;