import React from 'react';
import {
    Flex,
    Input,
    Select,
    InputProps,
    useColorModeValue
} from '@chakra-ui/react';

interface InputWithUnitProps extends Omit<InputProps, 'value' | 'onChange'> {
    value: string | number;
    unit: string;
    availableUnits: string[];
    onValueChange: (val: string) => void;
    onUnitChange: (unit: string) => void;
    isDisabled?: boolean;
    name?: string;
    onBlur?: () => void;
}

export const InputWithUnit: React.FC<InputWithUnitProps> = ({
    value,
    unit,
    availableUnits,
    onValueChange,
    onUnitChange,
    isDisabled,
    name,
    onBlur,
    ...props
}) => {
    // Явно задаем цвета для светлой и темной тем
    const inputBg = useColorModeValue('white', 'gray.800');
    const selectBg = useColorModeValue('gray.50', 'gray.700');
    const borderColor = useColorModeValue('gray.200', 'gray.600');
    const hoverBorder = useColorModeValue('gray.300', 'gray.500');
    const optionBg = useColorModeValue('white', 'gray.700'); // Фон для выпадающего списка

    return (
        <Flex w="100%">
            <Input
                flex={1}
                name={name}
                onBlur={onBlur}
                value={value ?? ''}
                onChange={(e) => onValueChange(e.target.value)}
                isDisabled={isDisabled}
                borderRightRadius={0}
                bg={inputBg}
                borderColor={borderColor}
                _hover={{ borderColor: hoverBorder }}
                _focus={{ zIndex: 1, borderColor: "teal.500", boxShadow: "0 0 0 1px var(--chakra-colors-teal-500)" }}
                {...props}
            />
            <Select
                value={unit}
                onChange={(e) => onUnitChange(e.target.value)}
                isDisabled={isDisabled}
                borderLeftRadius={0}
                w="fit-content"
                minW="110px"
                bg={selectBg}
                borderColor={borderColor}
                ml="-1px"
                _hover={{ borderColor: hoverBorder }}
                _focus={{ zIndex: 2, borderColor: "teal.500", boxShadow: "0 0 0 1px var(--chakra-colors-teal-500)" }}
            >
                {availableUnits.map((u) => (
                    <option key={u} value={u} style={{ background: optionBg }}>
                        {u}
                    </option>
                ))}
            </Select>
        </Flex>
    );
};