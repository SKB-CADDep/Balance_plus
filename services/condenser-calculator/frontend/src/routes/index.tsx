import {
    Container,
    Heading,
    Input,
    InputGroup,
    InputLeftElement,
    VStack,
    Box,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Button,
    useColorModeValue,
    Text,
    Spinner,
    Flex,
    Icon,
} from "@chakra-ui/react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { FiSearch, FiArrowRight } from "react-icons/fi";
import { useState } from "react";
import { CondensersService } from "../client";

function SearchPage() {
    const [search, setSearch] = useState("");
    const navigate = useNavigate();

    const { data: condensers, isLoading, isError } = useQuery({
        queryKey: ["condensers", search],
        queryFn: () => CondensersService.listCondensersApiV1CondensersGet({ search: search || undefined }),
    });

    const cardBg = useColorModeValue("white", "gray.800");
    const borderColor = useColorModeValue("gray.200", "gray.700");
    const hoverBg = useColorModeValue("gray.50", "gray.700");

    return (
        <Container maxW="container.xl" py={8}>
            <VStack spacing={6} align="stretch">
                <Box>
                    <Heading as="h1" size="xl" mb={2}>Поиск оборудования</Heading>
                    <Text color="gray.500">Найдите конденсатор по марке или проекту для начала расчета</Text>
                </Box>

                <Box bg={cardBg} p={6} borderRadius="lg" borderWidth="1px" borderColor={borderColor} boxShadow="sm">
                    <InputGroup size="lg" mb={6}>
                        <InputLeftElement pointerEvents="none">
                            <Icon as={FiSearch} color="gray.400" />
                        </InputLeftElement>
                        <Input
                            placeholder="Поиск по наименованию или проекту..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </InputGroup>

                    {isLoading ? (
                        <Flex justify="center" p={8}>
                            <Spinner size="xl" color="teal.500" />
                        </Flex>
                    ) : isError ? (
                        <Text color="red.500">Ошибка при загрузке данных</Text>
                    ) : condensers && condensers.length > 0 ? (
                        <Box overflowX="auto">
                            <Table variant="simple">
                                <Thead>
                                    <Tr>
                                        <Th>ID</Th>
                                        <Th>Маркировка</Th>
                                        <Th>Проект</Th>
                                        <Th textAlign="right">Действие</Th>
                                    </Tr>
                                </Thead>
                                <Tbody>
                                    {condensers.map((condenser) => (
                                        <Tr key={condenser.id} _hover={{ bg: hoverBg }}>
                                            <Td>{condenser.id}</Td>
                                            <Td fontWeight="medium">{condenser.name_condenser}</Td>
                                            <Td>{condenser.project_name}</Td>
                                            <Td textAlign="right">
                                                <Button
                                                    size="sm"
                                                    colorScheme="teal"
                                                    rightIcon={<FiArrowRight />}
                                                    onClick={() => navigate({ to: "/calculator", search: { condenserId: condenser.id } })}
                                                >
                                                    Выбрать
                                                </Button>
                                            </Td>
                                        </Tr>
                                    ))}
                                </Tbody>
                            </Table>
                        </Box>
                    ) : (
                        <Flex justify="center" p={8}>
                            <Text color="gray.500">Оборудование не найдено</Text>
                        </Flex>
                    )}
                </Box>
            </VStack>
        </Container>
    );
}

export const Route = createFileRoute('/')({
    component: SearchPage,
});