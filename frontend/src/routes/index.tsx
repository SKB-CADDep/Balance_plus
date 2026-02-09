import {
    Container,
    Heading,
    Text,
    VStack,
    Button,
    Icon,
    SimpleGrid,
    useColorModeValue,
    Divider,
    Flex,
} from "@chakra-ui/react";
import {createFileRoute, Link as RouterLink} from "@tanstack/react-router";
import {FiArrowRight, FiZap, FiHelpCircle, FiInfo, FiCode} from "react-icons/fi";
import React from "react";

const FeatureCard = ({title, description, icon, to, buttonText}: {
    title: string,
    description: string,
    icon: React.ElementType,
    to: string,
    buttonText: string
}) => {
    const cardBg = useColorModeValue("white", "gray.700");
    const borderColor = useColorModeValue("gray.200", "gray.600");

    return (
        <VStack
            bg={cardBg}
            p={6}
            spacing={4}
            borderRadius="lg"
            borderWidth="1px"
            borderColor={borderColor}
            alignItems="flex-start"
            boxShadow="md"
            transition="all 0.2s ease-in-out"
            _hover={{boxShadow: "lg", transform: "translateY(-4px)"}}
        >
            <Flex
                w={12}
                h={12}
                align="center"
                justify="center"
                borderRadius="full"
                bg={useColorModeValue("teal.50", "teal.900")}
                mb={1}
            >
                <Icon as={icon} w={6} h={6} color="teal.500"/>
            </Flex>
            <Heading as="h3" size="md">{title}</Heading>
            <Text color={useColorModeValue("gray.600", "gray.400")} flexGrow={1}>
                {description}
            </Text>
            <Button
                as={RouterLink}
                to={to}
                rightIcon={<Icon as={FiArrowRight}/>}
                colorScheme="teal"
                variant="solid"
                alignSelf="flex-start"
            >
                {buttonText}
            </Button>
        </VStack>
    );
};


function DashboardPage() {
    const headingColor = useColorModeValue("gray.700", "whiteAlpha.900");
    const textColor = useColorModeValue("gray.600", "gray.300");

    return (
        <Container maxW="container.xl" py={{base: 8, md: 12}}>
            <VStack spacing={{base: 6, md: 10}} textAlign="center">
                <Heading
                    as="h1"
                    fontSize={{base: "3xl", sm: "4xl", md: "5xl"}}
                    fontWeight="bold"
                    color={headingColor}
                    lineHeight="1.2"
                >
                    Добро пожаловать в{" "}
                    <Text as="span" color="teal.400">
                        WSAPropertiesCalculator
                    </Text>
                </Heading>
                <Text fontSize={{base: "lg", md: "xl"}} color={textColor} maxW="2xl">
                    Ваш надежный инструмент для точного и быстрого расчета параметров паровых турбин и их штоков,
                    разработанный на АО «Уральский турбинный завод».
                </Text>
                <Button
                    as={RouterLink}
                    to="/calculator"
                    colorScheme="teal"
                    size="lg"
                    rightIcon={<Icon as={FiZap}/>}
                    px={8}
                    py={6}
                    fontSize="lg"
                >
                    Начать расчет
                </Button>
            </VStack>

            <Divider my={{base: 10, md: 16}}/>

            <VStack spacing={8} align="stretch">
                <Heading as="h2" size="xl" textAlign="center" color={headingColor}>
                    Основные возможности
                </Heading>
                <SimpleGrid columns={{base: 1, md: 2, lg: 3}} spacing={8} mt={4}>
                    <FeatureCard
                        icon={FiCode}
                        title="Калькулятор Штоков"
                        description="Производите детальные расчеты параметров штоков паровых турбин с учетом множества входных данных."
                        to="/calculator"
                        buttonText="К калькулятору"
                    />
                    <FeatureCard
                        icon={FiInfo}
                        title="О Программе"
                        description="Узнайте больше о назначении программы, ее разработчиках и используемых технологиях."
                        to="/about"
                        buttonText="Подробнее"
                    />
                    <FeatureCard
                        icon={FiHelpCircle}
                        title="Раздел Помощи"
                        description="Найдите ответы на часто задаваемые вопросы и инструкции по использованию калькулятора."
                        to="/help"
                        buttonText="Перейти в Помощь"
                    />
                </SimpleGrid>
            </VStack>
        </Container>
    );
}

export const Route = createFileRoute('/')({
    component: DashboardPage,
});