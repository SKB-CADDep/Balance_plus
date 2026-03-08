// frontend/src/components/Calculator/StockInputPage.tsx
import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
    Box, Button, FormControl, FormLabel, VStack, HStack,
    Heading, Text, Icon, SimpleGrid, useColorModeValue,
} from '@chakra-ui/react';
import { FiChevronLeft, FiInfo } from "react-icons/fi";
import { type TurbineInfo } from '../../client';
import { InputWithUnit } from '../Common/InputWithUnit';
import { type SelectedStock } from './StockSelection';

type Props = {
    selectedStocks: SelectedStock[];
    turbine: TurbineInfo;
    onSubmit: (payload: any) => void;
    onGoBack: () => void;
};

const StockInputPage: React.FC<Props> = ({ selectedStocks, turbine, onSubmit, onGoBack }) => {
    const boxBg = useColorModeValue('gray.50', 'gray.700');
    const pressureUnits = ["кгс/см²", "МПа"];
    const tempUnits = ["°C"];

    // Инициализация дефолтных значений формы
    const defaultGroups = selectedStocks.map(s => {
        const intermediateCount = Math.max(0, (s.valve.count_parts || 3) - 2);
        return { intermediates: Array(intermediateCount).fill({ value: '', unit: 'кгс/см²' }) };
    });

    const { handleSubmit, control, watch, setValue, formState: {} } = useForm({
        defaultValues: {
            globals: {
                p_fresh: '', p_fresh_unit: 'кгс/см²',
                t_fresh: '', t_fresh_unit: '°C',
                p_air: '1.033', p_air_unit: 'кгс/см²',
                t_air: '40', t_air_unit: '°C',
                p_lst_leak_off: '0.97', p_lst_leak_off_unit: 'кгс/см²'
            },
            groups: defaultGroups
        }
    });

    const processSubmit = (data: any) => {
        const payload = {
            turbine_id: turbine.id,
            globals: {
                P_fresh: Number(data.globals.p_fresh), P_fresh_unit: data.globals.p_fresh_unit,
                T_fresh: Number(data.globals.t_fresh), T_fresh_unit: data.globals.t_fresh_unit,
                P_air: Number(data.globals.p_air), P_air_unit: data.globals.p_air_unit,
                T_air: Number(data.globals.t_air), T_air_unit: data.globals.t_air_unit,
                P_lst_leak_off: Number(data.globals.p_lst_leak_off), P_lst_leak_off_unit: data.globals.p_lst_leak_off_unit,
            },
            groups: selectedStocks.map((stock, i) => {
                const intermediates = (data.groups[i]?.intermediates || []).map((x: any) => Number(x.value));
                // Собираем точный массив P по всем участкам, как ожидает движок: [Свежий_пар, ...отсосы, Воздух]
                const p_values = [Number(data.globals.p_fresh), ...intermediates, Number(data.globals.p_air)];
                
                return {
                    valve_id: stock.valve.id,
                    type: stock.valve.type || "Неизвестно",
                    valve_names: [stock.valve.name],
                    quantity: stock.quantity,
                    p_values: p_values,
                    p_values_unit: data.globals.p_fresh_unit,
                    p_leak_offs: intermediates,
                    p_leak_offs_unit: data.globals.p_fresh_unit
                };
            })
        };
        onSubmit(payload);
    };

    return (
        <VStack as="form" onSubmit={handleSubmit(processSubmit)} spacing={6} p={5} w="100%" maxW="container.lg" mx="auto" align="stretch">
            <Heading as="h2" size="lg" textAlign="center">
                Ввод параметров расчёта
            </Heading>
            <Text textAlign="center" fontSize="md" color="gray.600">
                Турбина: {turbine.name} | Выбрано клапанов: {selectedStocks.length}
            </Text>

            <Box width="100%" textAlign="center" my={2}>
                <Button onClick={onGoBack} variant="outline" colorScheme="teal" size="sm" leftIcon={<Icon as={FiChevronLeft} />}>
                    Изменить состав клапанов
                </Button>
            </Box>

            {/* ГЛОБАЛЬНЫЕ ПАРАМЕТРЫ */}
            <Box borderWidth="1px" borderRadius="lg" p={5} bg={boxBg} shadow="sm">
                <HStack mb={4} align="center">
                    <Heading as="h3" size="md">Глобальные параметры</Heading>
                    <Icon as={FiInfo} color="teal.500" />
                </HStack>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    <FormControl isRequired>
                        <FormLabel>Давление свежего пара</FormLabel>
                        <Controller name="globals.p_fresh" control={control} rules={{ required: true }} render={({ field }) => (
                            <InputWithUnit value={field.value} unit={watch("globals.p_fresh_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={u => setValue("globals.p_fresh_unit", u)} />
                        )} />
                    </FormControl>

                    <FormControl isRequired>
                        <FormLabel>Температура свежего пара</FormLabel>
                        <Controller name="globals.t_fresh" control={control} rules={{ required: true }} render={({ field }) => (
                            <InputWithUnit value={field.value} unit={watch("globals.t_fresh_unit")} availableUnits={tempUnits} onValueChange={field.onChange} onUnitChange={u => setValue("globals.t_fresh_unit", u)} />
                        )} />
                    </FormControl>

                    <FormControl isRequired>
                        <FormLabel>Давление воздуха</FormLabel>
                        <Controller name="globals.p_air" control={control} rules={{ required: true }} render={({ field }) => (
                            <InputWithUnit value={field.value} unit={watch("globals.p_air_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={u => setValue("globals.p_air_unit", u)} />
                        )} />
                    </FormControl>

                    <FormControl isRequired>
                        <FormLabel>Температура воздуха</FormLabel>
                        <Controller name="globals.t_air" control={control} rules={{ required: true }} render={({ field }) => (
                            <InputWithUnit value={field.value} unit={watch("globals.t_air_unit")} availableUnits={tempUnits} onValueChange={field.onChange} onUnitChange={u => setValue("globals.t_air_unit", u)} />
                        )} />
                    </FormControl>

                    <FormControl isRequired gridColumn={{ md: "span 2" }}>
                        <FormLabel color="teal.600" fontWeight="bold">Давление последнего отсоса (Вакуум)</FormLabel>
                        <Controller name="globals.p_lst_leak_off" control={control} rules={{ required: true }} render={({ field }) => (
                            <InputWithUnit value={field.value} unit={watch("globals.p_lst_leak_off_unit")} availableUnits={pressureUnits} onValueChange={field.onChange} onUnitChange={u => setValue("globals.p_lst_leak_off_unit", u)} />
                        )} />
                    </FormControl>
                </SimpleGrid>
            </Box>

            {/* ПРОМЕЖУТОЧНЫЕ ОТСОСЫ (Рендерится динамически для каждого клапана) */}
            {selectedStocks.map((stockItem, idx) => {
                const intermediateCount = Math.max(0, (stockItem.valve.count_parts || 3) - 2);
                if (intermediateCount === 0) return null;

                return (
                    <Box key={stockItem.valve.id} borderWidth="1px" borderRadius="lg" p={5} bg="white" shadow="sm">
                        <Heading as="h3" size="sm" mb={4}>
                            Промежуточные отсосы: {stockItem.valve.name} ({stockItem.quantity} шт.)
                        </Heading>
                        <VStack spacing={4}>
                            {Array.from({ length: intermediateCount }).map((_, i) => (
                                <FormControl key={i} isRequired>
                                    <FormLabel>Давление в камере {i + 1}</FormLabel>
                                    <Controller
                                        name={`groups.${idx}.intermediates.${i}.value` as any}
                                        control={control}
                                        rules={{ required: true }}
                                        render={({ field }) => (
                                            <InputWithUnit
                                                value={field.value}
                                                unit={watch(`groups.${idx}.intermediates.${i}.unit` as any) || 'кгс/см²'}
                                                availableUnits={pressureUnits}
                                                onValueChange={field.onChange}
                                                onUnitChange={u => setValue(`groups.${idx}.intermediates.${i}.unit` as any, u)}
                                            />
                                        )}
                                    />
                                </FormControl>
                            ))}
                        </VStack>
                    </Box>
                );
            })}

            <Button type="submit" colorScheme="teal" size="lg" mt={4} height="60px" fontSize="xl">
                Рассчитать
            </Button>
        </VStack>
    );
};

export default StockInputPage;