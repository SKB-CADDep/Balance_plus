import { useEffect, useState } from 'react';
import { createFileRoute, useNavigate, useSearch } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import {
    Alert,
    AlertIcon,
    Box,
    Button,
    Container,
    Divider,
    Flex,
    FormControl,
    FormLabel,
    Heading,
    Select,
    SimpleGrid,
    Spinner,
    Text,
    VStack,
    Badge,
    useColorModeValue,
    useToast
} from '@chakra-ui/react';
import { CondensersService, type CalculationInput } from '../client';
import {
  CondenserForm,
  type CondenserFormValues,
  useCondenserCalculation,
} from '../components/CondenserCalculator';

export const Route = createFileRoute('/calculator')({
    component: CalculatorPage,
    validateSearch: (search: Record<string, unknown>) => ({
        condenserId: search.condenserId ? Number(search.condenserId) : undefined,
    }),
});

function CalculatorPage() {
    const searchParams = useSearch({ from: Route.fullPath });
    const navigate = useNavigate();
    const toast = useToast();

    const cardBg = useColorModeValue('white', 'gray.800');
    const cardBorder = useColorModeValue('gray.200', 'gray.700');

    const condenserId = searchParams.condenserId;

    const { data: condenser, isLoading: isCondenserLoading, isError: isCondenserError } = useQuery({
        queryKey: ['condenser', condenserId],
        queryFn: () => CondensersService.getCondenserApiV1CondensersCondenserIdGet({ condenserId: condenserId! }),
        enabled: !!condenserId,
    });

    const materials = condenser?.materials || [];

    const [materialId, setMaterialId] = useState<number | null>(null);
    const [serverErrors, setServerErrors] = useState<Record<string, string> | null>(null);

    // Default material when loaded
    useEffect(() => {
        if (materials.length > 0 && materialId === null) {
            setMaterialId(materials[0].id);
        }
    }, [materials, materialId]);

    const mutation = useCondenserCalculation();

    const handleCalculate = (values: CondenserFormValues) => {
        if (!condenserId) {
            toast({ title: "Ошибка", description: "Конденсатор не выбран.", status: "error" });
            return;
        }
        if (materialId === null) {
            toast({ title: "Ошибка", description: "Материал трубок не загружен.", status: "error" });
            return;
        }

        const payload: CalculationInput = {
          condenser_id: condenserId,
          material_id: materialId,
          method: values.method,
          G_steam: values.G_steam,
          W_main: values.W_main,
          t1_main: values.t1_main,
          G_steam_unit: values.G_steam_unit as any,
          W_main_unit: values.W_main_unit as any,
          t1_main_unit: values.t1_main_unit as any,
          H_steam_unit: values.H_steam_unit as any,
        };

        if (values.coefficient_b.trim()) payload.coefficient_b = values.coefficient_b;
        if (values.Z_main.trim()) payload.Z_main = Number(values.Z_main);

        if (values.method === 'berman') {
            if (values.W_builtin.trim()) payload.W_builtin = values.W_builtin;
            if (values.t1_builtin.trim()) payload.t1_builtin = values.t1_builtin;
            if (values.Z_builtin.trim()) payload.Z_builtin = Number(values.Z_builtin);
            if (values.H_steam.trim()) payload.H_steam = Number(values.H_steam);
            if (values.Z_ejectors.trim()) payload.Z_ejectors = Number(values.Z_ejectors);
        } else if (values.method === 'metro-vickers') {
            if (values.X_steam.trim()) payload.X_steam = Number(values.X_steam);
        }

        mutation.mutate(payload, {
          onSuccess: (data) => {
            setServerErrors(null);
            sessionStorage.setItem('lastCalculationResult', JSON.stringify(data));
            toast({ title: "Расчет выполнен успешно!", status: "success" });
            navigate({ to: '/results' });
          },
          onError: (err: any) => {
            setServerErrors(null);
            const detail = err?.response?.data?.detail ?? err?.body?.detail;
            
            // Если это 422 Unprocessable Entity (ошибки валидации)
            if (Array.isArray(detail)) {
              const fieldErrors: Record<string, string> = {};
              const generalErrors: string[] = [];
              
              detail.forEach((e: any) => {
                // Пытаемся привязать ошибку к полю
                // loc обычно имеет вид ["body", "G_steam"]
                if (Array.isArray(e.loc) && e.loc.length > 1 && e.loc[0] === 'body') {
                    const fieldName = e.loc.slice(1).join('.');
                    fieldErrors[fieldName] = e.msg;
                } else {
                    const field = Array.isArray(e.loc) ? e.loc.join(' → ') : String(e.loc ?? '');
                    generalErrors.push(field ? `[${field}]: ${e.msg}` : e.msg);
                }
              });
              
              if (Object.keys(fieldErrors).length > 0) {
                  setServerErrors(fieldErrors);
                  toast({ title: "Ошибка валидации", description: "Пожалуйста, проверьте подсвеченные поля формы.", status: "error", isClosable: true });
              }
              if (generalErrors.length > 0) {
                  toast({ title: "Ошибка входных данных", description: generalErrors.join('\n'), status: "error", isClosable: true, duration: 8000 });
              }
            } else {
                // Общая ошибка (например, 400 CalculationEngineError)
                let description = 'Неизвестная ошибка на сервере';
                if (typeof detail === 'string') {
                    description = detail;
                } else if (err?.body) {
                    description = typeof err.body === 'string' ? err.body : (err.body.message || err.body.error || JSON.stringify(err.body));
                } else if (err?.message) {
                    description = err.message;
                }
                toast({ title: "Ошибка расчета", description, status: "error", isClosable: true, duration: 8000 });
            }
          },
        });
    };

    if (!condenserId) {
        return (
            <Container maxW="container.xl" py={8}>
                <Alert status="warning">
                    <AlertIcon />
                    Конденсатор не выбран. Пожалуйста, вернитесь на главную страницу и выберите оборудование.
                </Alert>
                <Button mt={4} onClick={() => navigate({ to: '/' })}>На главную</Button>
            </Container>
        );
    }

    if (isCondenserLoading) {
        return <Flex justify="center" p={8}><Spinner size="xl" /></Flex>;
    }

    if (isCondenserError || !condenser) {
        return <Alert status="error"><AlertIcon />Ошибка загрузки данных конденсатора.</Alert>;
    }

    return (
        <Container maxW="container.xl" py={8}>
            <VStack spacing={8} align="stretch">
                <Box p={6} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
                    <Flex justify="space-between" align="center" mb={2}>
                        <Heading size="lg">Характеристики: {condenser.name_condenser}</Heading>
                        <Badge colorScheme="blue" fontSize="0.9em" p={1} borderRadius="md">Read-only</Badge>
                    </Flex>
                    {condenser.project_name && <Text color="gray.600" mb={4}>Проект: {condenser.project_name}</Text>}
                    
                    <Divider mb={4} />

                    <SimpleGrid columns={{ base: 1, md: 3, lg: 4 }} spacing={4}>
                        <Box><Text color="gray.500" fontSize="sm">Внутренний диаметр труб</Text><Text fontWeight="medium">{condenser.diameter_internal} мм</Text></Box>
                        <Box><Text color="gray.500" fontSize="sm">Толщина стенки труб</Text><Text fontWeight="medium">{condenser.wall_thickness} мм</Text></Box>
                        <Box><Text color="gray.500" fontSize="sm">Эжекторы</Text><Text fontWeight="medium">{condenser.ejectors_count} шт</Text></Box>
                        <Box><Text color="gray.500" fontSize="sm">Воздухоохладители</Text><Text fontWeight="medium">{condenser.aircooler_count ?? 0} шт</Text></Box>
                        
                        <Box><Text color="gray.500" fontSize="sm">Расход пара (ном)</Text><Text fontWeight="medium">{condenser.mass_flow_steam_nom} т/ч</Text></Box>
                        <Box><Text color="gray.500" fontSize="sm">Присосы воздуха</Text><Text fontWeight="medium">{condenser.mass_flow_air} кг/ч</Text></Box>
                    </SimpleGrid>

                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} mt={6}>
                        <Box p={4} bg={useColorModeValue('gray.50', 'gray.700')} borderRadius="md">
                            <Heading size="sm" mb={3} color="teal.500">Основной пучок</Heading>
                            <SimpleGrid columns={2} spacing={3}>
                                <Box><Text color="gray.500" fontSize="xs">Длина труб</Text><Text fontSize="sm">{condenser.main_length} мм</Text></Box>
                                <Box><Text color="gray.500" fontSize="xs">Количество труб</Text><Text fontSize="sm">{condenser.main_count} шт</Text></Box>
                                <Box><Text color="gray.500" fontSize="xs">Число ходов</Text><Text fontSize="sm">{condenser.passes_main}</Text></Box>
                            </SimpleGrid>
                        </Box>
                        
                        <Box p={4} bg={useColorModeValue('gray.50', 'gray.700')} borderRadius="md">
                            <Heading size="sm" mb={3} color="teal.500">Встроенный пучок</Heading>
                            {condenser.builtin_count ? (
                                <SimpleGrid columns={2} spacing={3}>
                                    <Box><Text color="gray.500" fontSize="xs">Длина труб</Text><Text fontSize="sm">{condenser.builtin_length} мм</Text></Box>
                                    <Box><Text color="gray.500" fontSize="xs">Количество труб</Text><Text fontSize="sm">{condenser.builtin_count} шт</Text></Box>
                                    <Box><Text color="gray.500" fontSize="xs">Число ходов</Text><Text fontSize="sm">{condenser.passes_builtin ?? '-'}</Text></Box>
                                </SimpleGrid>
                            ) : (
                                <Text color="gray.500" fontSize="sm">Отсутствует</Text>
                            )}
                        </Box>
                    </SimpleGrid>
                </Box>

                <Box p={6} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
                  <Heading size="md" mb={6}>
                    Калькулятор
                  </Heading>

                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} mb={6}>
                    <FormControl>
                      <FormLabel>Материал трубок</FormLabel>
                      <Select value={materialId ?? ''} onChange={(e) => setMaterialId(Number(e.target.value))}>
                        {materials?.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.name}
                          </option>
                        ))}
                      </Select>
                    </FormControl>
                  </SimpleGrid>

                  <Flex direction="column" gap={6}>
                    <Box w="full">
                      <CondenserForm onSubmit={handleCalculate} isSubmitting={mutation.isPending} serverErrors={serverErrors} />
                    </Box>
                  </Flex>
                </Box>
            </VStack>
        </Container>
    );
}

export default CalculatorPage;