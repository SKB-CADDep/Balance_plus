import { useEffect, useMemo, useState } from 'react';
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
import { CondensersService, MaterialsService } from '../client';
import {
  CondenserForm,
  type CondenserCalculationResponse,
  type CondenserFormValues,
  type CondenserMatrixResult,
  ResultMatrixViewer,
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

    const [results, setResults] = useState<Array<CondenserMatrixResult>>([]);

    // Default material when loaded
    useEffect(() => {
        if (materials && materials.length > 0 && materialId === null) {
            setMaterialId(materials[0].id);
        }
    }, [materials]);

    const mutation = useCondenserCalculation();

    const normalizedResults = useMemo(() => results, [results]);

    const handleCalculate = (values: CondenserFormValues) => {
        if (!condenserId) {
            toast({ title: "Ошибка", description: "Конденсатор не выбран.", status: "error" });
            return;
        }
        if (materialId === null) {
            toast({ title: "Ошибка", description: "Материал трубок не загружен.", status: "error" });
            return;
        }

        mutation.mutate(
          {
            ...values,
            condenser_id: String(condenserId),
            material_id: String(materialId),
          },
          {
            onSuccess: (data: CondenserCalculationResponse) => {
              const arr = Array.isArray(data) ? data : data.results;
              setResults(arr ?? []);
              toast({ title: "Расчет выполнен успешно!", status: "success" });
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
              } else {
                description = err?.message ?? 'Неизвестная ошибка';
              }
              toast({ title: "Ошибка расчета", description, status: "error", isClosable: true, duration: 8000 });
            },
          },
        );
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

                  <Flex direction={{ base: 'column', lg: 'row' }} gap={6} align="flex-start">
                    <Box flex="1" minW={0}>
                      <CondenserForm onSubmit={handleCalculate} isSubmitting={mutation.isPending} />
                    </Box>
                    <Box flex="1" minW={0}>
                      <ResultMatrixViewer results={normalizedResults} />
                    </Box>
                  </Flex>
                </Box>
            </VStack>
        </Container>
    );
}

export default CalculatorPage;