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
    RadioGroup,
    Radio,
    useColorModeValue,
} from '@chakra-ui/react';
import { FiChevronLeft, FiInfo } from "react-icons/fi";
import { useQuery } from '@tanstack/react-query';

import {
    type ValveInfo_Output as ValveInfo,
    type TurbineInfo,
    type MultiCalculationParams // <-- ИСПОЛЬЗУЕМ НОВЫЙ ТИП
} from '../../client';

import { InputWithUnit } from '../Common/InputWithUnit';
import { request as __request } from '../../client/core/request';
import { OpenAPI } from '../../client/core/OpenAPI';

// ---------------------------------------------------------------------
// Типы формы
// ---------------------------------------------------------------------
interface FormInputValues {
    turbine_id: number;
    valve_id: number;
    valve_name: string;
    valve_type: string;
    count_valves: number;

    // Глобальные параметры
    p_fresh: string;
    p_fresh_unit: string;
    
    // ПЕРЕКЛЮЧАТЕЛЬ T / H
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

    // Давления перед участками (p_values)
    p_values: { value: string; unit: string }[];

    // Динамические промежуточные отсосы (p_leak_offs)
    p_intermediates: { value: string; unit: string }[];
}

type Props = {
    stock: ValveInfo;
    turbine: TurbineInfo;
    onSubmit: (data: MultiCalculationParams) => void;
    initialData?: any; // Пока оставим any для совместимости с рутовым компонентом
    onGoBack?: () => void;
};

