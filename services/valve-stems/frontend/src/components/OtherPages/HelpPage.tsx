import {
    Box,
    Container,
    Heading,
    Text,
    VStack,
    Accordion,
    AccordionItem,
    AccordionButton,
    AccordionPanel,
    AccordionIcon,
    useColorModeValue,
    Icon,
    Divider,
} from "@chakra-ui/react";
import {MdHelpOutline, MdQuestionAnswer, MdContactSupport} from "react-icons/md";

const faqData = [
    {
        question: "Как начать новый расчет?",
        answer: "Для начала нового расчета перейдите на страницу 'Калькулятор' из главного меню. Если вы уже на ней, выберите турбину, затем клапан (шток). Если для данного штока есть предыдущие расчеты, вам будет предложено использовать их или начать новый. Для нового расчета нажмите 'Да' (пересчитать) или выберите шток, для которого нет предыдущих расчетов. Затем заполните все необходимые входные параметры на странице ввода данных и нажмите кнопку 'Отправить на расчет'.",
    },
    {
        question: "Где я могу найти результаты предыдущих расчетов?",
        answer: "После выбора турбины и штока, если для данного штока существуют сохраненные расчеты, вам будет показана страница 'Обнаружен предыдущий расчет'. На ней будут отображены входные и выходные данные последнего расчета. Вы можете либо использовать эти данные (нажав 'Нет' на вопрос о перерасчете), либо начать новый расчет.",
    },
    {
        question: "Как сохранить результаты расчета в Excel?",
        answer: "На странице результатов расчета (после его выполнения или просмотра предыдущего) найдите кнопку 'Сохранить в виде Excel'. Нажмите на нее, и файл с результатами будет автоматически загружен на ваш компьютер.",
    },
    {
        question: "Что означают различные параметры на странице ввода/вывода?",
        answer: "Детальное описание каждого параметра, его физический смысл и единицы измерения должны быть приведены во внутренней технической документации или могут быть уточнены у ответственных инженеров. Эта программа является инструментом для автоматизации уже известных методик расчета.",
    },
    {
        question: "Что делать, если я обнаружил ошибку в расчетах или работе программы?",
        answer: "Пожалуйста, сообщите об ошибке команде разработки или ответственному лицу в вашем отделе, предоставив как можно больше деталей: какие данные вы вводили, какие результаты получили, текст ошибки (если есть), и шаги для воспроизведения проблемы.",
    },
    {
        question: "Могу ли я изменить данные уже выполненного расчета?",
        answer: "Текущая версия программы не поддерживает прямое редактирование уже сохраненных результатов. Чтобы получить другие результаты, вам необходимо выполнить новый расчет с измененными входными параметрами.",
    }
];


function HelpPage() {
    const headingColor = useColorModeValue("gray.700", "whiteAlpha.900");
    const textColor = useColorModeValue("gray.700", "gray.300");
    const panelBg = useColorModeValue("gray.50", "gray.700");
    const accordionItemBorderColor = useColorModeValue("gray.200", "gray.600");

    return (
        <Container maxW="container.lg" py={{base: 8, md: 12}}>
            <VStack spacing={8} align="stretch">
                <Box textAlign="center">
                    <Icon as={MdHelpOutline} w={16} h={16} color="teal.500" mb={4}/>
                    <Heading as="h1" size="2xl" color={headingColor} mb={2}>
                        Помощь и Ответы на Вопросы
                    </Heading>
                    <Text fontSize="lg" color={useColorModeValue("gray.600", "gray.400")}>
                        Здесь вы найдете ответы на часто задаваемые вопросы по работе с WSAPropertiesCalculator.
                    </Text>
                </Box>

                <Accordion allowMultiple defaultIndex={[0]}>
                    {faqData.map((faq, index) => (
                        <AccordionItem
                            key={index}
                            mb={3}
                            borderWidth="1px"
                            borderColor={accordionItemBorderColor}
                            borderRadius="lg"
                            overflow="hidden"
                        >
                            <h2>
                                <AccordionButton
                                    _expanded={{bg: "teal.500", color: "white"}}
                                    py={3}
                                    px={4}
                                >
                                    <Box flex="1" textAlign="left" fontWeight="semibold" fontSize="lg">
                                        <Icon as={MdQuestionAnswer} mr={2} verticalAlign="middle"/> {faq.question}
                                    </Box>
                                    <AccordionIcon/>
                                </AccordionButton>
                            </h2>
                            <AccordionPanel
                                pb={4}
                                pt={3}
                                px={4}
                                bg={panelBg}
                                color={textColor}
                                lineHeight="tall"
                            >
                                {faq.answer}
                            </AccordionPanel>
                        </AccordionItem>
                    ))}
                </Accordion>

                <Divider my={6}/>

                <Box textAlign="center">
                    <Heading as="h2" size="lg" color={headingColor} mb={3}>
                        <Icon as={MdContactSupport} mr={2} verticalAlign="middle"/> Не нашли ответ?
                    </Heading>
                    <Text fontSize="md" color={textColor}>
                        Если у вас остались вопросы или возникли проблемы, пожалуйста, обратитесь
                        к внутренней документации или к команде поддержки.
                    </Text>
                </Box>

            </VStack>
        </Container>
    );
}

export default HelpPage;