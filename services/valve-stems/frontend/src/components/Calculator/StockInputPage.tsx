import React, { useEffect } from 'react';
import { useForm, useFieldArray, Controller, type SubmitHandler } from 'react-hook-form';
import {
    Box,
    Button,
    FormControl,
    FormLabel,
    FormErrorMessage,
    NumberInput,
    NumberInputField,
    NumberInputStepper,
    NumberIncrementStepper,
    NumberDecrementStepper,
    VStack,
    HStack,
    Heading,
    Text,
    Icon,
    Input,
    SimpleGrid,
    Divider,
    Alert,
    AlertIcon,
} from '@chakra-ui/react';
import { FiChevronLeft, FiInfo } from "react-icons/fi";

import {
    type ValveInfo_Output as ValveInfo,
    type TurbineInfo,
    type CalculationParams
} from '../../client';

// ---------------------------------------------------------------------
// Типы формы
// ---------------------------------------------------------------------

interface FormInputValues {
    turbine_name: string;
    valve_drawing: string;
    valve_id: number;
    count_valves: number;

    // Глобальные параметры
    p_fresh: string;        // P свежего пара
    t_fresh: string;        // T свежего пара
    p_air: string;          // P воздуха (по умолчанию 1.033)
    t_air: string;          // T воздуха (по умолчанию 40)
    p_lst_leak_off: string; // P последнего отсоса (по умолчанию 0.97)

