import React, { useMemo } from 'react';
import { useForm, useFieldArray, Controller, type SubmitHandler } from 'react-hook-form';
import {
    Box, Button, FormControl, FormLabel, VStack, HStack, Heading, Text, Icon,
    SimpleGrid, Spinner, RadioGroup, Radio, Stack, useColorModeValue, FormErrorMessage,
} from '@chakra-ui/react';
import { FiChevronLeft, FiInfo } from "react-icons/fi";
import { useQuery } from '@tanstack/react-query';

import {
    type TurbineInfo,
    type MultiCalculationParams,
    type CalculationGlobals,
    type ValveGroupInput,
} from '../../client';
import { OpenAPI } from '../../client/core/OpenAPI';
import { InputWithUnit } from '../Common/InputWithUnit';
import { type SelectedStock } from './StockSelection';

interface FormInputValues {
    globals: {
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
    };
    groups: {
        valveId: number;
        intermediates: { value: string; unit: string }[];
    }[];
}

type Props = {
    selectedStocks: SelectedStock[];
    turbine: TurbineInfo;
    onSubmit: (data: MultiCalculationParams) => void;
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
            pressure: ["кгс/см²", "МПа", "бар", "Па"],
            temperature: ["°C", "K"],
            enthalpy: ["ккал/кг", "кДж/кг"]
        };
    }
};

