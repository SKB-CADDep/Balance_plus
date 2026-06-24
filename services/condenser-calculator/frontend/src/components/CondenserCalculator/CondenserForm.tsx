import { useEffect, useMemo, useRef } from 'react';
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  Heading,
  Radio,
  RadioGroup,
  SimpleGrid,
  Stack,
  useColorModeValue,
} from '@chakra-ui/react';
import { Controller, useForm } from 'react-hook-form';
import { InputWithUnit } from '../Common/InputWithUnit';
import type { CondenserFormValues, CondenserMethod } from './types';

export type CondenserFormProps = {
  onSubmit: (values: CondenserFormValues) => void;
  isSubmitting?: boolean;
};

const DEFAULT_VALUES: CondenserFormValues = {
  method: 'berman',
  coefficient_b: '1',
  Z_ejectors: '1',
  X_steam: '0.950',

  G_steam: '',
  W_main: '',
  W_builtin: '',
  t1_main: '',
  t1_builtin: '',
  Z_main: '',
  Z_builtin: '',
  H_steam: '',

  G_steam_unit: 'т/ч',
  W_main_unit: 'т/ч',
  W_builtin_unit: 'т/ч',
  t1_main_unit: '°C',
  t1_builtin_unit: '°C',
  H_steam_unit: 'ккал/кг',
};

