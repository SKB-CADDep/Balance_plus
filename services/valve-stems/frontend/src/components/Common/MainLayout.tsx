import {
    Box,
    Flex,
    Image,
    Text,
    Link as ChakraLink,
    Icon,
    HStack,
    useColorModeValue,
    useDisclosure,
    IconButton,
    Stack,
} from '@chakra-ui/react';
import {Outlet, Link as RouterLink} from '@tanstack/react-router';
import {FiGrid, FiCode, FiHelpCircle, FiInfo, FiClock} from 'react-icons/fi';

import SidebarComponent from './Sidebar';
import {ThemeToggleButton} from './ThemeToggleButton';

export default function MainLayout() {
    const headerBg = useColorModeValue('white', 'gray.800');
    const headerBorderColor = useColorModeValue('gray.200', 'gray.700');
    const footerBg = useColorModeValue('gray.50', 'gray.900');
    const linkColor = useColorModeValue('gray.600', 'gray.200');
    const activeLinkColor = useColorModeValue('teal.500', 'teal.300');
    const activeLinkBg = useColorModeValue('teal.50', 'gray.700');

    const navLinks = [
        {to: "/", label: "Главная", icon: FiGrid},
        {to: "/calculator", label: "Калькулятор", icon: FiCode},
        {to: "/about", label: "О программе", icon: FiInfo},
        {to: "/help", label: "Помощь", icon: FiHelpCircle},
    ];

    const {isOpen: isSidebarOpen, onOpen: onSidebarOpen, onClose: onSidebarClose} = useDisclosure();
    const headerHeight = "65px";

    return (
        <Flex direction="column" minH="100vh">
            <Flex
                as="header"
                align="center"
                justify="space-between"
                py={3}
                px={4}
                bg={headerBg}
                borderBottomWidth="1px"
                borderColor={headerBorderColor}
                boxShadow="sm"
                wrap="wrap"
                position="fixed"
                top={0}
                left={0}
                right={0}
                zIndex="sticky"
                h={headerHeight}
            >

                <Flex align="center" as={RouterLink} to="/" _hover={{textDecoration: 'none'}}>
                    <Image src="/logo.png" alt="WSA Logo" boxSize="36px" mr={2}/>
                    <Text fontSize={{base: "md", md: "lg"}} fontWeight="bold"
                          color={useColorModeValue('gray.700', 'white')}>
                        WSAPropertiesCalculator
                    </Text>
                </Flex>

                <Stack direction="row" spacing={{base: 1, md: 3}} align="center" ml="auto">
                    <IconButton
                        aria-label="Открыть историю расчетов"
                        icon={<Icon as={FiClock} boxSize={5}/>}
                        variant="ghost"
                        onClick={onSidebarOpen}
                        display={{base: 'flex'}}
                    />
                    <HStack as="nav" spacing={{base: 1, md: 3}}>
                        {navLinks.map(link => (
                            <ChakraLink
                                key={link.to}
                                as={RouterLink}
                                to={link.to}
                                display="flex"
                                alignItems="center"
                                p={2}
                                borderRadius="md"
                                fontWeight="medium"
                                color={linkColor}
                                _hover={{
                                    textDecoration: 'none',
                                    bg: useColorModeValue('gray.100', 'gray.700'),
                                    color: activeLinkColor,
                                }}
                                activeProps={{
                                    style: {
                                        fontWeight: 'bold',
                                        color: activeLinkColor,
                                        backgroundColor: activeLinkBg,
                                    }
                                }}
                            >
                                <Icon as={link.icon} mr={{base: 0, md: 1}}
                                      boxSize={link.label === "Калькулятор" ? 4 : 5}/>
                                <Text display={{base: 'none', md: 'inline'}} fontSize="sm">{link.label}</Text>
                            </ChakraLink>
                        ))}
                    </HStack>
                    <ThemeToggleButton/>
                </Stack>
            </Flex>

            <Flex
                flex="1"
                pt={headerHeight}
            >
                <SidebarComponent isOpen={isSidebarOpen} onClose={onSidebarClose}/>

                <Box
                    flex="1"
                    p={{base: 4, md: 6}}
                    as="main"
                    overflowY="auto"
                >
                    <Outlet/>
                </Box>
            </Flex>

            <Box
                as="footer"
                bg={footerBg}
                py={3}
                px={6}
                textAlign="center"
                borderTopWidth="1px"
                borderColor={headerBorderColor}
            >
                <Text fontSize="xs" color={useColorModeValue('gray.600', 'gray.400')}>
                    © WSAPropertiesCalculator. АО «Уральский турбинный завод», 2024-2025.
                </Text>
            </Box>
        </Flex>
    );
}