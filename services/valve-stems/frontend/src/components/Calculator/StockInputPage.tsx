import React from 'react';
import { useForm, useFieldArray, Controller, type SubmitHandler } from 'react-hook-form';
import {
    Box, Button, FormControl, FormLabel, VStack, HStack, Heading, Text, Icon,
    SimpleGrid, Spinner, RadioGroup, Radio, Stack, useColorModeValue, FormErrorMessage,
} from '@chakra-ui/react';
import { FiChevronLeft } from "react-icons/fi";
import { useQuery } from '@tanstack/react-query';

import {
    type ValveInfo_Output as ValveInfo,
    type TurbineInfo,
    type MultiCalculationParams,
} from '../../client';
import { OpenAPI } from '../../client/core/OpenAPI'; // ИМПОРТ ДОБАВЛЕН
import { InputWithUnit } from '../Common/InputWithUnit';

interface FormInputValues {
    turbine_id: number;
    valve_id: number;
    valve_name: string;
    valve_type: string;
    count_valves: number;
    p_fresh: string;
    p_fresh_unit: string;
    th_mode: 'temperature' | 'enthalpy';
    t_fresh: string;
    t_fresh_unit: string;
    h_fresh: string;
    h_fresh_unit: string;
    p_air: string;
    p_air_unit: string;
    t_air: string;
    t_air_unit: string;
    p_lst_leak_off: string;
    p_lst_leak_off_unit: string;
    p_intermediates: { value: string; unit: string }[];
}

type Props = {
    stock: ValveInfo;
    turbine: TurbineInfo;
    onSubmit: (data: MultiCalculationParams) => void;
    initialData?: any; 
    onGoBack?: () => void;
};

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

