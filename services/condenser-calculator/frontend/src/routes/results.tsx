import { createFileRoute, useNavigate } from '@tanstack/react-router';
import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  useColorModeValue,
  useToast,
  VStack,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { useEffect, useState } from 'react';
import type { CalculationOutput } from '../client';
import { ResultMatrixViewer } from '../components/CondenserCalculator';
import { FiArrowLeft, FiCopy } from 'react-icons/fi';

export const Route = createFileRoute('/results')({
  component: ResultsPage,
});

function ResultsPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [result, setResult] = useState<CalculationOutput | null>(null);

  const cardBg = useColorModeValue('white', 'gray.800');
  const cardBorder = useColorModeValue('gray.200', 'gray.700');
  const preBg = useColorModeValue('gray.50', 'gray.900');

  useEffect(() => {
    const saved = sessionStorage.getItem('lastCalculationResult');
    if (saved) {
      try {
        setResult(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse result from sessionStorage', e);
      }
    }
  }, []);

  const copyJsonToClipboard = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2))
      .then(() => toast({ title: 'JSON скопирован', status: 'success', duration: 2000 }))
      .catch(() => toast({ title: 'Ошибка копирования', status: 'error' }));
  };

  if (!result) {
    return (
      <Container maxW="container.xl" py={8}>
        <Alert status="warning" mb={4}>
          <AlertIcon />
          Нет данных для отображения. Возможно, вы еще не запускали расчет.
        </Alert>
        <Button leftIcon={<FiArrowLeft />} onClick={() => navigate({ to: '/' })}>
          Вернуться на главную
        </Button>
      </Container>
    );
  }

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
          <Heading size="lg">Результаты: {result.condenser_name}</Heading>
          <Button leftIcon={<FiArrowLeft />} variant="outline" onClick={() => navigate({ to: '/calculator', search: { condenserId: result.condenser_id } })}>
            К калькулятору
          </Button>
        </Flex>

        <Box p={6} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
          <Flex gap={8} mb={6} flexWrap="wrap">
            <Box>
              <Text color="gray.500" fontSize="sm">Метод расчета</Text>
              <Text fontWeight="medium">{result.method === 'berman' ? 'Берман' : 'Метро-Виккерс'}</Text>
            </Box>
            <Box>
              <Text color="gray.500" fontSize="sm">Количество матриц</Text>
              <Text fontWeight="medium">{result.total_tables}</Text>
            </Box>
            <Box>
              <Text color="gray.500" fontSize="sm">Время расчета</Text>
              <Text fontWeight="medium">{(result.calculation_time_ms / 1000).toFixed(2)} с</Text>
            </Box>
          </Flex>

          <Tabs colorScheme="teal" variant="enclosed" isLazy>
            <TabList>
              <Tab>Таблицы (Матрицы)</Tab>
              <Tab>Сырой JSON</Tab>
            </TabList>

            <TabPanels>
              <TabPanel px={0} py={4}>
                <ResultMatrixViewer results={result.tables ?? []} />
              </TabPanel>

              <TabPanel px={0} py={4}>
                <Box position="relative">
                  <Button
                    size="sm"
                    position="absolute"
                    top={2}
                    right={4}
                    leftIcon={<FiCopy />}
                    onClick={copyJsonToClipboard}
                    colorScheme="gray"
                  >
                    Копировать
                  </Button>
                  <Box
                    as="pre"
                    p={4}
                    bg={preBg}
                    borderRadius="md"
                    borderWidth={1}
                    borderColor={cardBorder}
                    overflowX="auto"
                    fontSize="sm"
                    maxH="600px"
                    overflowY="auto"
                  >
                    {JSON.stringify(result, null, 2)}
                  </Box>
                </Box>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Box>
      </VStack>
    </Container>
  );
}

export default ResultsPage;
