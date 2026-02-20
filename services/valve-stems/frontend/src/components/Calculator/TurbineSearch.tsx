import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    Box,
    Button,
    Card,
    CardBody,
    Collapse,
    Flex,
    FormControl,
    FormLabel,
    Heading,
    Icon,
    Input,
    List,
    ListItem,
    Spinner,
    Stack,
    Tag,
    Text,
    useColorModeValue,
    VStack,
    Wrap,
    WrapItem,
    InputGroup,
    InputRightElement,
    IconButton
} from '@chakra-ui/react';
import { FiSearch, FiChevronRight, FiFilter, FiX } from 'react-icons/fi';
import { useDebounce } from 'use-debounce'; // Рекомендую установить: npm i use-debounce

import {
    type SimpleValveInfo,
    TurbinesService,
    type TurbineWithValvesInfo,
} from '../../client';

// Расширяем тип, так как мы добавили поля в бэкенд, но клиент мог еще не обновиться
interface ExtendedTurbine extends TurbineWithValvesInfo {
    station_name?: string;
    station_number?: string;
    factory_number?: string;
    matched_valve_id?: number;
}

type Props = {
    onSelectTurbine: (turbine: ExtendedTurbine, autoSelectValveId?: number) => void;
};

// Функция API вызова с фильтрами
const searchTurbinesAPI = async (filters: {
    q: string;
    station: string;
    factory: string;
    valve: string;
}): Promise<ExtendedTurbine[]> => {
    // В реальном коде вам нужно обновить `client/services.ts`, 
    // но пока можно использовать прямой fetch или axios, если авто-генератор еще не запущен
    // Ниже пример через сгенерированный сервис (предполагая, что вы обновили OpenAPI)
    
    // Если вы еще не обновили клиент, придется формировать URL вручную:
    const params = new URLSearchParams();
    if (filters.q) params.append('q', filters.q);
    if (filters.station) params.append('station', filters.station);
    if (filters.factory) params.append('factory', filters.factory);
    if (filters.valve) params.append('valve', filters.valve);

    const response = await fetch(`/api/v1/turbines/search?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` } 
    });
    if (!response.ok) throw new Error('Network response was not ok');
    return response.json();
};

const TurbineSearch: React.FC<Props> = ({ onSelectTurbine }) => {
    // Состояние фильтров
    const [filters, setFilters] = useState({
        q: '',        // Марка турбины
        station: '',  // Станция
        factory: '',  // Зав №
        valve: ''     // Чертеж
    });

    // Дебаунс для предотвращения запросов при каждом нажатии клавиши
    const [debouncedFilters] = useDebounce(filters, 500);

    const {
        data: turbines,
        isLoading,
        isError,
    } = useQuery<ExtendedTurbine[], Error>({
        queryKey: ['turbinesSearch', debouncedFilters],
        queryFn: () => searchTurbinesAPI(debouncedFilters),
        // Не делать запрос, если все поля пустые
        enabled: Object.values(debouncedFilters).some(v => v.length > 0),
    });

    const handleInputChange = (field: keyof typeof filters, value: string) => {
        setFilters(prev => ({ ...prev, [field]: value }));
    };

    const clearFilters = () => {
        setFilters({ q: '', station: '', factory: '', valve: '' });
    };

    // Авто-выбор, если поиск по клапану дал точное совпадение
    useEffect(() => {
        if (filters.valve && turbines && turbines.length === 1) {
            // Если найден ровно 1 проект с таким клапаном -> можно подсветить или предложить авто-переход
            // Но лучше оставить явный клик пользователю, чтобы он убедился, что это та станция
        }
    }, [turbines, filters.valve]);

    // Стили
    const cardBg = useColorModeValue('white', 'gray.750');
    const borderColor = useColorModeValue('gray.200', 'gray.600');
    const hoverBg = useColorModeValue('teal.50', 'gray.700');

    return (
        <VStack spacing={6} p={2} align="stretch" w="100%" maxW="container.lg" mx="auto">
            <Heading as="h2" size="lg" textAlign="center" mb={2}>
                Поиск проекта
            </Heading>

            {/* Панель фильтров */}
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

            {/* Результаты */}
            <Box minH="300px">
                {isLoading && (
                    <Flex justify="center" p={10}>
                        <Spinner size="xl" color="teal.500" />
                    </Flex>
                )}

                {!isLoading && turbines && turbines.length === 0 && (
                    <Text textAlign="center" color="gray.500" mt={10}>
                        Проекты не найдены. Попробуйте изменить критерии поиска.
                    </Text>
                )}

                {!isLoading && !turbines && (
                    <Text textAlign="center" color="gray.400" mt={10}>
                        Введите параметры для поиска
                    </Text>
                )}

                <List spacing={3}>
                    {turbines?.map((turbine) => (
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
                                    
                                    {/* Отображение клапанов */}
                                    {turbine.valves && turbine.valves.length > 0 && (
                                        <Wrap mt={2} spacing={2}>
                                            {turbine.valves.slice(0, 5).map(v => (
                                                <WrapItem key={v.id}>
                                                    <Tag 
                                                        size="sm" 
                                                        // Подсвечиваем клапан, если искали именно его
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
            </Box>
        </VStack>
    );
};

export default TurbineSearch;