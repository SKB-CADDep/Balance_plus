import {IconButton, useColorMode, useColorModeValue, Tooltip} from '@chakra-ui/react';
import {FaMoon, FaSun} from 'react-icons/fa';

export const ThemeToggleButton = () => {
    const {toggleColorMode} = useColorMode();
    const SwitchIcon = useColorModeValue(FaMoon, FaSun);
    const nextMode = useColorModeValue('темную', 'светлую');
    const buttonLabel = `Переключить на ${nextMode} тему`;

    return (
        <Tooltip label={buttonLabel} placement="bottom" openDelay={500}>
            <IconButton
                size="md"
                fontSize="lg"
                aria-label={buttonLabel}
                variant="ghost"
                color="current"
                onClick={toggleColorMode}
                icon={<SwitchIcon/>}
                ml={2}
            />
        </Tooltip>
    );
};