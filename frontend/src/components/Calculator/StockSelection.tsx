import React from 'react';
import {useQuery} from '@tanstack/react-query';
import {
    Box,
    Button,
    Flex,
    Heading, Icon,
    List,
    ListItem,
    Spinner,
    Tag,
    Text,
    useColorModeValue,
    VStack,
} from '@chakra-ui/react';

import {
    type TurbineInfo,
    TurbinesService,
    type TurbineValves as ClientTurbineValvesResponse,
    type ValveInfo_Output as ClientValveInfo
} from '../../client';
import {FiChevronLeft} from "react-icons/fi";

type Valve = ClientValveInfo;

type Props = {
    turbine: TurbineInfo | null;
    onSelectValve: (valve: Valve) => void;
    onGoBack?: () => void;
};

const fetchValvesForTurbineAPI = async (turbineName: string) => {
    if (!turbineName) {
        return {count: 0, valves: []};
    }
    return TurbinesService.turbinesGetValvesByTurbineEndpoint({turbineName});
};

const StockSelection: React.FC<Props> = ({turbine, onSelectValve, onGoBack}) => {
    const turbineName = turbine?.name || '';

    const {
        data: turbineValvesResponse,
        isLoading,
        isError,
        error,
    } = useQuery<ClientTurbineValvesResponse, Error>({
        queryKey: ['valvesForTurbine', turbineName],
        queryFn: () => fetchValvesForTurbineAPI(turbineName),
        enabled: !!turbineName,
    });

    const listItemHoverBg = useColorModeValue('teal.50', 'gray.700');
    const listItemHoverBorderColor = useColorModeValue('teal.300', 'teal.500');

    const valves = turbineValvesResponse?.valves || [];

    if (!turbine) {
        return (
            <VStack spacing={4} p={5} align="center" justify="center" minH="200px">
                <Text>Турбина не выбрана.</Text>
                {onGoBack && <Button onClick={onGoBack} colorScheme="teal">Вернуться к выбору турбины</Button>}
            </VStack>
        );
    }

    if (isLoading) {
        return (
            <VStack spacing={4} align="center" justify="center" minH="200px">
                <Spinner size="xl" color="teal.500"/>
                <Text>Загрузка клапанов для турбины {turbine.name}...</Text>
            </VStack>
        );
    }

    if (isError) {
        return (
            <VStack spacing={4} align="center" justify="center" minH="200px" color="red.500">
                <Heading as="h3" size="md">Ошибка при загрузке клапанов:</Heading>
                <Text>{error?.message || 'Произошла неизвестная ошибка'}</Text>
                {onGoBack &&
                    <Button onClick={onGoBack} colorScheme="teal" variant="outline">Вернуться к выбору турбины</Button>}
            </VStack>
        );
    }

    return (
        <VStack spacing={6} p={5} align="stretch" w="100%" maxW="container.md" mx="auto">
            <Heading as="h2" size="lg" textAlign="center">
                Выбранная турбина: <Text as="span" color="teal.500">{turbine.name}</Text>
            </Heading>

            {onGoBack && (
                <Box width="100%" textAlign="center" mb={2}>
                    <Button
                        onClick={onGoBack}
                        variant="outline"
                        colorScheme="teal"
                        size="sm"
                        leftIcon={<Icon as={FiChevronLeft}/>}
                    >
                        Изменить турбину
                    </Button>
                </Box>
            )}

            <Heading as="h3" size="md" textAlign="center" mt={4}>
                Выберите клапан для расчёта
            </Heading>

            {valves.length > 0 ? (
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
                            transition="background-color 0.2s, box-shadow 0.2s, border-color 0.2s"
                        >
                            <Flex justify="space-between" align="center">
                                <Text fontSize="lg" fontWeight="medium">{valve.name}</Text>
                                {valve.type && <Tag size="sm" colorScheme="cyan">{valve.type}</Tag>}
                            </Flex>
                        </ListItem>
                    ))}
                </List>
            ) : (
                <Text textAlign="center" color="gray.500" p={4} borderWidth="1px" borderRadius="md"
                      borderStyle="dashed">
                    Для данной турбины клапаны не найдены.
                </Text>
            )}
        </VStack>
    );
};

export default StockSelection;