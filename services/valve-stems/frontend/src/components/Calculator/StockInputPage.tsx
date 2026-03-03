import React, { useEffect } from 'react';
import { useForm, useFieldArray, Controller, type SubmitHandler } from 'react-hook-form';
import {
    Box,
    Button,
    FormControl,
    FormLabel,
    FormErrorMessage,
    VStack,
    HStack,
    Heading,
    Text,
    Icon,
    SimpleGrid,
    Alert,
    AlertIcon,
    Spinner,
    useColorModeValue,
} from '@chakra-ui/react';
import { FiChevronLeft, FiInfo } from "react-icons/fi";

import {
    type ValveInfo_Output as ValveInfo,
    type TurbineInfo,
    type CalculationParams
} from '../../client';

import { InputWithUnit } from '../Common/InputWithUnit';
import { request as __request } from '../../client/core/request';
import { OpenAPI } from '../../client/core/OpenAPI';
import { useQuery } from '@tanstack/react-query';

// ---------------------------------------------------------------------
// Типы формы
// ---------------------------------------------------------------------

interface FormInputValues {
    turbine_name: string;
    valve_drawing: string;
    valve_id: number;
    count_valves: number;

    // Глобальные параметры (значение + единица измерения)
    p_fresh: string;
    p_fresh_unit: string;
    
    t_fresh: string;
    t_fresh_unit: string;
    
    p_air: string;
    p_air_unit: string;
    
    t_air: string;
    t_air_unit: string;
    
    p_lst_leak_off: string;
    p_lst_leak_off_unit: string;

    // Динамические промежуточные давления
    p_intermediates: { value: string; unit: string }[];
}

type Props = {
    stock: ValveInfo;
    turbine: TurbineInfo;
    onSubmit: (data: CalculationParams) => void;
    initialData?: Partial<CalculationParams>;
    onGoBack?: () => void;
};

// ---------------------------------------------------------------------
// Утилиты валидации
// ---------------------------------------------------------------------
const MAX_SCALE = 4;

const isValidDecimal = (val: unknown) => {
    const s = String(val ?? '').trim().replace(/\s/g, '');
    if (!/^-?\d+(?:[.,]\d+)?$/.test(s)) return false;
    const frac = s.split(/[.,]/)[1];
    return !(frac && frac.length > MAX_SCALE);
};

const parseLocaleNumberStrict = (val: unknown): number => {
    const s = String(val ?? '').trim().replace(/\s/g, '').replace(',', '.');
    if (!/^-?\d+(\.\d+)?$/.test(s)) return NaN;
    const n = Number(s);
    return Number.isFinite(n) ? n : NaN;
};

// Запрос за единицами измерения
const fetchUnits = async () => {
    try {
        const res = await __request(OpenAPI, { method: 'GET', url: '/api/v1/utils/units' });
        return (res as any).parameters;
    } catch (e) {
        return {
            pressure: ["кгс/см²", "МПа", "Па", "кПа", "бар", "атм (тех)"],
            temperature: ["°C", "K"],
        };
    }
};