    // Динамические промежуточные давления (если участков > 2)
    // Это будут давления в камерах (например, деаэратор)
    p_intermediates: { value: string }[];
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

const StockInputPage: React.FC<Props> = ({ stock, turbine, onSubmit, initialData, onGoBack }) => {
    // Определяем количество участков из данных клапана (или дефолт 3, если нет данных)
    const countParts = stock.count_parts || 3;
    
    // Количество промежуточных полей = N - 2
    // Если 2 участка -> 0 промежуточных
    // Если 3 участка -> 1 промежуточное (обычно Деаэратор)
    // Если 4 участка -> 2 промежуточных
    const intermediateCount = Math.max(0, countParts - 2);

    const {
        register,
        handleSubmit,
        control,
        formState: { errors, isSubmitting },
    } = useForm<FormInputValues>({
        defaultValues: {
            turbine_name: initialData?.turbine_name || turbine.name,
            valve_drawing: initialData?.valve_drawing || stock.name,
            valve_id: initialData?.valve_id || stock.id,
            count_valves: initialData?.count_valves || 3,
            
            // Инициализация глобальных параметров
            // Пытаемся достать из истории, если есть, иначе ставим дефолты
            p_fresh: initialData?.p_values?.[0] != null ? String(initialData.p_values[0]) : '',
            t_fresh: initialData?.temperature_start != null ? String(initialData.temperature_start) : '',
            
            p_air: initialData?.p_values?.[initialData.p_values.length - 1] != null 
                ? String(initialData.p_values[initialData.p_values.length - 1]) 
                : '1.033',
            t_air: initialData?.t_air != null ? String(initialData.t_air) : '40',
            
            p_lst_leak_off: initialData?.p_ejector?.[initialData.p_ejector.length - 1] != null 
                ? String(initialData.p_ejector[initialData.p_ejector.length - 1]) 
                : '0.97',

            // Инициализация промежуточных давлений
            // Берем из p_values, пропуская первый (свежий пар) и последний (воздух) элементы
            p_intermediates: initialData?.p_values && initialData.p_values.length > 2
                ? initialData.p_values.slice(1, -1).map(v => ({ value: String(v) }))
                : Array.from({ length: intermediateCount }, () => ({ value: '' })),
        },
        mode: 'onBlur',
    });

    const { fields: intermediateFields, append, remove } = useFieldArray({
        control,
        name: 'p_intermediates',
    });

    // Синхронизация количества полей с количеством участков (если вдруг stock изменится на лету, хотя это редкость)
    useEffect(() => {
        const currentLen = intermediateFields.length;
        if (currentLen < intermediateCount) {
            for (let i = 0; i < intermediateCount - currentLen; i++) append({ value: '' });
        } else if (currentLen > intermediateCount) {
            for (let i = currentLen - 1; i >= intermediateCount; i--) remove(i);
        }
    }, [intermediateCount, intermediateFields.length, append, remove]);

    const processSubmit: SubmitHandler<FormInputValues> = (data) => {
        // Парсим значения
        const pFresh = parseLocaleNumberStrict(data.p_fresh);
        const pAir = parseLocaleNumberStrict(data.p_air);
        const pLstLeakOff = parseLocaleNumberStrict(data.p_lst_leak_off);
        const pIntermediates = data.p_intermediates.map(p => parseLocaleNumberStrict(p.value));

        // ---------------------------------------------------------------------------
        // СБОРКА P_VALUES (Входные давления для каждого участка)
        // Логика: [P_fresh, ...P_intermediates, P_air]
        // ---------------------------------------------------------------------------
        const pValues = [pFresh, ...pIntermediates, pAir];

        // ---------------------------------------------------------------------------
        // СБОРКА P_EJECTOR (Давления всасывания/отсоса)
        // Логика зависит от количества участков (N).
        // Бэкенд ожидает N=2 -> 1 отсос, N=3 -> 1 отсос, N=4 -> 2 отсоса.
        // ---------------------------------------------------------------------------
        let pEjector: number[] = [];

        if (countParts === 2) {
            // Участок 1: Пар -> Отсос
            // Участок 2: Воздух -> Отсос
            pEjector = [pLstLeakOff];
        } else if (countParts === 3) {
            // Участок 1: Пар -> Промежуточный (pIntermediates[0], напр. Деаэратор)
            // Участок 2: Промежуточный -> Отсос (pLstLeakOff)
            // Участок 3: Воздух -> Отсос (pLstLeakOff)
            pEjector = [pLstLeakOff];
        } else if (countParts === 4) {
            // Для 4 участков логика сложнее. Обычно каскад.
            // Если есть промежуточные P1, P2.
            // Отсосы обычно идут в P2 и P_last.
            // Но в рамках текущей модели "Последний отсос" - это основной вакуум.
            // Если N=4, нам нужно 2 значения в массиве p_ejector.
            // Предположим, что первый отсос идет в последний промежуточный коллектор, а второй - в вакуум.
            if (pIntermediates.length >= 2) {
                 // Берем последний промежуточный как первый отсос, и P_last как второй
                 // Либо дублируем P_last, если схема подразумевает сброс всего в один коллектор.
                 // *Для надежности при N=4 берем последний промежуточный и вакуум*
                 // Но по ТЗ пользователя "Давление последнего отсоса" одно.
                 // Для совместимости с логикой бэкенда N=4 (требует 2 значения):
                 pEjector = [pIntermediates[pIntermediates.length - 1], pLstLeakOff];
            } else {
                 // Фолбек
                 pEjector = [pLstLeakOff, pLstLeakOff];
            }
        } else {
             // Фолбек для N > 4
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
        };

        onSubmit(calculationParams);
    };

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
                    <Button
                        onClick={onGoBack}
                        variant="outline"
                        colorScheme="teal"
                        size="sm"
                        leftIcon={<Icon as={FiChevronLeft} />}
                    >
                        Изменить клапан
                    </Button>
                </Box>
            )}

            <input type="hidden" {...register("turbine_name")} />
            <input type="hidden" {...register("valve_drawing")} />
            <input type="hidden" {...register("valve_id")} />

            {/* Количество клапанов */}
            <FormControl isRequired isInvalid={!!errors.count_valves} maxW="300px" mx="auto">
                <FormLabel htmlFor="count_valves" textAlign="center">Количество клапанов (N):</FormLabel>
                <Controller
                    name="count_valves"
                    control={control}
                    rules={{ required: "Обязательно", min: { value: 1, message: "Минимум 1" } }}
                    render={({ field }) => (
                        <NumberInput {...field} min={1} onChange={(_, val) => field.onChange(val)}>
                            <NumberInputField textAlign="center" />
                            <NumberInputStepper>
                                <NumberIncrementStepper />
                                <NumberDecrementStepper />
                            </NumberInputStepper>
                        </NumberInput>
                    )}
                />
                <FormErrorMessage>{errors.count_valves?.message}</FormErrorMessage>
            </FormControl>

            <Divider />

            {/* Глобальные параметры */}
            <Box borderWidth="1px" borderRadius="lg" p={5} bg="gray.50" shadow="sm">
                <HStack mb={4} align="center">
                    <Heading as="h3" size="md">Глобальные параметры</Heading>
                    <Icon as={FiInfo} color="teal.500" title="Основные параметры цикла и окружающей среды" />
                </HStack>

                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    {/* Свежий пар */}
                    <FormControl isRequired isInvalid={!!errors.p_fresh}>
                        <FormLabel>Давление свежего пара (кгс/см²)</FormLabel>
                        <Input
                            {...register("p_fresh", {
                                required: "Введите давление",
                                validate: v => isValidDecimal(v) || "Неверный формат числа"
                            })}
                            placeholder="P fresh"
                            bg="white"
                        />
                        <FormErrorMessage>{errors.p_fresh?.message}</FormErrorMessage>
                    </FormControl>

                    <FormControl isRequired isInvalid={!!errors.t_fresh}>
                        <FormLabel>Температура свежего пара (°С)</FormLabel>
                        <Input
                            {...register("t_fresh", {
                                required: "Введите температуру",
                                validate: v => isValidDecimal(v) || "Неверный формат числа"
                            })}
                            placeholder="T fresh"
                            bg="white"
                        />
                        <FormErrorMessage>{errors.t_fresh?.message}</FormErrorMessage>
                    </FormControl>

                    {/* Воздух */}
                    <FormControl isRequired isInvalid={!!errors.p_air}>
                        <FormLabel>
                            Давление воздуха (кгс/см²)
                            <Text as="span" fontSize="xs" color="gray.500" ml={2}>(Барометрическое)</Text>
                        </FormLabel>
                        <Input
                            {...register("p_air", {
                                required: "Обязательно",
                                validate: v => isValidDecimal(v) || "Неверный формат"
                            })}
                            bg="white"
                        />
                        <FormErrorMessage>{errors.p_air?.message}</FormErrorMessage>
                    </FormControl>

                    <FormControl isRequired isInvalid={!!errors.t_air}>
                        <FormLabel>
                            Температура воздуха (°С)
                            <Text as="span" fontSize="xs" color="gray.500" ml={2}>(Цех)</Text>
                        </FormLabel>
                        <Input
                            {...register("t_air", {
                                required: "Обязательно",
                                validate: v => isValidDecimal(v) || "Неверный формат"
                            })}
                            bg="white"
                        />
                        <FormErrorMessage>{errors.t_air?.message}</FormErrorMessage>
                    </FormControl>

                    {/* Последний отсос */}
                    <FormControl isRequired isInvalid={!!errors.p_lst_leak_off} gridColumn={{ md: "span 2" }}>
                        <FormLabel fontWeight="bold" color="teal.700">
                            Давление последнего отсоса (кгс/см²)
                            <Text as="span" fontSize="xs" color="gray.500" ml={2}>(Вакуум, обычно &lt; P воздуха)</Text>
                        </FormLabel>
                        <Input
                            {...register("p_lst_leak_off", {
                                required: "Введите давление вакуума",
                                validate: v => isValidDecimal(v) || "Неверный формат"
                            })}
                            bg="white"
                            borderColor="teal.200"
                            _focus={{ borderColor: "teal.500", boxShadow: "0 0 0 1px teal.500" }}
                        />
                        <FormErrorMessage>{errors.p_lst_leak_off?.message}</FormErrorMessage>
                    </FormControl>
                </SimpleGrid>
            </Box>

            {/* Промежуточные параметры (динамические) */}
            {intermediateCount > 0 && (
                <Box borderWidth="1px" borderRadius="lg" p={5} bg="white" shadow="sm">
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
                                <HStack>
                                    <FormLabel mb="0" minW="200px">
                                        Давление в камере {index + 1} (кгс/см²):
                                    </FormLabel>
                                    <Input
                                        {...register(`p_intermediates.${index}.value`, {
                                            required: "Это поле обязательно",
                                            validate: v => isValidDecimal(v) || "Неверный формат"
                                        })}
                                        placeholder={`Например: 6 (Деаэратор)`}
                                    />
                                </HStack>
                                <FormErrorMessage ml="210px">
                                    {errors.p_intermediates?.[index]?.value?.message}
                                </FormErrorMessage>
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