import React, {useEffect} from 'react';
import {useForm, useFieldArray, Controller, type SubmitHandler} from 'react-hook-form';
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
} from '@chakra-ui/react';

import {
    type ValveInfo_Output as ValveInfo,
    type TurbineInfo,
    type CalculationParams
} from '../../client';
import {FiChevronLeft} from "react-icons/fi";

interface FormInputValues {
    turbine_name: string;
    valve_drawing: string;
    valve_id: number;
    temperature_start: string;
    t_air: string;
    count_valves: number;
    p_values: { value: string }[];
    p_ejector: { value: string }[];
    count_parts_select: number;
}

type Props = {
    stock: ValveInfo;
    turbine: TurbineInfo;
    onSubmit: (data: CalculationParams) => void;
    initialData?: Partial<CalculationParams>;
    onGoBack?: () => void;
};

// Ограничение точности: задайте число, если хотите лимит на кол-во знаков после запятой (например, 3).
// Оставьте undefined — без ограничения.
const MAX_SCALE = 3;

const isValidDecimal = (val: unknown) => {
    const s = String(val ?? '').trim().replace(/\s/g, '');
    // Разрешаем: -?целая[,(.)дробная]
    if (!/^-?\d+(?:[.,]\d+)?$/.test(s)) return false;

    const frac = s.split(/[.,]/)[1];
    return !(frac && frac.length > MAX_SCALE);
};

const parseLocaleNumberStrict = (val: unknown): number => {
    const s = String(val ?? '').trim().replace(/\s/g, '').replace(',', '.');
    // Запрещаем экспоненту и любые нецифровые символы кроме одной точки
    if (!/^-?\d+(\.\d+)?$/.test(s)) return NaN;
    const n = Number(s);
    return Number.isFinite(n) ? n : NaN;
};

