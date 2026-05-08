import {
    Box,
    Container,
    Heading,
    Text,
    VStack,
    useColorModeValue,
    Divider,
    Stack,
    Tag,
    Wrap,
    WrapItem,
    Icon,
} from "@chakra-ui/react";
import {MdInfoOutline, MdCode, MdBusiness, MdPeople } from "react-icons/md"; // Иконки

function AboutPage() {
    const headingColor = useColorModeValue("gray.700", "whiteAlpha.900");
    const textColor = useColorModeValue("gray.600", "gray.400");
    const accentColor = "teal.500";

    const technologies = [
        "React", "TypeScript", "Vite", "Chakra UI", "TanStack Router",
        "TanStack Query", "React Hook Form", "FastAPI (Python)", "SQLAlchemy/SQLModel", "PostgreSQL", "Docker"
    ];

    return (
        <Container maxW="container.lg" py={{ base: 8, md: 12 }}>
            <VStack spacing={8} align="stretch">
                <Box textAlign="center">
                    <Icon as={MdInfoOutline} w={16} h={16} color={accentColor} mb={4} />
                    <Heading as="h1" size="2xl" color={headingColor} mb={2}>
                        О программе WSAPropertiesCalculator
                    </Heading>
                    <Text fontSize="lg" color={textColor}>
                        Детальная информация о нашем приложении для расчета параметров штоков паровых турбин.
                    </Text>
                </Box>

                <Divider />

                <Stack spacing={6}>
                    <Box>
                        <Heading as="h2" size="lg" color={headingColor} mb={3}>
                            <Icon as={MdBusiness} mr={2} verticalAlign="middle" /> Назначение
                        </Heading>
                        <Text fontSize="md" color={textColor} lineHeight="tall">
                            Программа <strong>WSAPropertiesCalculator</strong> предназначена для инженеров и специалистов
                            АО «Уральский турбинный завод», занимающихся проектированием и анализом паровых турбин.
                            Она позволяет производить точные расчеты параметров штоков на основе заданных входных данных,
                            учитывая различные режимы работы и конструктивные особенности.
                        </Text>
                        <Text fontSize="md" color={textColor} mt={3} lineHeight="tall">
                            Основная цель – автоматизация и ускорение процесса расчета, снижение вероятности ошибок
                            и предоставление удобного интерфейса для работы с результатами и их анализа.
                        </Text>
                    </Box>

                    <Box>
                        <Heading as="h2" size="lg" color={headingColor} mb={3}>
                            <Icon as={MdPeople} mr={2} verticalAlign="middle" /> Разработчики
                        </Heading>
                        <Text fontSize="md" color={textColor}>
                            Разработано командой отдела разработки из АО «Уральский турбинный завод».
                        </Text>
                        <Text fontSize="md" color={textColor}>
                            GitHubs: Misha-Mayskiy | LevShlyogin | D0k2
                        </Text>
                    </Box>

                    <Box>
                        <Heading as="h2" size="lg" color={headingColor} mb={3}>
                            <Icon as={MdCode} mr={2} verticalAlign="middle" /> Используемые технологии
                        </Heading>
                        <Text fontSize="md" color={textColor} mb={3}>
                            Приложение построено на современном стеке технологий, обеспечивающем производительность,
                            надежность и удобство разработки:
                        </Text>
                        <Wrap spacing={2}>
                            {technologies.map(tech => (
                                <WrapItem key={tech}>
                                    <Tag size="md" variant="subtle" colorScheme="teal">
                                        {tech}
                                    </Tag>
                                </WrapItem>
                            ))}
                        </Wrap>
                    </Box>
                </Stack>
            </VStack>
        </Container>
    );
}

export default AboutPage;