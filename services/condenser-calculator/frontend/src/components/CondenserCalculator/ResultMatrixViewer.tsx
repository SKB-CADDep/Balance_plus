import { useMemo, useState } from 'react';
import {
  Alert,
  AlertIcon,
  Box,
  Heading,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  useColorModeValue,
} from '@chakra-ui/react';
import type { CondenserMatrix, CondenserMatrixResult } from './types';

function pickMatrix(r: CondenserMatrixResult): CondenserMatrix | null {
  if (r.matrix) return r.matrix;
  if (r.columns && r.rows && r.values) return { columns: r.columns, rows: r.rows, values: r.values };
  return null;
}

function stringifyMeta(meta: Record<string, unknown> | undefined): string {
  if (!meta) return 'case';
  const b = meta.coefficient_b ?? meta.b;
  const wMain = meta.W_main ?? meta.W ?? meta.w_main;
  const wBuiltin = meta.W_builtin ?? meta.w_builtin;

  const parts: string[] = [];
  if (b !== undefined) parts.push(`b=${String(b)}`);
  if (wMain !== undefined) parts.push(`W_main=${String(wMain)}`);
  if (wBuiltin !== undefined && String(wBuiltin) !== 'null') parts.push(`W_builtin=${String(wBuiltin)}`);

  return parts.length ? parts.join(', ') : 'case';
}

export type ResultMatrixViewerProps = {
  results: Array<CondenserMatrixResult>;
};

export function ResultMatrixViewer({ results }: ResultMatrixViewerProps) {
  const cardBg = useColorModeValue('white', 'gray.800');
  const cardBorder = useColorModeValue('gray.200', 'gray.700');
  const warningBg = useColorModeValue('yellow.50', 'yellow.900');

  const cases = useMemo(() => {
    return results
      .map((r, idx) => ({
        id: `${idx}`,
        label: stringifyMeta(r.meta),
        warnings: r.warnings ?? [],
        matrix: pickMatrix(r),
      }))
      .filter((c) => c.matrix);
  }, [results]);

  const [tabIdx, setTabIdx] = useState(0);

  if (!results.length) {
    return (
      <Box p={5} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
        <Heading size="sm">Результаты</Heading>
        <Box mt={2} color="gray.500">
          Нет данных. Нажмите «Рассчитать».
        </Box>
      </Box>
    );
  }

  if (!cases.length) {
    return (
      <Box p={5} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
        <Heading size="sm">Результаты</Heading>
        <Alert status="warning" mt={4}>
          <AlertIcon />
          Ответ сервера не содержит матрицу в ожидаемом формате.
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={5} borderWidth={1} borderColor={cardBorder} borderRadius="lg" bg={cardBg} shadow="sm">
      <Heading size="sm" mb={4}>
        Результаты ({cases.length} кейсов)
      </Heading>

      <Tabs index={Math.min(tabIdx, cases.length - 1)} onChange={setTabIdx} colorScheme="teal" variant="enclosed">
        <TabList overflowX="auto" overflowY="hidden">
          {cases.map((c) => (
            <Tab key={c.id} whiteSpace="nowrap">
              {c.label}
            </Tab>
          ))}
        </TabList>
        <TabPanels>
          {cases.map((c) => {
            const m = c.matrix!;
            return (
              <TabPanel key={c.id} px={0}>
                {c.warnings.length > 0 && (
                  <Alert status="warning" mb={4}>
                    <AlertIcon />
                    {c.warnings.join('; ')}
                  </Alert>
                )}

                <Box overflowX="auto">
                  <Table variant="striped" size="sm">
                    <Thead>
                      <Tr>
                        <Th>t1 \ G_steam</Th>
                        {m.columns.map((col, colIdx) => (
                          <Th key={colIdx}>{String(col)}</Th>
                        ))}
                      </Tr>
                    </Thead>
                    <Tbody>
                      {m.rows.map((row, rIdx) => (
                        <Tr key={rIdx}>
                          <Td fontWeight="bold">{String(row)}</Td>
                          {m.values[rIdx]?.map((v, cIdx) => (
                            <Td key={cIdx} bg={c.warnings.length ? warningBg : undefined}>
                              {v === null || v === undefined ? '-' : String(v)}
                            </Td>
                          ))}
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              </TabPanel>
            );
          })}
        </TabPanels>
      </Tabs>
    </Box>
  );
}