const StockInputPage: React.FC<Props> = ({stock, turbine, onSubmit, initialData, onGoBack}) => {
    const defaultCountParts = initialData?.p_values?.length || stock.count_parts || 2;

    const {
        register,
        handleSubmit,
        control,
        reset,
        formState: {errors, isSubmitting},
    } = useForm<FormInputValues>({
        defaultValues: {
            turbine_name: initialData?.turbine_name || turbine.name,
            valve_drawing: initialData?.valve_drawing || stock.name,
            valve_id: initialData?.valve_id || stock.id,
            temperature_start: initialData?.temperature_start != null ? String(initialData.temperature_start) : '',
            t_air: initialData?.t_air != null ? String(initialData.t_air) : '',
            count_valves: initialData?.count_valves || 3,
            count_parts_select: defaultCountParts,
            p_values:
                initialData?.p_values?.map(v => ({value: v != null ? String(v) : ''})) ||
                Array.from({length: defaultCountParts}, () => ({value: ''})),
            p_ejector:
                initialData?.p_ejector?.map(v => ({value: v != null ? String(v) : ''})) ||
                Array.from({length: defaultCountParts}, () => ({value: ''})),
        },
        mode: 'onBlur',
    });

    const {fields: pValueFields, append: appendPValue, remove: removePValue} = useFieldArray({
        control,
        name: 'p_values',
    });

    const {fields: pEjectorFields, append: appendPEjector, remove: removePEjector} = useFieldArray({
        control,
        name: 'p_ejector',
    });

    useEffect(() => {
        const currentPValuesLength = pValueFields.length;
        const targetLength = Number(defaultCountParts) || 0;

        if (targetLength > currentPValuesLength) {
            for (let i = 0; i < targetLength - currentPValuesLength; i++) {
                appendPValue({value: ''});
            }
        } else if (targetLength < currentPValuesLength) {
            for (let i = currentPValuesLength - 1; i >= targetLength; i--) {
                removePValue(i);
            }
        }

        const currentPEjectorsLength = pEjectorFields.length;
        if (targetLength > currentPEjectorsLength) {
            for (let i = 0; i < targetLength - currentPEjectorsLength; i++) {
                appendPEjector({value: ''});
            }
        } else if (targetLength < currentPEjectorsLength) {
            for (let i = currentPEjectorsLength - 1; i >= targetLength; i--) {
                removePEjector(i);
            }
        }
    }, [
        defaultCountParts,
        appendPValue,
        removePValue,
        pValueFields.length,
        appendPEjector,
        removePEjector,
        pEjectorFields.length
    ]);

    useEffect(() => {
        const newDefaultCountParts = initialData?.p_values?.length || stock.count_parts || 2;
        reset({
            turbine_name: initialData?.turbine_name || turbine.name,
            valve_drawing: initialData?.valve_drawing || stock.name,
            valve_id: initialData?.valve_id || stock.id,
            temperature_start: initialData?.temperature_start != null ? String(initialData.temperature_start) : '',
            t_air: initialData?.t_air != null ? String(initialData.t_air) : '',
            count_valves: initialData?.count_valves || 3,
            count_parts_select: newDefaultCountParts,
            p_values:
                initialData?.p_values?.map(v => ({value: v != null ? String(v) : ''})) ||
                Array.from({length: newDefaultCountParts}, () => ({value: ''})),
            p_ejector:
                initialData?.p_ejector?.map(v => ({value: v != null ? String(v) : ''})) ||
                Array.from({length: newDefaultCountParts}, () => ({value: ''})),
        });
    }, [stock, turbine, initialData, reset]);

    const processSubmit: SubmitHandler<FormInputValues> = (data) => {
        const calculationParams: CalculationParams = {
            turbine_name: data.turbine_name,
            valve_drawing: data.valve_drawing,
            valve_id: data.valve_id,
            temperature_start: parseLocaleNumberStrict(data.temperature_start),
            t_air: parseLocaleNumberStrict(data.t_air),
            count_valves: data.count_valves,
            p_values: data.p_values.map(p => parseLocaleNumberStrict(p.value)),
            p_ejector: data.p_ejector.map(p => parseLocaleNumberStrict(p.value)),
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
            noValidate // отключаем нативную HTML-валидацию; валидируем через RHF
        >
            <Heading as="h2" size="lg" textAlign="center">
                Ввод данных для клапана <Text as="span" color="teal.500">{stock.name}</Text>
            </Heading>
            <Text textAlign="center" fontSize="md" color="gray.600">Турбина: {turbine.name}</Text>

            {onGoBack && (
                <Box width="100%" textAlign="center" my={2}>
                    <Button
                        onClick={onGoBack}
                        variant="outline"
                        colorScheme="teal"
                        size="sm"
                        leftIcon={<Icon as={FiChevronLeft}/>}
                    >
                        Изменить клапан
                    </Button>
                </Box>
            )}

            <input type="hidden" {...register("turbine_name")} />
            <input type="hidden" {...register("valve_drawing")} />
            <input type="hidden" {...register("valve_id")} />
            <input type="hidden" {...register("count_parts_select")} />

            {/* Количество клапанов: (целое число) */}
            <FormControl isRequired isInvalid={!!errors.count_valves}>
                <FormLabel htmlFor="count_valves">Количество клапанов:</FormLabel>
                <Controller
                    name="count_valves"
                    control={control}
                    rules={{required: "Это поле обязательно", min: {value: 1, message: "Минимум 1"}}}
                    render={({field}) => (
                        <NumberInput {...field} min={1}
                                     onChange={(_valueString, valueNumber) => field.onChange(valueNumber)}>
                            <NumberInputField placeholder="Введите количество" id="count_valves"/>
                            <NumberInputStepper>
                                <NumberIncrementStepper/>
                                <NumberDecrementStepper/>
                            </NumberInputStepper>
                        </NumberInput>
                    )}
                />
                <FormErrorMessage>{errors.count_valves?.message}</FormErrorMessage>
            </FormControl>

            {/* Входные давления: P1, P2, P3... */}
            <Box borderWidth="1px" borderRadius="md" p={4}>
                <Heading as="h3" size="md" mb={3}>Введите входные давления:</Heading>
                <VStack spacing={4} align="stretch">
                    {pValueFields.map((field, index) => (
                        <FormControl key={field.id} isRequired isInvalid={!!errors.p_values?.[index]?.value}>
                            <HStack align="center">
                                <FormLabel htmlFor={`p_values.${index}.value`} mb="0" minW="130px">
                                    Давление P{index + 1}:
                                </FormLabel>
                                <Controller
                                    name={`p_values.${index}.value`}
                                    control={control}
                                    rules={{
                                        required: "Это поле обязательно",
                                        validate: (value) =>
                                            isValidDecimal(value) ||
                                            `Введите корректное число (например: 113,292 или 113.292; не более ${MAX_SCALE} знаков после запятой)`,
                                    }}
                                    render={({field: {onChange, onBlur, value, name, ref}}) => (
                                        <Input
                                            id={name}
                                            type="text"
                                            inputMode="decimal"
                                            value={value ?? ''}
                                            onChange={(e) => onChange(e.target.value)}
                                            onBlur={onBlur}
                                            name={name}
                                            ref={ref}
                                            placeholder={`P${index + 1}`}
                                        />
                                    )}
                                />
                            </HStack>
                            <FormErrorMessage ml="140px">{errors.p_values?.[index]?.value?.message}</FormErrorMessage>
                        </FormControl>
                    ))}
                </VStack>
            </Box>

            {/* Выходные давления: Потребитель 1, 2, 3... */}
            <Box borderWidth="1px" borderRadius="md" p={4}>
                <Heading as="h3" size="md" mb={3}>Введите выходные давления:</Heading>
                <VStack spacing={4} align="stretch">
                    {pEjectorFields.map((field, index) => (
                        <FormControl key={field.id} isRequired isInvalid={!!errors.p_ejector?.[index]?.value}>
                            <HStack align="center">
                                <FormLabel htmlFor={`p_ejector.${index}.value`} mb="0" minW="130px">
                                    Потребитель {index + 1}:
                                </FormLabel>
                                <Controller
                                    name={`p_ejector.${index}.value`}
                                    control={control}
                                    rules={{
                                        required: "Это поле обязательно",
                                        validate: (value) =>
                                            isValidDecimal(value) ||
                                            `Введите корректное число (например: 113,292 или 113.292; не более ${MAX_SCALE} знаков после запятой)`,
                                    }}
                                    render={({field: {onChange, onBlur, value, name, ref}}) => (
                                        <Input
                                            id={name}
                                            type="text"
                                            inputMode="decimal"
                                            value={value ?? ''}
                                            onChange={(e) => onChange(e.target.value)}
                                            onBlur={onBlur}
                                            name={name}
                                            ref={ref}
                                            placeholder={`Потребитель ${index + 1}`}
                                        />
                                    )}
                                />
                            </HStack>
                            <FormErrorMessage ml="140px">{errors.p_ejector?.[index]?.value?.message}</FormErrorMessage>
                        </FormControl>
                    ))}
                </VStack>
            </Box>

            {/* Температуры */}
            <Box borderWidth="1px" borderRadius="md" p={4}>
                <Heading as="h3" size="md" mb={3}>Введите температурные значения:</Heading>
                <VStack spacing={4} align="stretch">
                    <FormControl isRequired isInvalid={!!errors.temperature_start}>
                        <HStack align="center">
                            <FormLabel htmlFor="temperature_start" mb="0" minW="180px">
                                Начальная температура (°C):
                            </FormLabel>
                            <Controller
                                name="temperature_start"
                                control={control}
                                rules={{
                                    required: "Это поле обязательно",
                                    validate: (value) =>
                                        isValidDecimal(value) ||
                                        `Введите корректное число (например: 113,292 или 113.292; не более ${MAX_SCALE} знаков после запятой)`,
                                }}
                                render={({field}) => (
                                    <Input
                                        id="temperature_start"
                                        type="text"
                                        inputMode="decimal"
                                        value={field.value ?? ''}
                                        onChange={(e) => field.onChange(e.target.value)}
                                        onBlur={field.onBlur}
                                        name={field.name}
                                        ref={field.ref}
                                        placeholder="Начальная температура"
                                    />
                                )}
                            />
                        </HStack>
                        <FormErrorMessage ml="190px">{errors.temperature_start?.message}</FormErrorMessage>
                    </FormControl>

                    <FormControl isRequired isInvalid={!!errors.t_air}>
                        <HStack align="center">
                            <FormLabel htmlFor="t_air" mb="0" minW="180px">
                                Температура воздуха (°C):
                            </FormLabel>
                            <Controller
                                name="t_air"
                                control={control}
                                rules={{
                                    required: "Это поле обязательно",
                                    validate: (value) =>
                                        isValidDecimal(value) ||
                                        `Введите корректное число (например: 113,292 или 113.292; не более ${MAX_SCALE} знаков после запятой)`,
                                }}
                                render={({field}) => (
                                    <Input
                                        id="t_air"
                                        type="text"
                                        inputMode="decimal"
                                        value={field.value ?? ''}
                                        onChange={(e) => field.onChange(e.target.value)}
                                        onBlur={field.onBlur}
                                        name={field.name}
                                        ref={field.ref}
                                        placeholder="Температура воздуха"
                                    />
                                )}
                            />
                        </HStack>
                        <FormErrorMessage ml="190px">{errors.t_air?.message}</FormErrorMessage>
                    </FormControl>
                </VStack>
            </Box>

            <Button type="submit" colorScheme="teal" isLoading={isSubmitting} size="lg" mt={4} width="full">
                Отправить
            </Button>
        </VStack>
    );
};

export default StockInputPage;