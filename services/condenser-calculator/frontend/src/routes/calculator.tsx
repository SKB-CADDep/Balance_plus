import { useEffect, useState } from 'react';
import { createFileRoute, useNavigate, useSearch } from '@tanstack/react-router';
import { useQuery } from '@tanstack/react-query';
import {
    Alert,
    AlertIcon,
    Box,
    Button,
    Container,
    Flex,
    FormControl,
    FormLabel,
    Heading,
    Select,
    SimpleGrid,
    Spinner,
    Text,
    VStack,
    useColorModeValue,
    useToast
} from '@chakra-ui/react';
import { CondensersService, MaterialsService, type CalculationInput } from '../client';
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

    const { data: materials, isLoading: isMaterialsLoading } = useQuery({
        queryKey: ['materials'],
        queryFn: () => MaterialsService.listMaterialsApiV1MaterialsGet(),
    });

    const [materialId, setMaterialId] = useState<number | null>(null);

    // Default material when loaded
    useEffect(() => {
        if (materials && materials.length > 0 && materialId === null) {
            setMaterialId(materials[0].id);
        }
    }, [materials]);

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

        const parseNumber = (val: string) => {
            if (!val.trim()) return undefined;
            const parsed = Number(val.replace(',', '.'));
            return isNaN(parsed) ? undefined : parsed;
        };

        if (values.coefficient_b.trim()) payload.coefficient_b = values.coefficient_b;
        if (values.Z_main.trim()) payload.Z_main = parseNumber(values.Z_main);

        if (values.method === 'berman') {
            if (values.W_builtin.trim()) payload.W_builtin = values.W_builtin;
            if (values.t1_builtin.trim()) payload.t1_builtin = values.t1_builtin;
            if (values.Z_builtin.trim()) payload.Z_builtin = parseNumber(values.Z_builtin);
            if (values.H_steam.trim()) payload.H_steam = parseNumber(values.H_steam) ?? null;
            if (values.Z_ejectors.trim()) payload.Z_ejectors = parseNumber(values.Z_ejectors);
        } else if (values.method === 'metro-vickers') {
            if (values.X_steam.trim()) payload.X_steam = parseNumber(values.X_steam);
        }

        mutation.mutate(payload, {
          onSuccess: (data) => {
            sessionStorage.setItem('lastCalculationResult', JSON.stringify(data));
            toast({ title: "Расчет выполнен успешно!", status: "success" });
            navigate({ to: '/results' });
          },
          onError: (err: any) => {
            const detail = err?.response?.data?.detail ?? err?.body?.detail;
            let description: string;
            if (Array.isArray(detail)) {
              description = detail
                .map((e: any) => {
                  const field = Array.isArray(e.loc) ? e.loc.join(' → ') : String(e.loc ?? '');
                  return field ? `[${field}]: ${e.msg}` : e.msg;
                })
                .join('\n');
            } else if (typeof detail === 'string') {
              description = detail;
            } else if (err?.body) {
              if (typeof err.body === 'string') {
                description = err.body;
              } else {
                description = err.body.message || err.body.error || JSON.stringify(err.body);
              }
            } else {
              description = err?.message ?? 'Неизвестная ошибка на сервере';
            }
            toast({ title: "Ошибка расчета", description, status: "error", isClosable: true, duration: 8000 });
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

    if (isCondenserLoading || isMaterialsLoading) {
        return <Flex justify="center" p={8}><Spinner size="xl" /></Flex>;
    }

    if (isCondenserError || !condenser) {
        return <Alert status="error"><AlertIcon />Ошибка загрузки данных конденсатора.</Alert>;
    }

    return (
        <Container maxW="container.xl" py={8}>
            <VStack spacing={8} align="stretch">
                <Box p={6} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
                    <Heading size="lg" mb={2}>Характеристики: {condenser.name_condenser}</Heading>
                    {condenser.project_name && <Text color="gray.600">Проект: {condenser.project_name}</Text>}
                    <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4} mt={4}>
                        <Box>Ходы (осн): {condenser.passes_main}</Box>
                        <Box>Эжекторы: {condenser.ejectors_count}</Box>
                        <Box>Ном. пар: {condenser.mass_flow_steam_nom} т/ч</Box>
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
                      <CondenserForm onSubmit={handleCalculate} isSubmitting={mutation.isPending} />
                    </Box>
                  </Flex>
                </Box>
            </VStack>
        </Container>
    );
}

export default CalculatorPage;
