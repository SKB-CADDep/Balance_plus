import {
    Drawer,
    DrawerBody,
    DrawerCloseButton,
    DrawerContent,
    DrawerOverlay,
    Flex,
    Text,
    Heading,
    useColorModeValue,
    Divider,
    Button,
    VStack,
    HStack,
    Tooltip,
    Icon,
    IconButton,
    Box,
} from "@chakra-ui/react";
import {FiTrash, FiClock, FiChevronRight} from "react-icons/fi";
import {useNavigate} from '@tanstack/react-router';
import React, {useState, useEffect, useCallback} from 'react';

export interface HistoryEntry {
    id: string;
    stockName: string;
    stockId: number;
    turbineName: string;
    turbineId: number;
    timestamp: number;
}

export const LOCAL_STORAGE_HISTORY_KEY = 'wsaCalculatorHistory';

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({isOpen, onClose}) => {
    const sidebarInnerBg = useColorModeValue("ui.secondary", "ui.darkSlate");
    const borderColor = useColorModeValue("gray.200", "gray.700");
    const textColor = useColorModeValue("gray.800", "whiteAlpha.900");
    const secondaryTextColor = useColorModeValue("gray.600", "gray.400");
    const hoverBg = useColorModeValue("gray.200", "gray.600");

    const navigate = useNavigate();
    const [history, setHistory] = useState<HistoryEntry[]>([]);

    const refreshHistoryFromStorage = useCallback(() => {
        const storedHistory = localStorage.getItem(LOCAL_STORAGE_HISTORY_KEY);
        if (storedHistory) {
            try {
                setHistory(JSON.parse(storedHistory));
            } catch (e) {
                console.error("Failed to parse history from localStorage", e);
                localStorage.removeItem(LOCAL_STORAGE_HISTORY_KEY);
                setHistory([]);
            }
        } else {
            setHistory([]);
        }
    }, []);

    useEffect(() => {
        refreshHistoryFromStorage();
        const handleHistoryUpdate = () => {
            refreshHistoryFromStorage();
        };
        window.addEventListener('wsaHistoryUpdated', handleHistoryUpdate);
        return () => {
            window.removeEventListener('wsaHistoryUpdated', handleHistoryUpdate);
        };
    }, [refreshHistoryFromStorage]);

    const handleClearHistory = useCallback(() => {
        setHistory([]);
        localStorage.removeItem(LOCAL_STORAGE_HISTORY_KEY);
    }, []);

    const handleRemoveHistoryEntry = useCallback((idToRemove: string) => {
        setHistory(prevHistory => {
            const updated = prevHistory.filter(entry => entry.id !== idToRemove);
            localStorage.setItem(LOCAL_STORAGE_HISTORY_KEY, JSON.stringify(updated));
            return updated;
        });
    }, []);

    const handleHistoryEntryClick = (entry: HistoryEntry) => {
        navigate({
            to: '/calculator',
            search: (prev: any) => ({
                ...prev,
                resultId: entry.id,
                stockIdToLoad: String(entry.stockId),
                turbineIdToLoad: String(entry.turbineId)
            }),
        }).then();
        onClose();
    };


    const sidebarContent = (
        <Flex direction="column" h="full">
            <Flex
                align="center"
                p={4}
                justifyContent="space-between"
            >
                <HStack spacing={2}>
                    <Icon as={FiClock} boxSize={6} color="teal.400"/>
                    <Heading size="md" color={textColor}>История</Heading>
                </HStack>
                <DrawerCloseButton position="static"
                                   color={textColor}/>
            </Flex>
            <Divider borderColor={borderColor}/>

            {history.length === 0 ? (
                <Text p={6} color={secondaryTextColor} textAlign="center" flex="1" display="flex" alignItems="center"
                      justifyContent="center">
                    История расчетов пуста.
                </Text>
            ) : (
                <VStack
                    spacing={0}
                    align="stretch"
                    p={2}
                    overflowY="auto"
                    flex="1"
                >
                    {history
                        .sort((a, b) => b.timestamp - a.timestamp)
                        .map((entry) => (
                            <Box
                                key={entry.id}
                                role="button"
                                tabIndex={0}
                                textAlign="left"
                                w="full"
                                p={3}
                                borderRadius="md"
                                bg="transparent"
                                _hover={{bg: hoverBg, textDecoration: 'none', cursor: 'pointer'}}
                                _focus={{boxShadow: 'outline', borderColor: 'teal.300', bg: hoverBg}}
                                onClick={() => handleHistoryEntryClick(entry)}
                            >
                                <HStack justify="space-between" align="center">
                                    <VStack align="flex-start" spacing={0}>
                                        <Text fontWeight="semibold" color={textColor} fontSize="sm" noOfLines={1}
                                              title={entry.stockName}>
                                            {entry.stockName}
                                        </Text>
                                        <Text fontSize="xs" color={secondaryTextColor} noOfLines={1}
                                              title={entry.turbineName}>
                                            {entry.turbineName}
                                        </Text>
                                        <Text fontSize="xs" color={secondaryTextColor}>
                                            {new Date(entry.timestamp).toLocaleDateString()} {new Date(entry.timestamp).toLocaleTimeString([], {
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                        </Text>
                                    </VStack>
                                    <HStack spacing={1}>
                                        <Tooltip label="Удалить" placement="top" openDelay={300}>
                                            <IconButton
                                                aria-label="Удалить запись"
                                                icon={<FiTrash/>}
                                                size="xs"
                                                variant="ghost"
                                                colorScheme="red"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleRemoveHistoryEntry(entry.id);
                                                }}
                                            />
                                        </Tooltip>
                                        <Icon as={FiChevronRight} color={secondaryTextColor}/>
                                    </HStack>
                                </HStack>
                            </Box>
                        ))}
                </VStack>
            )}

            {history.length > 0 && (
                <Box p={3} borderTopWidth="1px" borderColor={borderColor}>
                    <Button
                        leftIcon={<Icon as={FiTrash}/>}
                        colorScheme="red"
                        variant="ghost"
                        onClick={handleClearHistory}
                        width="full"
                        size="sm"
                        color={secondaryTextColor}
                        _hover={{
                            bg: useColorModeValue("red.50", "red.900"),
                            color: useColorModeValue("red.600", "red.300")
                        }}
                    >
                        Очистить всю историю
                    </Button>
                </Box>
            )}
        </Flex>
    );

    return (
        <Drawer isOpen={isOpen} placement="left" onClose={onClose} size="md">
            <DrawerOverlay/>
            <DrawerContent bg={sidebarInnerBg}
                           pt={0}>
                <DrawerBody p={0}>
                    {sidebarContent}
                </DrawerBody>
            </DrawerContent>
        </Drawer>
    );
};


export default Sidebar;