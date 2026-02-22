import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    Box,
    Button,
    Flex,
    Heading,
    Icon,
    List,
    ListItem,
    Spinner,
    Tag,
    Text,
    useColorModeValue,
    VStack,
} from '@chakra-ui/react';
import { FiChevronLeft } from "react-icons/fi";

import {
    type TurbineInfo,
    TurbinesService,
    type TurbineValves as ClientTurbineValvesResponse,
    type ValveInfo_Output as ClientValveInfo
} from '../../client';

type Valve = ClientValveInfo;

type Props = {
    // Временно расширяем тип для новых полей, пока клиент OpenAPI не обновлен
    turbine: (TurbineInfo & { station_name?: string; station_number?: string; factory_number?: string }) | null;
    onSelectValve: (valve: Valve) => void;
    onGoBack?: () => void;
};

const fetchValvesForTurbineAPI = async (turbineId: number) => {
    if (!turbineId) {
        return { count: 0, valves: [] };
    }
    // ВНИМАНИЕ: Если вы перегенерируете OpenAPI клиент, ключ здесь изменится с turbineName на turbineId
    // Пока оставляем как в старом клиенте, но передаем строковое значение ID
    return TurbinesService.turbinesGetValvesByTurbineEndpoint({ turbineName: turbineId.toString() as any });
};

const StockSelection: React.FC<Props> = ({ turbine, onSelectValve, onGoBack }) => {
    // Используем ID вместо имени для уникальности
    const turbineId = turbine?.id;

    const {
        data: turbineValvesResponse,
        isLoading,
        isError,
        error,
    } = useQuery<ClientTurbineValvesResponse, Error>({
        queryKey: ['valvesForTurbine', turbineId],
        queryFn: () => fetchValvesForTurbineAPI(turbineId!),
        enabled: !!turbineId,
    });

    const listItemHoverBg = useColorModeValue('teal.50', 'gray.700');
    const listItemHoverBorderColor = useColorModeValue('teal.300', 'teal.500');

    const valves = turbineValvesResponse?.valves || [];

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
                    <Button
                        onClick={onGoBack}
                        variant="outline"
                        colorScheme="teal"
                        size="sm"
                        leftIcon={<Icon as={FiChevronLeft} />}
                    >
                        Изменить проект
                    </Button>
                </Box>
            )}

            <Heading as="h3" size="md" textAlign="center" mt={4}>
                Выберите клапан для расчёта
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
                            onClick={() => onSelectValve(valve)}
                            p={4}
                            borderWidth="1px"
                            borderRadius="lg"
                            _hover={{
                                bg: listItemHoverBg,
                                cursor: 'pointer',
                                shadow: 'md',
                                borderColor: listItemHoverBorderColor,
                            }}
                            transition="all 0.2s"
                        >
                            <Flex justify="space-between" align="center">
                                <Text fontSize="lg" fontWeight="medium">{valve.name}</Text>
                                {valve.type && <Tag size="sm" colorScheme="cyan">{valve.type}</Tag>}
                            </Flex>
                        </ListItem>
                    ))}
                </List>
            ) : (
                <Text textAlign="center" color="gray.500" p={4} borderWidth="1px" borderRadius="md" borderStyle="dashed">
                    Для данного проекта клапаны не найдены.
                </Text>
            )}
        </VStack>
    );
};

export default StockSelection;