// ---------------------------------------------------------------------
// Утилиты
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
        const baseUrl = OpenAPI.BASE || import.meta.env.VITE_API_URL || '';
        const cleanBaseUrl = baseUrl.replace(/\/$/, '');
        const res = await fetch(`${cleanBaseUrl}/api/v1/utils/units`);
        return await res.json();
    } catch (e) {
        return {
            pressure: { available: ["кгс/см²", "МПа", "бар"] },
            temperature: { available: ["°C", "K"] },
            enthalpy: { available: ["ккал/кг", "кДж/кг"] }
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

    const {
        register,
        handleSubmit,
        control,
        watch,
        setValue,
        formState: { errors, isSubmitting },
    } = useForm<FormInputValues>({
        defaultValues: {
            turbine_id: turbine.id,
            valve_id: stock.id,
            valve_name: stock.name,
            valve_type: stock.type || "СК",
            count_valves: 1, // По умолчанию считаем 1 клапан, если это одиночный расчет
            
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

            p_values: Array.from({ length: countParts }, () => ({ value: '', unit: 'кгс/см²' })),
            p_intermediates: Array.from({ length: intermediateCount }, () => ({ value: '', unit: 'кгс/см²' })),
        },
        mode: 'onBlur',
    });

    const { fields: pValuesFields } = useFieldArray({ control, name: 'p_values' });
    const { fields: intermediateFields } = useFieldArray({ control, name: 'p_intermediates' });

    const thMode = watch('th_mode');

    const processSubmit: SubmitHandler<FormInputValues> = (data) => {
        // Собираем правильный JSON по новому контракту MultiCalculationParams
        
        // 1. Глобальные параметры
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

        // 2. Локальные параметры группы клапанов
        // В одиночном расчете мы отправляем массив groups с 1 элементом
        const parsedPValues = data.p_values.map(p => parseLocaleNumberStrict(p.value));
        const parsedPLeakOffs = data.p_intermediates.map(p => parseLocaleNumberStrict(p.value));

        const group = {
            valve_id: data.valve_id,
            type: data.valve_type,
            valve_names: [data.valve_name],
            quantity: data.count_valves, // В будущем здесь будет счетчик со страницы Корзины
            p_values: parsedPValues,
            p_values_unit: data.p_values[0]?.unit || "кгс/см²", // Берем единицу из первого поля
            p_leak_offs: parsedPLeakOffs,
            p_leak_offs_unit: data.p_intermediates[0]?.unit || "кгс/см²",
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

    const pressureUnits = unitsDict?.pressure?.available || ["кгс/см²"];
    const tempUnits = unitsDict?.temperature?.available || ["°C"];
    const enthalpyUnits = unitsDict?.enthalpy?.available || ["ккал/кг"];

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

            {/* ГЛОБАЛЬНЫЕ ПАРАМЕТРЫ */}
            <Box borderWidth="1px" borderRadius="lg" p={5} bg={boxBg} shadow="sm">
                <HStack mb={4} align="center">
                    <Heading as="h3" size="md">Глобальные параметры (Свежий пар и Воздух)</Heading>
                </HStack>

                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    <FormControl isRequired isInvalid={!!errors.p_fresh}>
                        <FormLabel>Давление свежего пара</FormLabel>
                        <Controller name="p_fresh" control={control} rules={{ required: "Обязательно", validate: isValidDecimal }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("p_fresh_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("p_fresh_unit", u)} />
                            )}
                        />
                    </FormControl>

                    {/* ПЕРЕКЛЮЧАТЕЛЬ ТЕМПЕРАТУРА ИЛИ ЭНТАЛЬПИЯ */}
                    <Box borderWidth="1px" p={3} borderRadius="md" borderColor="teal.200">
                        <RadioGroup onChange={(val: 'temperature' | 'enthalpy') => setValue('th_mode', val)} value={thMode} mb={3}>
                            <Stack direction="row" spacing={5}>
                                <Radio value="temperature" colorScheme="teal">Задать Температуру</Radio>
                                <Radio value="enthalpy" colorScheme="teal">Задать Энтальпию</Radio>
                            </Stack>
                        </RadioGroup>

                        {thMode === 'temperature' ? (
                            <FormControl isRequired isInvalid={!!errors.t_fresh}>
                                <Controller name="t_fresh" control={control} rules={{ required: "Обязательно", validate: isValidDecimal }}
                                    render={({ field }) => (
                                        <InputWithUnit value={field.value} unit={watch("t_fresh_unit")} availableUnits={tempUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("t_fresh_unit", u)} />
                                    )}
                                />
                            </FormControl>
                        ) : (
                            <FormControl isRequired isInvalid={!!errors.h_fresh}>
                                <Controller name="h_fresh" control={control} rules={{ required: "Обязательно", validate: isValidDecimal }}
                                    render={({ field }) => (
                                        <InputWithUnit value={field.value} unit={watch("h_fresh_unit")} availableUnits={enthalpyUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("h_fresh_unit", u)} />
                                    )}
                                />
                            </FormControl>
                        )}
                    </Box>

                    <FormControl isRequired isInvalid={!!errors.p_air}>
                        <FormLabel>Давление воздуха</FormLabel>
                        <Controller name="p_air" control={control} rules={{ required: "Обязательно" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("p_air_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("p_air_unit", u)} />
                            )}
                        />
                    </FormControl>

                    <FormControl isRequired isInvalid={!!errors.t_air}>
                        <FormLabel>Температура воздуха</FormLabel>
                        <Controller name="t_air" control={control} rules={{ required: "Обязательно" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("t_air_unit")} availableUnits={tempUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("t_air_unit", u)} />
                            )}
                        />
                    </FormControl>
                    
                    <FormControl isRequired isInvalid={!!errors.p_lst_leak_off} gridColumn={{ md: "span 2" }}>
                        <FormLabel>Давление последнего отсоса (Вакуум)</FormLabel>
                        <Controller name="p_lst_leak_off" control={control} rules={{ required: "Обязательно" }}
                            render={({ field }) => (
                                <InputWithUnit value={field.value} unit={watch("p_lst_leak_off_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={(u) => setValue("p_lst_leak_off_unit", u)} />
                            )}
                        />
                    </FormControl>
                </SimpleGrid>
            </Box>

            {/* ЛОКАЛЬНЫЕ ПАРАМЕТРЫ КЛАПАНА */}
            <Box borderWidth="1px" borderRadius="lg" p={5} bg={boxBgSecondary} shadow="sm">
                <Heading as="h3" size="md" mb={4}>Давления по участкам клапана ({countParts} шт)</Heading>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                    {pValuesFields.map((field, index) => (
                        <FormControl key={field.id} isRequired isInvalid={!!errors.p_values?.[index]?.value}>
                            <FormLabel fontSize="sm">P{index} (Перед участком {index + 1})</FormLabel>
                            <Controller name={`p_values.${index}.value` as const} control={control} rules={{ required: "Обязательно" }}
                                render={({ field: inputField }) => (
                                    <InputWithUnit value={inputField.value} unit={watch(`p_values.${index}.unit`)} availableUnits={pressureUnits} onValueChange={inputField.onChange} onUnitChange={(u) => setValue(`p_values.${index}.unit`, u)} />
                                )}
                            />
                        </FormControl>
                    ))}
                </SimpleGrid>

                {intermediateCount > 0 && (
                    <Box mt={6}>
                        <Heading as="h4" size="sm" mb={3}>Промежуточные отсосы ({intermediateCount} шт)</Heading>
                        <VStack spacing={4} align="stretch">
                            {intermediateFields.map((field, index) => (
                                <FormControl key={field.id} isRequired isInvalid={!!errors.p_intermediates?.[index]?.value}>
                                    <FormLabel fontSize="sm">Давление в камере {index + 1}:</FormLabel>
                                    <Controller name={`p_intermediates.${index}.value` as const} control={control} rules={{ required: "Обязательно" }}
                                        render={({ field: inputField }) => (
                                            <InputWithUnit value={inputField.value} unit={watch(`p_intermediates.${index}.unit`)} availableUnits={pressureUnits} onValueChange={inputField.onChange} onUnitChange={(u) => setValue(`p_intermediates.${index}.unit`, u)} />
                                        )}
                                    />
                                </FormControl>
                            ))}
                        </VStack>
                    </Box>
                )}
            </Box>

            <Button type="submit" colorScheme="teal" isLoading={isSubmitting} size="lg" height="60px" fontSize="xl">
                Рассчитать
            </Button>
        </VStack>
    );
};

export default StockInputPage;