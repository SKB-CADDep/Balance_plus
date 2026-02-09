import React, {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {
    Box,
    Flex,
    Heading,
    HStack,
    Icon,
    Input,
    InputGroup,
    List,
    ListItem,
    Spinner,
    Tag,
    Text,
    useColorModeValue,
    VStack,
    Wrap,
    WrapItem,
} from '@chakra-ui/react';

import {
    type SimpleValveInfo,
    TurbinesService,
    type TurbineWithValvesInfo as ClientTurbineWithValves
} from '../../client';
import {FiChevronRight} from 'react-icons/fi';

type Turbine = ClientTurbineWithValves;

type Props = {
    onSelectTurbine: (turbine: Turbine) => void;
};

const fetchTurbinesAPI = async (): Promise<Turbine[]> => {
    return TurbinesService.turbinesGetAllTurbinesWithValves();
};

const TurbineSearch: React.FC<Props> = ({onSelectTurbine}) => {
    const [searchTerm, setSearchTerm] = useState('');

    const {
        data: turbines,
        isLoading,
        isError,
        error,
    } = useQuery<Turbine[], Error>({
        queryKey: ['turbinesWithValves'],
        queryFn: fetchTurbinesAPI,
    });

    const listItemBg = useColorModeValue("white", "gray.750");
    const listItemHoverBg = useColorModeValue('gray.100', 'gray.700');
    const listItemBorderColor = useColorModeValue("gray.200", "gray.600");
    const listItemHoverBorderColor = useColorModeValue("teal.300", "teal.500");
    const valveTagColorScheme = useColorModeValue("gray", "gray");
    const iconColor = useColorModeValue("gray.400", "gray.500");

    const filteredTurbines = turbines?.filter(turbine =>
        turbine.name.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    if (isLoading) {
        return (
            <VStack spacing={4} align="center" justify="center" minH="200px">
                <Spinner size="xl" color="teal.500"/>
                <Text>Загрузка турбин...</Text>
            </VStack>
        );
    }

    if (isError) {
        return (
            <VStack spacing={4} align="center" justify="center" minH="200px" color="red.500">
                <Text fontSize="lg" fontWeight="bold">Ошибка при загрузке данных:</Text>
                <Text>{error?.message || 'Произошла неизвестная ошибка'}</Text>
            </VStack>
        );
    }

    return (
        <VStack spacing={6} p={5} align="stretch" w="100%" maxW="container.lg" mx="auto">
            <Heading as="h2" size="xl" textAlign="center" mb={2}>
                Введите название турбины
            </Heading>

            <Box>
                <InputGroup size="lg">
                    <Input
                        type="text"
                        placeholder="Например, A-100"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        focusBorderColor="teal.500"
                        variant="filled"
                    />
                </InputGroup>
            </Box>

            {turbines && turbines.length > 0 ? (
                <List spacing={3} w="100%">
                    {filteredTurbines.map((turbine) => (
                        <ListItem
                            key={turbine.id}
                            onClick={() => onSelectTurbine(turbine)}
                            p={4}
                            borderWidth="1px"
                            borderRadius="lg"
                            borderColor={listItemBorderColor}
                            bg={listItemBg}
                            boxShadow="base"
                            _hover={{
                                bg: listItemHoverBg,
                                cursor: 'pointer',
                                shadow: 'md',
                                borderColor: listItemHoverBorderColor,
                            }}
                            transition="all 0.2s ease-in-out"
                        >
                            <Flex justify="space-between" align="center" w="full">
                                <Text
                                    fontSize="lg"
                                    fontWeight="medium"
                                    noOfLines={1}
                                    title={turbine.name}
                                    flexShrink={1}
                                    overflow="hidden"
                                    mr={3}
                                >
                                    {turbine.name}
                                </Text>

                                <HStack spacing={2} align="center"
                                        flexShrink={0}>
                                    {turbine.valves && turbine.valves.length > 0 && (
                                        <Wrap
                                            spacing={1}
                                            justify="flex-end"
                                            maxW="400px"
                                            overflow="hidden"
                                            whiteSpace="nowrap"
                                        >
                                            {turbine.valves.slice(0, 4).map((valve: SimpleValveInfo) => (
                                                <WrapItem key={valve.id}>
                                                    <Tag size="sm" variant="subtle" colorScheme={valveTagColorScheme}>
                                                        {valve.name}
                                                    </Tag>
                                                </WrapItem>
                                            ))}
                                            {turbine.valves.length > 4 && (
                                                <WrapItem>
                                                    <Tag size="sm" variant="outline" colorScheme="gray">...</Tag>
                                                </WrapItem>
                                            )}
                                        </Wrap>
                                    )}
                                    {(!turbine.valves || turbine.valves.length === 0) && (
                                        <Box w="auto"/>
                                    )}

                                    <Icon as={FiChevronRight} boxSize={5} color={iconColor}/>
                                </HStack>
                            </Flex>
                        </ListItem>
                    ))}
                    {filteredTurbines.length === 0 && searchTerm && (
                        <ListItem textAlign="center" color="gray.500" p={4}>
                            Турбины не найдены по вашему запросу.
                        </ListItem>
                    )}
                </List>
            ) : (
                <Text textAlign="center" color="gray.500" p={4}>
                    Нет доступных турбин.
                </Text>
            )}
        </VStack>
    );
};

export default TurbineSearch;