const StockInputPage: React.FC<Props> = ({ stock, turbine, onSubmit, initialData, onGoBack }) => {
    const countParts = stock.count_parts || 3;
    const intermediateCount = Math.max(0, countParts - 2);
    const boxBg = useColorModeValue('gray.50', 'gray.700');
    const boxBgSecondary = useColorModeValue('white', 'gray.700');
    const labelAccentColor = useColorModeValue('teal.700', 'teal.300');

    // Получаем список единиц измерения с бэкенда
    const { data: unitsDict, isLoading: isUnitsLoading } = useQuery({
        queryKey: ['unitsDictionary'],
        queryFn: fetchUnits,
    });

    const {
        register,
        handleSubmit,
        control,
        watch,
        setValue,
        formState: { errors, isSubmitting },
    } = useForm<FormInputValues>({
        defaultValues: {
            turbine_name: initialData?.turbine_name || turbine.name,
            valve_drawing: initialData?.valve_drawing || stock.name,
            valve_id: initialData?.valve_id || stock.id,
            count_valves: initialData?.count_valves || 3,
            
            p_fresh: initialData?.p_values?.[0] != null ? String(initialData.p_values[0]) : '',
            p_fresh_unit: 'кгс/см²', // Дефолтные значения
            
            t_fresh: initialData?.temperature_start != null ? String(initialData.temperature_start) : '',
            t_fresh_unit: '°C',
            
            p_air: initialData?.p_values?.[initialData.p_values.length - 1] != null 
                ? String(initialData.p_values[initialData.p_values.length - 1]) : '1.033',
            p_air_unit: 'кгс/см²',
            
            t_air: initialData?.t_air != null ? String(initialData.t_air) : '40',
            t_air_unit: '°C',
            
            p_lst_leak_off: initialData?.p_ejector?.[initialData.p_ejector.length - 1] != null 
                ? String(initialData.p_ejector[initialData.p_ejector.length - 1]) : '0.97',
            p_lst_leak_off_unit: 'кгс/см²',

            p_intermediates: initialData?.p_values && initialData.p_values.length > 2
                ? initialData.p_values.slice(1, -1).map(v => ({ value: String(v), unit: 'кгс/см²' }))
                : Array.from({ length: intermediateCount }, () => ({ value: '', unit: 'кгс/см²' })),
        },
        mode: 'onBlur',
    });

    const { fields: intermediateFields, append, remove } = useFieldArray({
        control,
        name: 'p_intermediates',
    });

    useEffect(() => {
        const currentLen = intermediateFields.length;
        if (currentLen < intermediateCount) {
            for (let i = 0; i < intermediateCount - currentLen; i++) append({ value: '', unit: 'кгс/см²' });
        } else if (currentLen > intermediateCount) {
            for (let i = currentLen - 1; i >= intermediateCount; i--) remove(i);
        }
    }, [intermediateCount, intermediateFields.length, append, remove]);

    const processSubmit: SubmitHandler<FormInputValues> = (data) => {
        const pFresh = parseLocaleNumberStrict(data.p_fresh);
        const pAir = parseLocaleNumberStrict(data.p_air);
        const pLstLeakOff = parseLocaleNumberStrict(data.p_lst_leak_off);
        const pIntermediates = data.p_intermediates.map(p => parseLocaleNumberStrict(p.value));

        const pValues = [pFresh, ...pIntermediates, pAir];
        let pEjector: number[] = [];

        if (countParts === 2 || countParts === 3) {
            pEjector = [pLstLeakOff];
        } else if (countParts === 4) {
             pEjector = [pIntermediates[pIntermediates.length - 1] || pLstLeakOff, pLstLeakOff];
        } else {
             pEjector = Array(Math.max(1, countParts - 2)).fill(pLstLeakOff);
        }

        const calculationParams: CalculationParams = {
            turbine_name: data.turbine_name,
            valve_drawing: data.valve_drawing,
            valve_id: data.valve_id,
            temperature_start: parseLocaleNumberStrict(data.t_fresh),
            t_air: parseLocaleNumberStrict(data.t_air),
            count_valves: data.count_valves,
            p_values: pValues,
            p_ejector: pEjector,
        } as any; 

        onSubmit(calculationParams);
    };

    if (isUnitsLoading) {
        return (
             <VStack spacing={4} align="center" justify="center" minH="300px">
                 <Spinner size="xl" color="teal.500" />
                 <Text>Загрузка справочников...</Text>
             </VStack>
        )
    }

    const pressureUnits = unitsDict?.pressure || ["кгс/см²"];
    const tempUnits = unitsDict?.temperature || ["°C"];

    return (
        <VStack
            as="form"
            onSubmit={handleSubmit(processSubmit)}
            spacing={6}
            p={5}
            w="100%"
            maxW="container.lg"
            mx="auto"
            align="stretch"
            noValidate
        >
            <Heading as="h2" size="lg" textAlign="center">
                Ввод параметров расчёта <Text as="span" color="teal.500">{stock.name}</Text>
            </Heading>
            <Text textAlign="center" fontSize="md" color="gray.600">
                Турбина: {turbine.name} | Участков в уплотнении: <b>{countParts}</b>
            </Text>

            {onGoBack && (
                <Box width="100%" textAlign="center" my={2}>
                    <Button onClick={onGoBack} variant="outline" colorScheme="teal" size="sm" leftIcon={<Icon as={FiChevronLeft} />}>
                        Изменить клапан
                    </Button>
                </Box>
            )}

            <input type="hidden" {...register("turbine_name")} />
            <input type="hidden" {...register("valve_drawing")} />
            <input type="hidden" {...register("valve_id")} />
            <input type="hidden" {...register("count_valves", { valueAsNumber: true })} />

            <Box borderWidth="1px" borderRadius="lg" p={5} bg={boxBg} shadow="sm">
                <HStack mb={4} align="center">
                    <Heading as="h3" size="md">Глобальные параметры</Heading>
                    <Icon as={FiInfo} color="teal.500" title="Основные параметры цикла и окружающей среды" />
                </HStack>

                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    {/* Свежий пар */}
                    <FormControl isRequired isInvalid={!!errors.p_fresh}>
                        <FormLabel>Давление свежего пара</FormLabel>
                        <Controller
                            name="p_fresh"
                            control={control}
                            rules={{ required: "Введите давление", validate: v => isValidDecimal(v) || "Неверный формат числа" }}
                            render={({ field }) => (
                                <InputWithUnit
                                    value={field.value}
                                    unit={watch("p_fresh_unit")}
                                    availableUnits={pressureUnits}
                                    onValueChange={field.onChange}
                                    onUnitChange={(newUnit) => setValue("p_fresh_unit", newUnit)}
                                    placeholder="Например: 130"
                                />
                            )}
                        />
                        <FormErrorMessage>{errors.p_fresh?.message}</FormErrorMessage>
                    </FormControl>

                    <FormControl isRequired isInvalid={!!errors.t_fresh}>
                        <FormLabel>Температура свежего пара</FormLabel>
                        <Controller
                            name="t_fresh"
                            control={control}
                            rules={{ required: "Введите температуру", validate: v => isValidDecimal(v) || "Неверный формат числа" }}
                            render={({ field }) => (
                                <InputWithUnit
                                    value={field.value}
                                    unit={watch("t_fresh_unit")}
                                    availableUnits={tempUnits}
                                    onValueChange={field.onChange}
                                    onUnitChange={(newUnit) => setValue("t_fresh_unit", newUnit)}
                                    placeholder="Например: 555"
                                />
                            )}
                        />
                        <FormErrorMessage>{errors.t_fresh?.message}</FormErrorMessage>
                    </FormControl>

                    {/* Воздух */}
                    <FormControl isRequired isInvalid={!!errors.p_air}>
                        <FormLabel>Давление воздуха <Text as="span" fontSize="xs" color="gray.500">(Барометрическое)</Text></FormLabel>
                        <Controller
                            name="p_air"
                            control={control}
                            rules={{ required: "Обязательно", validate: v => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit
                                    value={field.value}
                                    unit={watch("p_air_unit")}
                                    availableUnits={pressureUnits}
                                    onValueChange={field.onChange}
                                    onUnitChange={(newUnit) => setValue("p_air_unit", newUnit)}
                                />
                            )}
                        />
                        <FormErrorMessage>{errors.p_air?.message}</FormErrorMessage>
                    </FormControl>

                    <FormControl isRequired isInvalid={!!errors.t_air}>
                        <FormLabel>Температура воздуха <Text as="span" fontSize="xs" color="gray.500">(Цех)</Text></FormLabel>
                        <Controller
                            name="t_air"
                            control={control}
                            rules={{ required: "Обязательно", validate: v => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit
                                    value={field.value}
                                    unit={watch("t_air_unit")}
                                    availableUnits={tempUnits}
                                    onValueChange={field.onChange}
                                    onUnitChange={(newUnit) => setValue("t_air_unit", newUnit)}
                                />
                            )}
                        />
                        <FormErrorMessage>{errors.t_air?.message}</FormErrorMessage>
                    </FormControl>

                    {/* Последний отсос */}
                    <FormControl isRequired isInvalid={!!errors.p_lst_leak_off} gridColumn={{ md: "span 2" }}>
                        <FormLabel fontWeight="bold" color={labelAccentColor}>
                            Давление последнего отсоса <Text as="span" fontSize="xs" color="gray.500">(Вакуум)</Text>
                        </FormLabel>
                        <Controller
                            name="p_lst_leak_off"
                            control={control}
                            rules={{ required: "Введите давление вакуума", validate: v => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit
                                    value={field.value}
                                    unit={watch("p_lst_leak_off_unit")}
                                    availableUnits={pressureUnits}
                                    onValueChange={field.onChange}
                                    onUnitChange={(newUnit) => setValue("p_lst_leak_off_unit", newUnit)}
                                    borderColor="teal.200"
                                />
                            )}
                        />
                        <FormErrorMessage>{errors.p_lst_leak_off?.message}</FormErrorMessage>
                    </FormControl>
                </SimpleGrid>
            </Box>

            {/* Промежуточные параметры */}
            {intermediateCount > 0 && (
                <Box borderWidth="1px" borderRadius="lg" p={5} bg={boxBgSecondary} shadow="sm">
                    <HStack mb={4} align="center">
                        <Heading as="h3" size="md">Промежуточные отсосы</Heading>
                        <Text fontSize="sm" color="gray.500">(Давления в камерах между участками)</Text>
                    </HStack>

                    <Alert status="info" variant="subtle" mb={4} borderRadius="md" size="sm">
                        <AlertIcon />
                        Для схемы из {countParts} участков необходимо ввести {intermediateCount} промежуточных давлений (например, Деаэратор).
                    </Alert>

                    <VStack spacing={4} align="stretch">
                        {intermediateFields.map((field, index) => (
                            <FormControl key={field.id} isRequired isInvalid={!!errors.p_intermediates?.[index]?.value}>
                                <FormLabel mb="1">Давление в камере {index + 1}:</FormLabel>
                                <Controller
                                    name={`p_intermediates.${index}.value` as const}
                                    control={control}
                                    rules={{ required: "Это поле обязательно", validate: v => isValidDecimal(v) || "Неверный формат" }}
                                    render={({ field: inputField }) => (
                                        <InputWithUnit
                                            value={inputField.value}
                                            unit={watch(`p_intermediates.${index}.unit`)}
                                            availableUnits={pressureUnits}
                                            onValueChange={inputField.onChange}
                                            onUnitChange={(newUnit) => setValue(`p_intermediates.${index}.unit`, newUnit)}
                                            placeholder={`Например: 6 (Деаэратор)`}
                                        />
                                    )}
                                />
                                <FormErrorMessage>{errors.p_intermediates?.[index]?.value?.message}</FormErrorMessage>
                            </FormControl>
                        ))}
                    </VStack>
                </Box>
            )}

            <Button
                type="submit"
                colorScheme="teal"
                isLoading={isSubmitting}
                size="lg"
                mt={4}
                width="full"
                height="60px"
                fontSize="xl"
            >
                Рассчитать
            </Button>
        </VStack>
    );
};

export default StockInputPage;