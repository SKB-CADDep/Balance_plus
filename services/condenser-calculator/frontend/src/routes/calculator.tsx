import { useState, useEffect, useRef } from 'react';
import { createFileRoute, useNavigate, useSearch } from '@tanstack/react-router';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
    Box, Container, Heading, Text, VStack, Spinner, Flex, Alert, AlertIcon,
    RadioGroup, Radio, Stack, SimpleGrid, FormControl, FormLabel, Input,
    FormHelperText, Button, useToast, Tabs, TabList, TabPanels, Tab, TabPanel,
    Table, Thead, Tbody, Tr, Th, Td, Select, Divider, useColorModeValue
} from '@chakra-ui/react';
import { CondensersService, CalculationsService, MaterialsService, type CalculationInput, type CalculationOutput } from '../client';
import { parseRange } from '../utils/parser';

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
    const headingColor = useColorModeValue('teal.600', 'teal.300');
    const warningBg = useColorModeValue('yellow.50', 'yellow.900');

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

    const [method, setMethod] = useState<'berman' | 'metro-vickers'>('berman');
    const [materialId, setMaterialId] = useState<number | null>(null);

    const [coefficientB, setCoefficientB] = useState('1');
    const [gSteam, setGSteam] = useState('');
    const [wMain, setWMain] = useState('');
    const [wBuiltin, setWBuiltin] = useState('');
    const [t1Main, setT1Main] = useState('');
    const [t1Builtin, setT1Builtin] = useState('');
    const [zEjectors, setZEjectors] = useState('1');
    const [zMain, setZMain] = useState('2');
    const [zBuiltin, setZBuiltin] = useState('');
    const [hSteam, setHSteam] = useState('');
    const [xSteam, setXSteam] = useState('0.950');

    // Sync state for t1Builtin
    const [isT1BuiltinManuallyChanged, setIsT1BuiltinManuallyChanged] = useState(false);

    // Units
    const [gSteamUnit, setGSteamUnit] = useState<'т/ч' | 'кг/с'>('т/ч');
    const [wMainUnit, setWMainUnit] = useState<'т/ч' | 'кг/с' | 'м3/ч' | 'т/с'>('т/ч');
    const [t1MainUnit, setT1MainUnit] = useState<'°C' | 'K'>('°C');
    const [hSteamUnit, setHSteamUnit] = useState<'ккал/кг' | 'кДж/кг'>('ккал/кг');

    const [results, setResults] = useState<CalculationOutput | null>(null);
    const [lastPayload, setLastPayload] = useState<CalculationInput | null>(null);
    const [isExporting, setIsExporting] = useState(false);

    const resultsRef = useRef<HTMLDivElement>(null);

    // Default material when loaded
    useEffect(() => {
        if (materials && materials.length > 0 && materialId === null) {
            setMaterialId(materials[0].id);
        }
    }, [materials]);

    // BR-04: Sync t1_main with t1_builtin if not manually changed
    useEffect(() => {
        if (!isT1BuiltinManuallyChanged) {
            setT1Builtin(t1Main);
        }
    }, [t1Main, isT1BuiltinManuallyChanged]);

    const mutation = useMutation({
        mutationFn: (data: CalculationInput) => CalculationsService.calculateApiV1CalculatePost({ requestBody: data }),
        onSuccess: (data) => {
            setResults(data);
            toast({ title: "Расчет выполнен успешно!", status: "success" });
            setTimeout(() => {
                resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        },
        onError: (err: any) => {
            const detail = err?.body?.detail;
            let description: string;
            if (Array.isArray(detail)) {
                // FastAPI validation errors: array of {loc, msg, type}
                description = detail.map((e: any) => {
                    const field = Array.isArray(e.loc) ? e.loc.join(' → ') : String(e.loc ?? '');
                    return field ? `[${field}]: ${e.msg}` : e.msg;
                }).join('\n');
            } else if (typeof detail === 'string') {
                description = detail;
            } else {
                description = err?.message ?? 'Неизвестная ошибка';
            }
            toast({ title: "Ошибка расчета", description, status: "error", isClosable: true, duration: 8000 });
        }
    });

    const handleCalculate = () => {
        if (!condenserId) {
            toast({ title: "Ошибка", description: "Конденсатор не выбран.", status: "error" });
            return;
        }
        if (materialId === null) {
            toast({ title: "Ошибка", description: "Материал трубок не загружен.", status: "error" });
            return;
        }

        const gSteamArr = parseRange(gSteam);
        const wMainArr = parseRange(wMain);
        const t1MainArr = parseRange(t1Main);

        if (!gSteamArr.length || !wMainArr.length || !t1MainArr.length) {
            toast({ title: "Ошибка валидации", description: "Заполните обязательные поля: G_steam, W_main, t1_main (пример: '10 20 30' или '10-50-5').", status: "warning" });
            return;
        }

        const payload: CalculationInput = {
            condenser_id: condenserId,
            material_id: materialId,
            method: method,
            coefficient_b: coefficientB ? parseRange(coefficientB) : [1.0],
            G_steam: gSteamArr,
            W_main: wMainArr,
            t1_main: t1MainArr,
            G_steam_unit: gSteamUnit,
            W_main_unit: wMainUnit,
            t1_main_unit: t1MainUnit,
            H_steam_unit: hSteamUnit,
            Z_ejectors: Number(zEjectors) || 1,
            Z_main: Number(zMain) || 2,
        };

        if (wBuiltin) payload.W_builtin = parseRange(wBuiltin);
        if (t1Builtin) payload.t1_builtin = parseRange(t1Builtin);
        if (zBuiltin) payload.Z_builtin = Number(zBuiltin);
        if (hSteam) payload.H_steam = Number(hSteam);
        if (xSteam) payload.X_steam = Number(xSteam);

        setLastPayload(payload);
        mutation.mutate(payload);
    };

    const handleExportExcel = async () => {
        if (!lastPayload) return;
        setIsExporting(true);
        try {
            const response = await fetch('/api/v1/calculate/excel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(lastPayload)
            });
            if (!response.ok) throw new Error('Ошибка выгрузки Excel. Статус: ' + response.status);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `condenser_results.xlsx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            toast({ title: "Excel скачан", status: "success" });
        } catch (err: any) {
            toast({ title: "Ошибка выгрузки", description: err.message, status: "error" });
        } finally {
            setIsExporting(false);
        }
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

    const mainLimits = (condenser.water_flow_limits as any)?.main_bundle;
    const builtinLimits = (condenser.water_flow_limits as any)?.builtin_bundle;

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
                    <Heading size="md" mb={6}>Настройки расчета</Heading>

                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} mb={8}>
                        <FormControl>
                            <FormLabel>Методика расчета</FormLabel>
                            <RadioGroup onChange={(val: any) => setMethod(val)} value={method}>
                                <Stack direction="row" spacing={6}>
                                    <Radio value="berman">Методика Бермана</Radio>
                                    <Radio value="metro-vickers">Методика Метро-Виккерса</Radio>
                                </Stack>
                            </RadioGroup>
                        </FormControl>

                        <FormControl>
                            <FormLabel>Материал трубок</FormLabel>
                            <Select value={materialId ?? ''} onChange={(e) => setMaterialId(Number(e.target.value))}>
                                {materials?.map(m => (
                                    <option key={m.id} value={m.id}>{m.name}</option>
                                ))}
                            </Select>
                        </FormControl>
                    </SimpleGrid>

                    <Divider mb={6} />

                    <Box mb={8}>
                        <Heading size="sm" mb={4} color={headingColor}>Параметры охлаждающей воды</Heading>
                        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                            <FormControl isRequired>
                                <FormLabel>Расход воды осн. (W_main)</FormLabel>
                                <Flex><Input placeholder="4000 8000" value={wMain} onChange={e => setWMain(e.target.value)} />
                                    <Select w="100px" ml={2} value={wMainUnit} onChange={e => setWMainUnit(e.target.value as any)}>
                                        <option value="т/ч">т/ч</option><option value="м3/ч">м3/ч</option><option value="кг/с">кг/с</option>
                                    </Select>
                                </Flex>
                                {mainLimits && (
                                    <FormHelperText color="teal.500">Допустимо: {mainLimits.min} - {mainLimits.max}</FormHelperText>
                                )}
                            </FormControl>

                            <FormControl isDisabled={method === 'metro-vickers'}>
                                <FormLabel>Расход воды встр. (W_builtin)</FormLabel>
                                <Input placeholder="Массив..." value={wBuiltin} onChange={e => setWBuiltin(e.target.value)} />
                                {builtinLimits && (
                                    <FormHelperText color="teal.500">Допустимо: {builtinLimits.min} - {builtinLimits.max}</FormHelperText>
                                )}
                            </FormControl>

                            <FormControl isRequired>
                                <FormLabel>Темп. воды осн. (t1_main)</FormLabel>
                                <Flex><Input placeholder="10 20" value={t1Main} onChange={e => setT1Main(e.target.value)} />
                                    <Select w="100px" ml={2} value={t1MainUnit} onChange={e => setT1MainUnit(e.target.value as any)}>
                                        <option value="°C">°C</option><option value="K">K</option>
                                    </Select>
                                </Flex>
                            </FormControl>

                            <FormControl isDisabled={method === 'metro-vickers'}>
                                <FormLabel>Темп. воды встр. (t1_builtin)</FormLabel>
                                <Input placeholder="Синхронизация по умолч." value={t1Builtin} onChange={e => {
                                    setT1Builtin(e.target.value);
                                    setIsT1BuiltinManuallyChanged(true);
                                }} />
                            </FormControl>

                            <FormControl isRequired>
                                <FormLabel>Ходы воды осн. (Z_main)</FormLabel>
                                <Input placeholder="2" value={zMain} onChange={e => setZMain(e.target.value)} />
                            </FormControl>

                            <FormControl isDisabled={method === 'metro-vickers'}>
                                <FormLabel>Ходы воды встр. (Z_builtin)</FormLabel>
                                <Input placeholder="" value={zBuiltin} onChange={e => setZBuiltin(e.target.value)} />
                            </FormControl>
                        </SimpleGrid>
                    </Box>

                    <Divider mb={6} />

                    <Box mb={8}>
                        <Heading size="sm" mb={4} color={headingColor}>Параметры пара</Heading>
                        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                            <FormControl isRequired>
                                <FormLabel>Расход пара (G_steam)</FormLabel>
                                <Flex><Input placeholder="10-50-5" value={gSteam} onChange={e => setGSteam(e.target.value)} />
                                    <Select w="100px" ml={2} value={gSteamUnit} onChange={e => setGSteamUnit(e.target.value as any)}>
                                        <option value="т/ч">т/ч</option><option value="кг/с">кг/с</option>
                                    </Select>
                                </Flex>
                            </FormControl>

                            <FormControl isRequired={method === 'berman'} isDisabled={method === 'metro-vickers'}>
                                <FormLabel>Энтальпия пара (H_steam)</FormLabel>
                                <Flex><Input placeholder="Напр: 560" value={hSteam} onChange={e => setHSteam(e.target.value)} />
                                    <Select w="120px" ml={2} value={hSteamUnit} onChange={e => setHSteamUnit(e.target.value as any)}>
                                        <option value="ккал/кг">ккал/кг</option><option value="кДж/кг">кДж/кг</option>
                                    </Select>
                                </Flex>
                            </FormControl>

                            <FormControl isDisabled={method === 'berman'}>
                                <FormLabel>Сухость пара (X_steam)</FormLabel>
                                <Input placeholder="0.950" value={xSteam} onChange={e => setXSteam(e.target.value)} />
                            </FormControl>
                        </SimpleGrid>
                    </Box>

                    <Divider mb={6} />

                    <Box mb={6}>
                        <Heading size="sm" mb={4} color={headingColor}>Конструктив и прочее</Heading>
                        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                            <FormControl>
                                <FormLabel>Коэфф. загрязнения (b)</FormLabel>
                                <Input placeholder="Напр: 0.8 1.0" value={coefficientB} onChange={e => setCoefficientB(e.target.value)} />
                                <FormHelperText>Массив значений</FormHelperText>
                            </FormControl>
                            <FormControl isRequired>
                                <FormLabel>Кол-во эжекторов (Z_ejectors)</FormLabel>
                                <Input placeholder="1" value={zEjectors} onChange={e => setZEjectors(e.target.value)} />
                            </FormControl>
                        </SimpleGrid>
                    </Box>

                    <Button mt={4} colorScheme="teal" size="lg" onClick={handleCalculate} isLoading={mutation.isPending}>
                        Рассчитать
                    </Button>
                </Box>

                {results && (
                    <Box ref={resultsRef} p={6} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
                        <Flex justify="space-between" align="center" mb={4}>
                            <Heading size="md">Результаты ({results.total_tables} матриц)</Heading>
                            <Button
                                colorScheme="green"
                                size="sm"
                                onClick={handleExportExcel}
                                isLoading={isExporting}
                            >
                                В Excel
                            </Button>
                        </Flex>
                        <Tabs colorScheme="teal" variant="enclosed">
                            <TabList overflowX="auto" overflowY="hidden">
                                {results.tables.map((table, idx) => (
                                    <Tab key={idx} whiteSpace="nowrap">
                                        b={table.meta.coefficient_b as string}, W={table.meta.W_main as string}
                                    </Tab>
                                ))}
                            </TabList>
                            <TabPanels>
                                {results.tables.map((table, idx) => (
                                    <TabPanel key={idx} px={0}>
                                        {table.warnings && table.warnings.length > 0 && (
                                            <Alert status="warning" mb={4}>
                                                <AlertIcon />
                                                {table.warnings.join('; ')}
                                            </Alert>
                                        )}
                                        <Box overflowX="auto">
                                            <Table variant="striped" size="sm">
                                                <Thead>
                                                    <Tr>
                                                        <Th>t1 \ G_steam</Th>
                                                        {table.columns.map(c => <Th key={c}>{c}</Th>)}
                                                    </Tr>
                                                </Thead>
                                                <Tbody>
                                                    {table.rows.map((rowVal, rIdx) => (
                                                        <Tr key={rowVal}>
                                                            <Td fontWeight="bold">{rowVal}</Td>
                                                            {table.values[rIdx].map((val, cIdx) => (
                                                                <Td key={cIdx} bg={table.warnings?.length ? warningBg : undefined}>
                                                                    {typeof val === 'number' ? val.toFixed(4) : String(val ?? '-')}
                                                                </Td>
                                                            ))}
                                                        </Tr>
                                                    ))}
                                                </Tbody>
                                            </Table>
                                        </Box>
                                    </TabPanel>
                                ))}
                            </TabPanels>
                        </Tabs>

                        {results.ejector_results && results.ejector_results.length > 0 && (
                            <Box mt={8}>
                                <Heading size="sm" mb={4}>Параметры отсосов (Эжекторы)</Heading>
                                <Box overflowX="auto">
                                    <Table variant="simple" size="sm">
                                        <Thead>
                                            <Tr>
                                                <Th>Количество эжекторов</Th>
                                                <Th>Давление (кПа)</Th>
                                                <Th>Давление (атм)</Th>
                                            </Tr>
                                        </Thead>
                                        <Tbody>
                                            {results.ejector_results.map((ej, i) => (
                                                <Tr key={i}>
                                                    <Td>{ej.number_of_ejectors}</Td>
                                                    <Td>{ej.P_ejector_kPa.toFixed(4)}</Td>
                                                    <Td>{ej.P_ejector_atm.toFixed(4)}</Td>
                                                </Tr>
                                            ))}
                                        </Tbody>
                                    </Table>
                                </Box>
                            </Box>
                        )}
                    </Box>
                )}
            </VStack>
        </Container>
    );
}

export default CalculatorPage;