const StockInputPage: React.FC<Props> = ({ selectedStocks, turbine, onSubmit, onGoBack }) => {
    const boxBg = useColorModeValue('gray.50', 'gray.700');
    const boxBgSecondary = useColorModeValue('white', 'gray.700');

    const { data: unitsDict, isLoading: isUnitsLoading } = useQuery({
        queryKey: ['unitsDictionary'],
        queryFn: fetchUnits,
    });

    // Инициализация дефолтных значений для групп
    const defaultGroups = useMemo(() => {
        return selectedStocks.map(s => {
            const intermediateCount = Math.max(0, (s.valve.count_parts || 3) - 2);
            return {
                valveId: s.valve.id as number,
                intermediates: Array(intermediateCount).fill({ value: '', unit: 'кгс/см²' })
            };
        });
    }, [selectedStocks]);

    const { handleSubmit, control, watch, setValue, formState: { errors, isSubmitting } } = useForm<FormInputValues>({
        defaultValues: {
            globals: {
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
            },
            groups: defaultGroups
        },
        mode: 'onBlur',
    });

    const { fields: groupFields } = useFieldArray({ control, name: 'groups' });
    const thMode = watch('globals.th_mode');

    const processSubmit: SubmitHandler<FormInputValues> = (data) => {
        const globalsData: CalculationGlobals = {
            P_fresh: parseLocaleNumberStrict(data.globals.p_fresh),
            P_fresh_unit: data.globals.p_fresh_unit,
            T_fresh: data.globals.th_mode === 'temperature' ? parseLocaleNumberStrict(data.globals.t_fresh) : null as any, // Type coercion for API
            T_fresh_unit: data.globals.t_fresh_unit,
            H_fresh: data.globals.th_mode === 'enthalpy' ? parseLocaleNumberStrict(data.globals.h_fresh) : null as any,
            H_fresh_unit: data.globals.h_fresh_unit,
            P_air: parseLocaleNumberStrict(data.globals.p_air),
            P_air_unit: data.globals.p_air_unit,
            T_air: parseLocaleNumberStrict(data.globals.t_air),
            T_air_unit: data.globals.t_air_unit,
            P_lst_leak_off: parseLocaleNumberStrict(data.globals.p_lst_leak_off),
            P_lst_leak_off_unit: data.globals.p_lst_leak_off_unit,
        };

        const groupsData: ValveGroupInput[] = selectedStocks.map((stock, i) => {
            const groupData = data.groups[i];
            const parsedIntermediates = groupData.intermediates.map(p => parseLocaleNumberStrict(p.value));
            
            const pValues = [globalsData.P_fresh, ...parsedIntermediates, globalsData.P_air] as number[];

            return {
                valve_id: stock.valve.id as number,
                type: stock.valve.type || "Неизвестно",
                valve_names: [stock.valve.name],
                quantity: stock.quantity,
                p_values: pValues,
                p_values_unit: globalsData.P_fresh_unit,
                p_leak_offs: parsedIntermediates,
                p_leak_offs_unit: groupData.intermediates.length > 0 ? groupData.intermediates[0].unit : globalsData.P_fresh_unit,
            };
        });

        const payload: MultiCalculationParams = {
            turbine_id: turbine.id,
            globals: globalsData,
            groups: groupsData
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

    // Безопасный парсинг массивов
    const getSafeArray = (key: string, defaultArray: string[]) => {
        if (!unitsDict) return defaultArray;
        if (unitsDict.parameters && Array.isArray(unitsDict.parameters[key])) return unitsDict.parameters[key];
        if (Array.isArray(unitsDict[key])) return unitsDict[key];
        return defaultArray;
    };

    const pressureUnits = getSafeArray('pressure', ["кгс/см²", "МПа", "бар"]);
    const tempUnits = getSafeArray('temperature', ["°C", "K"]);
    const enthalpyUnits = getSafeArray('enthalpy', ["ккал/кг", "кДж/кг"]);

    return (
        <VStack as="form" onSubmit={handleSubmit(processSubmit)} spacing={6} p={5} w="100%" maxW="container.lg" mx="auto" align="stretch" noValidate>
            <Heading as="h2" size="lg" textAlign="center">
                Параметры расчёта
            </Heading>
            <Text textAlign="center" fontSize="md" color="gray.600">
                Турбина: {turbine.name} | Выбрано клапанов: {selectedStocks.length}
            </Text>

            {onGoBack && (
                <Box width="100%" textAlign="center" my={2}>
                    <Button onClick={onGoBack} variant="outline" colorScheme="teal" size="sm" leftIcon={<Icon as={FiChevronLeft} />}>
                        Изменить состав клапанов
                    </Button>
                </Box>
            )}

            {/* ГЛОБАЛЬНЫЕ ПАРАМЕТРЫ */}
            <Box borderWidth="1px" borderRadius="lg" p={5} bg={boxBg} shadow="sm">
                <HStack mb={4} align="center">
                    <Heading as="h3" size="md">Глобальные параметры (Свежий пар и Воздух)</Heading>
                    <Icon as={FiInfo} color="teal.500" />
                </HStack>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    <FormControl isRequired isInvalid={!!errors.globals?.p_fresh}>
                        <FormLabel>Давление свежего пара</FormLabel>
                        <Controller name="globals.p_fresh" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("globals.p_fresh_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("globals.p_fresh_unit", u)} />
                            )}
                        />
                        <FormErrorMessage>{errors.globals?.p_fresh?.message as any}</FormErrorMessage>
                    </FormControl>

                    <Box borderWidth="1px" p={3} borderRadius="md" borderColor="teal.200">
                        <RadioGroup onChange={(val: 'temperature' | 'enthalpy') => setValue('globals.th_mode', val)} value={thMode} mb={3}>
                            <Stack direction="row" spacing={5}>
                                <Radio value="temperature" colorScheme="teal">Задать Температуру</Radio>
                                <Radio value="enthalpy" colorScheme="teal">Задать Энтальпию</Radio>
                            </Stack>
                        </RadioGroup>

                        {thMode === 'temperature' ? (
                            <FormControl isRequired isInvalid={!!errors.globals?.t_fresh}>
                                <Controller name="globals.t_fresh" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                                    render={({ field }) => (
                                        <InputWithUnit value={field.value} unit={watch("globals.t_fresh_unit")} availableUnits={tempUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("globals.t_fresh_unit", u)} />
                                    )}
                                />
                                <FormErrorMessage>{errors.globals?.t_fresh?.message as any}</FormErrorMessage>
                            </FormControl>
                        ) : (
                            <FormControl isRequired isInvalid={!!errors.globals?.h_fresh}>
                                <Controller name="globals.h_fresh" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                                    render={({ field }) => (
                                        <InputWithUnit value={field.value} unit={watch("globals.h_fresh_unit")} availableUnits={enthalpyUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("globals.h_fresh_unit", u)} />
                                    )}
                                />
                                <FormErrorMessage>{errors.globals?.h_fresh?.message as any}</FormErrorMessage>
                            </FormControl>
                        )}
                    </Box>

                    <FormControl isRequired isInvalid={!!errors.globals?.p_air}>
                        <FormLabel>Давление воздуха (Барометрическое)</FormLabel>
                        <Controller name="globals.p_air" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("globals.p_air_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("globals.p_air_unit", u)} />
                            )}
                        />
                        <FormErrorMessage>{errors.globals?.p_air?.message as any}</FormErrorMessage>
                    </FormControl>

                    <FormControl isRequired isInvalid={!!errors.globals?.t_air}>
                        <FormLabel>Температура воздуха (Цех)</FormLabel>
                        <Controller name="globals.t_air" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("globals.t_air_unit")} availableUnits={tempUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("globals.t_air_unit", u)} />
                            )}
                        />
                        <FormErrorMessage>{errors.globals?.t_air?.message as any}</FormErrorMessage>
                    </FormControl>
                    
                    <FormControl isRequired isInvalid={!!errors.globals?.p_lst_leak_off} gridColumn={{ md: "span 2" }}>
                        <FormLabel color="teal.600" fontWeight="bold">Давление последнего отсоса (Вакуум)</FormLabel>
                        <Controller name="globals.p_lst_leak_off" control={control} rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("globals.p_lst_leak_off_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("globals.p_lst_leak_off_unit", u)} />
                            )}
                        />
                        <FormErrorMessage>{errors.globals?.p_lst_leak_off?.message as any}</FormErrorMessage>
                    </FormControl>
                </SimpleGrid>
            </Box>

            {/* ПРОМЕЖУТОЧНЫЕ ОТСОСЫ */}
            {groupFields.map((field, idx) => {
                const stockItem = selectedStocks[idx];
                const intermediateCount = Math.max(0, (stockItem.valve.count_parts || 3) - 2);
                
                if (intermediateCount === 0) return null;

                return (
                    <Box key={field.id} borderWidth="1px" borderRadius="lg" p={5} bg={boxBgSecondary} shadow="sm">
                        <Heading as="h4" size="sm" mb={3}>
                            Промежуточные отсосы: {stockItem.valve.name} ({stockItem.quantity} шт)
                        </Heading>
                        <VStack spacing={4} align="stretch">
                            {Array.from({ length: intermediateCount }).map((_, i) => (
                                <FormControl key={i} isRequired isInvalid={!!errors.groups?.[idx]?.intermediates?.[i]?.value}>
                                    <FormLabel fontSize="sm">Давление в камере {i + 1}:</FormLabel>
                                    <Controller 
                                        name={`groups.${idx}.intermediates.${i}.value` as const} 
                                        control={control} 
                                        rules={{ required: "Обязательно", validate: (v: any) => isValidDecimal(v) || "Неверный формат" }}
                                        render={({ field: inputField }) => (
                                            <InputWithUnit 
                                                value={inputField.value} 
                                                unit={watch(`groups.${idx}.intermediates.${i}.unit` as any) || 'кгс/см²'} 
                                                availableUnits={pressureUnits} 
                                                onValueChange={inputField.onChange} 
                                                onUnitChange={(u) => setValue(`groups.${idx}.intermediates.${i}.unit` as any, u)} 
                                            />
                                        )}
                                    />
                                    <FormErrorMessage>{errors.groups?.[idx]?.intermediates?.[i]?.value?.message as any}</FormErrorMessage>
                                </FormControl>
                            ))}
                        </VStack>
                    </Box>
                );
            })}

            <Button type="submit" colorScheme="teal" isLoading={isSubmitting} size="lg" mt={4} height="60px" fontSize="xl">
                Рассчитать
            </Button>
        </VStack>
    );
};

export default StockInputPage;