// Надежный fetch, который сам найдет правильный базовый URL
const fetchUnits = async () => {
    try {
        const baseUrl = OpenAPI.BASE || '';
        const res = await fetch(`${baseUrl}/api/v1/utils/units`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        
        if (!res.ok) {
            throw new Error('Network response was not ok');
        }
        
        return await res.json();
    } catch (e) {
        console.error("Поймали ошибку в fetchUnits:", e);
        return {
            pressure: ["кгс/см²", "МПа", "бар", "Па (fallback)"],
            temperature: ["°C", "K"],
            enthalpy: ["ккал/кг", "кДж/кг"]
        };
    }
};

const StockInputPage: React.FC<Props> = ({ stock, turbine, onSubmit, onGoBack }) => {
    const countParts = stock.count_parts || 3;
    const intermediateCount = Math.max(0, countParts - 2);
    
    const boxBg = useColorModeValue('gray.50', 'gray.700');
    const boxBgSecondary = useColorModeValue('white', 'gray.700');

    const { data: unitsDict, isLoading: isUnitsLoading } = useQuery({
        queryKey: ['unitsDictionary'],
        queryFn: fetchUnits,
    });

    const { handleSubmit, control, watch, setValue, formState: { errors, isSubmitting } } = useForm<FormInputValues>({
        defaultValues: {
            turbine_id: turbine?.id ?? 0,
            valve_id: stock?.id ?? 0,
            valve_name: stock.name,
            valve_type: stock.type || "СК",
            count_valves: 1, 
            p_fresh: '130',
            p_fresh_unit: 'кгс/см²', 
            th_mode: 'temperature',
            t_fresh: '540',
            t_fresh_unit: '°C',
            h_fresh: '',
            h_fresh_unit: 'ккал/кг',
            p_air: '1.033',
            p_air_unit: 'кгс/см²',
            t_air: '27',
            t_air_unit: '°C',
            p_lst_leak_off: '0.97',
            p_lst_leak_off_unit: 'кгс/см²',
            p_intermediates: Array.from({ length: intermediateCount }, () => ({ value: '', unit: 'кгс/см²' })),
        },
        mode: 'onBlur',
    });

    const { fields: intermediateFields } = useFieldArray({ control, name: 'p_intermediates' });
    const thMode = watch('th_mode');

    const processSubmit: SubmitHandler<FormInputValues> = (data) => {
        const globals = {
            P_fresh: parseLocaleNumberStrict(data.p_fresh),
            P_fresh_unit: data.p_fresh_unit,
            T_fresh: data.th_mode === 'temperature' ? parseLocaleNumberStrict(data.t_fresh) : null,
            T_fresh_unit: data.t_fresh_unit,
            H_fresh: data.th_mode === 'enthalpy' ? parseLocaleNumberStrict(data.h_fresh) : null,
            H_fresh_unit: data.h_fresh_unit,
            P_air: parseLocaleNumberStrict(data.p_air),
            P_air_unit: data.p_air_unit,
            T_air: parseLocaleNumberStrict(data.t_air),
            T_air_unit: data.t_air_unit,
            P_lst_leak_off: parseLocaleNumberStrict(data.p_lst_leak_off),
            P_lst_leak_off_unit: data.p_lst_leak_off_unit,
        };

        const parsedPLeakOffs = data.p_intermediates.map(p => parseLocaleNumberStrict(p.value));

        const group = {
            valve_id: data.valve_id,
            type: data.valve_type,
            valve_names: [data.valve_name],
            quantity: data.count_valves,
            p_values: [], 
            p_values_unit: "кгс/см²", 
            p_leak_offs: parsedPLeakOffs,
            p_leak_offs_unit: data.p_intermediates.length > 0 ? data.p_intermediates[0].unit : "кгс/см²",
        };

        const payload: MultiCalculationParams = {
            turbine_id: data.turbine_id,
            globals: globals,
            groups: [group]
        };

        onSubmit(payload);
    };

    if (isUnitsLoading) {
        return (
             <VStack spacing={4} align="center" justify="center" minH="300px">
                 <Spinner size="xl" color="teal.500" />
                 <Text>Загрузка справочников...</Text>
             </VStack>
        )
    }

    // Идеальный парсинг. Ищем либо в корне (если fallback), либо в object.parameters (если пришло с бэкенда)
    const pressureUnits = unitsDict?.parameters?.pressure || unitsDict?.pressure || ["кгс/см²", "МПа", "бар"];
    const tempUnits = unitsDict?.parameters?.temperature || unitsDict?.temperature || ["°C", "K"];
    const enthalpyUnits = unitsDict?.parameters?.enthalpy || unitsDict?.enthalpy || ["ккал/кг", "кДж/кг"];

    return (
        <VStack as="form" onSubmit={handleSubmit(processSubmit)} spacing={6} p={5} w="100%" maxW="container.lg" mx="auto" align="stretch" noValidate>
            <Heading as="h2" size="lg" textAlign="center">
                Параметры расчёта <Text as="span" color="teal.500">{stock.name}</Text>
            </Heading>

            {onGoBack && (
                <Box width="100%" textAlign="center" my={2}>
                    <Button onClick={onGoBack} variant="outline" colorScheme="teal" size="sm" leftIcon={<Icon as={FiChevronLeft} />}>
                        Изменить клапан
                    </Button>
                </Box>
            )}

            <Box borderWidth="1px" borderRadius="lg" p={5} bg={boxBg} shadow="sm">
                <HStack mb={4} align="center">
                    <Heading as="h3" size="md">Глобальные параметры (Свежий пар и Воздух)</Heading>
                </HStack>

                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    <FormControl isRequired isInvalid={!!errors.p_fresh}>
                        <FormLabel>Давление свежего пара</FormLabel>
                        <Controller name="p_fresh" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("p_fresh_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("p_fresh_unit", u)} />
                            )}
                        />
                        <FormErrorMessage>{errors.p_fresh?.message as any}</FormErrorMessage>
                    </FormControl>

                    <Box borderWidth="1px" p={3} borderRadius="md" borderColor="teal.200">
                        <RadioGroup onChange={(val: 'temperature' | 'enthalpy') => setValue('th_mode', val)} value={thMode} mb={3}>
                            <Stack direction="row" spacing={5}>
                                <Radio value="temperature" colorScheme="teal">Задать Температуру</Radio>
                                <Radio value="enthalpy" colorScheme="teal">Задать Энтальпию</Radio>
                            </Stack>
                        </RadioGroup>

                        {thMode === 'temperature' ? (
                            <FormControl isRequired isInvalid={!!errors.t_fresh}>
                                <Controller name="t_fresh" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                                    render={({ field }) => (
                                        <InputWithUnit value={field.value} unit={watch("t_fresh_unit")} availableUnits={tempUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("t_fresh_unit", u)} />
                                    )}
                                />
                                <FormErrorMessage>{errors.t_fresh?.message as any}</FormErrorMessage>
                            </FormControl>
                        ) : (
                            <FormControl isRequired isInvalid={!!errors.h_fresh}>
                                <Controller name="h_fresh" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                                    render={({ field }) => (
                                        <InputWithUnit value={field.value} unit={watch("h_fresh_unit")} availableUnits={enthalpyUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("h_fresh_unit", u)} />
                                    )}
                                />
                                <FormErrorMessage>{errors.h_fresh?.message as any}</FormErrorMessage>
                            </FormControl>
                        )}
                    </Box>

                    <FormControl isRequired isInvalid={!!errors.p_air}>
                        <FormLabel>Давление воздуха</FormLabel>
                        <Controller name="p_air" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("p_air_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("p_air_unit", u)} />
                            )}
                        />
                        <FormErrorMessage>{errors.p_air?.message as any}</FormErrorMessage>
                    </FormControl>

                    <FormControl isRequired isInvalid={!!errors.t_air}>
                        <FormLabel>Температура воздуха</FormLabel>
                        <Controller name="t_air" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("t_air_unit")} availableUnits={tempUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("t_air_unit", u)} />
                            )}
                        />
                        <FormErrorMessage>{errors.t_air?.message as any}</FormErrorMessage>
                    </FormControl>
                    
                    <FormControl isRequired isInvalid={!!errors.p_lst_leak_off} gridColumn={{ md: "span 2" }}>
                        <FormLabel>Давление последнего отсоса (Вакуум)</FormLabel>
                        <Controller name="p_lst_leak_off" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("p_lst_leak_off_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("p_lst_leak_off_unit", u)} />
                            )}
                        />
                        <FormErrorMessage>{errors.p_lst_leak_off?.message as any}</FormErrorMessage>
                    </FormControl>
                </SimpleGrid>
            </Box>

            <Box borderWidth="1px" borderRadius="lg" p={5} bg={boxBgSecondary} shadow="sm">
                {intermediateCount > 0 ? (
                    <Box>
                        <Heading as="h4" size="sm" mb={3}>Промежуточные отсосы ({intermediateCount} шт)</Heading>
                        <VStack spacing={4} align="stretch">
                            {intermediateFields.map((field, index) => (
                                <FormControl key={field.id} isRequired isInvalid={!!errors.p_intermediates?.[index]?.value}>
                                    <FormLabel fontSize="sm">Давление в камере {index + 1}:</FormLabel>
                                    <Controller name={`p_intermediates.${index}.value` as const} control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                                        render={({ field: inputField }) => (
                                            <InputWithUnit value={inputField.value} unit={watch(`p_intermediates.${index}.unit`)} availableUnits={pressureUnits} onValueChange={inputField.onChange} onUnitChange={(u) => setValue(`p_intermediates.${index}.unit`, u)} />
                                        )}
                                    />
                                    <FormErrorMessage>{errors.p_intermediates?.[index]?.value?.message as any}</FormErrorMessage>
                                </FormControl>
                            ))}
                        </VStack>
                    </Box>
                ) : (
                    <Text color="gray.500">Для данного клапана промежуточные отсосы не требуются.</Text>
                )}
            </Box>

            <Button type="submit" colorScheme="teal" isLoading={isSubmitting} size="lg" height="60px" fontSize="xl">
                Рассчитать
            </Button>
        </VStack>
    );
};

export default StockInputPage;