export function CondenserForm({ onSubmit, isSubmitting }: CondenserFormProps) {
  const cardBg = useColorModeValue('white', 'gray.800');
  const cardBorder = useColorModeValue('gray.200', 'gray.700');
  const sectionTitle = useColorModeValue('teal.700', 'teal.300');

  const disabledStyle = useMemo(() => ({ opacity: 0.5 }), []);

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    getValues,
    formState: { dirtyFields },
  } = useForm<CondenserFormValues>({
    defaultValues: DEFAULT_VALUES,
    mode: 'onChange',
  });

  const method = watch('method');
  const t1Main = watch('t1_main');
  const t1MainUnit = watch('t1_main_unit');

  // BR-04: синхронизация t1_main -> t1_builtin, пока пользователь не изменил t1_builtin вручную
  const t1BuiltinLockedRef = useRef(false);
  useEffect(() => {
    if (dirtyFields.t1_builtin || dirtyFields.t1_builtin_unit) t1BuiltinLockedRef.current = true;
  }, [dirtyFields.t1_builtin, dirtyFields.t1_builtin_unit]);

  useEffect(() => {
    if (!t1BuiltinLockedRef.current) {
      const current = getValues('t1_builtin');
      const currentUnit = getValues('t1_builtin_unit');
      if (current !== t1Main) setValue('t1_builtin', t1Main, { shouldDirty: false });
      if (currentUnit !== t1MainUnit) setValue('t1_builtin_unit', t1MainUnit, { shouldDirty: false });
    }
  }, [t1Main, t1MainUnit, getValues, setValue]);

  const isMetroVickers = method === 'metro-vickers';
  const isBerman = method === 'berman';

  const isDisabledT1 = false;
  const isDisabledBuiltin = isMetroVickers;
  const isDisabledXSteam = isBerman;

  return (
    <Box as="form" onSubmit={handleSubmit(onSubmit)}>
      <Stack spacing={6}>
        <Box p={5} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
          <Heading size="sm" mb={4} color={sectionTitle}>
            Глобальные
          </Heading>

          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={5}>
            <FormControl>
              <FormLabel>Методика расчета</FormLabel>
              <Controller
                control={control}
                name="method"
                render={({ field }) => (
                  <RadioGroup value={field.value} onChange={(v) => field.onChange(v as CondenserMethod)}>
                    <Stack direction="row" spacing={6}>
                      <Radio value="berman">Берман</Radio>
                      <Radio value="metro-vickers">Метро-Виккерс</Radio>
                    </Stack>
                  </RadioGroup>
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Коэфф. загрязнения (coefficient_b)</FormLabel>
              <Controller
                control={control}
                name="coefficient_b"
                render={({ field }) => (
                  <InputWithUnit
                    value={field.value}
                    unit="-"
                    availableUnits={['-']}
                    onValueChange={field.onChange}
                    onUnitChange={() => {}}
                    name={field.name}
                    onBlur={field.onBlur}
                    placeholder="Напр: 0.8 1.0 или 0.75-1-0.05"
                  />
                )}
              />
            </FormControl>
          </SimpleGrid>
        </Box>

        <Box p={5} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
          <Heading size="sm" mb={4} color={sectionTitle}>
            Пар
          </Heading>

          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={5}>
            <FormControl isRequired>
              <FormLabel>Расход пара (G_steam)</FormLabel>
              <Controller
                control={control}
                name="G_steam"
                rules={{ required: true }}
                render={({ field }) => (
                  <Controller
                    control={control}
                    name="G_steam_unit"
                    render={({ field: unitField }) => (
                      <InputWithUnit
                        value={field.value}
                        unit={unitField.value}
                        availableUnits={['т/ч', 'кг/с']}
                        onValueChange={field.onChange}
                        onUnitChange={unitField.onChange}
                        name={field.name}
                        onBlur={field.onBlur}
                        placeholder="Напр: 10-50-5 или 10 20 30"
                      />
                    )}
                  />
                )}
              />
            </FormControl>

            <FormControl isDisabled={isDisabledXSteam} {...(isDisabledXSteam ? disabledStyle : undefined)}>
              <FormLabel>Степень сухости (X_steam)</FormLabel>
              <Controller
                control={control}
                name="X_steam"
                render={({ field }) => (
                  <InputWithUnit
                    value={field.value}
                    unit="-"
                    availableUnits={['-']}
                    onValueChange={field.onChange}
                    onUnitChange={() => {}}
                    name={field.name}
                    onBlur={field.onBlur}
                    isDisabled={isDisabledXSteam}
                    placeholder="0.950"
                  />
                )}
              />
            </FormControl>

            <FormControl isDisabled={isMetroVickers} {...(isMetroVickers ? disabledStyle : undefined)}>
              <FormLabel>Энтальпия пара (H_steam)</FormLabel>
              <Controller
                control={control}
                name="H_steam"
                render={({ field }) => (
                  <Controller
                    control={control}
                    name="H_steam_unit"
                    render={({ field: unitField }) => (
                      <InputWithUnit
                        value={field.value}
                        unit={unitField.value}
                        availableUnits={['ккал/кг', 'кДж/кг']}
                        onValueChange={field.onChange}
                        onUnitChange={unitField.onChange}
                        name={field.name}
                        onBlur={field.onBlur}
                        isDisabled={isMetroVickers}
                        placeholder="Напр: 560"
                      />
                    )}
                  />
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Кол-во эжекторов (Z_ejectors)</FormLabel>
              <Controller
                control={control}
                name="Z_ejectors"
                render={({ field }) => (
                  <InputWithUnit
                    value={field.value}
                    unit="шт"
                    availableUnits={['шт']}
                    onValueChange={field.onChange}
                    onUnitChange={() => {}}
                    name={field.name}
                    onBlur={field.onBlur}
                    placeholder="1"
                  />
                )}
              />
            </FormControl>
          </SimpleGrid>
        </Box>

        <Box p={5} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
          <Heading size="sm" mb={4} color={sectionTitle}>
            Вода
          </Heading>

          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={8}>
            <Stack spacing={5}>
              <Heading as="h3" size="xs" color="gray.500">
                Основной пучок
              </Heading>
            <FormControl isRequired>
              <FormLabel>Расход воды (W_main)</FormLabel>
              <Controller
                control={control}
                name="W_main"
                rules={{ required: true }}
                render={({ field }) => (
                  <Controller
                    control={control}
                    name="W_main_unit"
                    render={({ field: unitField }) => (
                      <InputWithUnit
                        value={field.value}
                        unit={unitField.value}
                        availableUnits={['т/ч', 'кг/с', 'м3/ч', 'т/с']}
                        onValueChange={field.onChange}
                        onUnitChange={unitField.onChange}
                        name={field.name}
                        onBlur={field.onBlur}
                        placeholder="Напр: 4000 8000"
                      />
                    )}
                  />
                )}
              />
            </FormControl>

            <FormControl isRequired isDisabled={isDisabledT1} {...(isDisabledT1 ? disabledStyle : undefined)}>
              <FormLabel>Темп. воды вход (t1_main)</FormLabel>
              <Controller
                control={control}
                name="t1_main"
                rules={{ required: true }}
                render={({ field }) => (
                  <Controller
                    control={control}
                    name="t1_main_unit"
                    render={({ field: unitField }) => (
                      <InputWithUnit
                        value={field.value}
                        unit={unitField.value}
                        availableUnits={['°C', 'K']}
                        onValueChange={field.onChange}
                        onUnitChange={unitField.onChange}
                        name={field.name}
                        onBlur={field.onBlur}
                        isDisabled={isDisabledT1}
                        placeholder="Напр: 10 20"
                      />
                    )}
                  />
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Ходы воды (Z_main)</FormLabel>
              <Controller
                control={control}
                name="Z_main"
                render={({ field }) => (
                  <InputWithUnit
                    value={field.value}
                    unit="шт"
                    availableUnits={['шт']}
                    onValueChange={field.onChange}
                    onUnitChange={() => {}}
                    name={field.name}
                    onBlur={field.onBlur}
                    placeholder="Напр: 2"
                  />
                )}
              />
            </FormControl>

            </FormControl>
            </Stack>

            <Stack spacing={5}>
              <Heading as="h3" size="xs" color="gray.500">
                Встроенный пучок
              </Heading>

              <FormControl isDisabled={isDisabledBuiltin} {...(isDisabledBuiltin ? disabledStyle : undefined)}>
                <FormLabel>Расход воды (W_builtin)</FormLabel>
                <Controller
                  control={control}
                  name="W_builtin"
                  render={({ field }) => (
                    <Controller
                      control={control}
                      name="W_builtin_unit"
                      render={({ field: unitField }) => (
                        <InputWithUnit
                          value={field.value}
                          unit={unitField.value}
                          availableUnits={['т/ч', 'кг/с', 'м3/ч', 'т/с']}
                          onValueChange={field.onChange}
                          onUnitChange={unitField.onChange}
                          name={field.name}
                          onBlur={field.onBlur}
                          isDisabled={isDisabledBuiltin}
                          placeholder="Напр: 500 750"
                        />
                      )}
                    />
                  )}
                />
              </FormControl>

              <FormControl isDisabled={isDisabledBuiltin} {...(isDisabledBuiltin ? disabledStyle : undefined)}>
                <FormLabel>Темп. воды вход (t1_builtin)</FormLabel>
                <Controller
                  control={control}
                  name="t1_builtin"
                  render={({ field }) => (
                    <Controller
                      control={control}
                      name="t1_builtin_unit"
                      render={({ field: unitField }) => (
                        <InputWithUnit
                          value={field.value}
                          unit={unitField.value}
                          availableUnits={['°C', 'K']}
                          onValueChange={field.onChange}
                          onUnitChange={unitField.onChange}
                          name={field.name}
                          onBlur={field.onBlur}
                          isDisabled={isDisabledBuiltin}
                          placeholder="По умолчанию синхр. с t1_main"
                        />
                      )}
                    />
                  )}
                />
              </FormControl>

              <FormControl isDisabled={isDisabledBuiltin} {...(isDisabledBuiltin ? disabledStyle : undefined)}>
                <FormLabel>Ходы воды (Z_builtin)</FormLabel>
                <Controller
                  control={control}
                  name="Z_builtin"
                  render={({ field }) => (
                    <InputWithUnit
                      value={field.value}
                      unit="шт"
                      availableUnits={['шт']}
                      onValueChange={field.onChange}
                      onUnitChange={() => {}}
                      name={field.name}
                      onBlur={field.onBlur}
                      isDisabled={isDisabledBuiltin}
                      placeholder=""
                    />
                  )}
                />
              </FormControl>
            </Stack>
          </SimpleGrid>
        </Box>

        <Flex justify="flex-start">
          <Button colorScheme="teal" size="lg" type="submit" isLoading={isSubmitting}>
            Рассчитать
          </Button>
        </Flex>
      </Stack>
    </Box>
  );
}

