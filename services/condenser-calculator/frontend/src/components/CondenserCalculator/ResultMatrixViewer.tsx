import { useMemo, useState } from 'react';
import {
  Alert,
  AlertIcon,
  Box,
  Select,
  Flex,
  Text,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  useColorModeValue,
} from '@chakra-ui/react';
import type { MatrixResult } from '../../client';

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
  results: Array<MatrixResult>;
};

export function ResultMatrixViewer({ results }: ResultMatrixViewerProps) {
  const cardBorder = useColorModeValue('gray.200', 'gray.700');
  const warningBg = useColorModeValue('yellow.50', 'yellow.900');
  const headerBg = useColorModeValue('gray.50', 'gray.800');

  const cases = useMemo(() => {
    return results
      .map((r, idx) => ({
        id: `${idx}`,
        label: stringifyMeta(r.meta),
        warnings: r.warnings ?? [],
        matrix: { columns: r.columns, rows: r.rows, values: r.values },
      }))
      .filter((c) => c.matrix);
  }, [results]);

  const [selectedIdx, setSelectedIdx] = useState(0);

  if (!results.length) {
    return (
      <Box color="gray.500">
        Нет данных для отображения.
      </Box>
    );
  }

  if (!cases.length) {
    return (
      <Alert status="warning">
        <AlertIcon />
        Ответ сервера не содержит матрицу в ожидаемом формате.
      </Alert>
    );
  }

  const currentCase = cases[Math.min(selectedIdx, cases.length - 1)];
  const m = currentCase?.matrix;

  return (
    <Box>
      {cases.length > 1 && (
        <Flex mb={6} align="center" gap={4} wrap="wrap">
          <Text fontWeight="medium" whiteSpace="nowrap">Выберите кейс:</Text>
          <Select 
            w="auto" 
            minW="300px"
            value={selectedIdx} 
            onChange={(e) => setSelectedIdx(Number(e.target.value))}
            bg={useColorModeValue('white', 'gray.700')}
          >
            {cases.map((cs, i) => (
              <option key={cs.id} value={i}>
                {cs.label} {cs.warnings.length > 0 ? ' (⚠️)' : ''}
              </option>
            ))}
          </Select>
        </Flex>
      )}

      {currentCase && m && (
        <Box>
          {currentCase.warnings.length > 0 && (
            <Alert status="warning" mb={4} borderRadius="md">
              <AlertIcon />
              {currentCase.warnings.join('; ')}
            </Alert>
          )}

          <Box overflowX="auto" borderWidth={1} borderColor={cardBorder} borderRadius="md">
            <Table variant="simple" size="sm">
              <Thead bg={headerBg}>
                <Tr>
                  <Th borderRightWidth={1} borderColor={cardBorder} minW="180px" p={2}>
                    <Flex direction="column" justify="space-between" h="full" gap={2}>
                      <Text textAlign="right" fontSize="xs" color="gray.500" textTransform="none">Расход пара →</Text>
                      <Text textAlign="left" fontSize="xs" color="gray.500" textTransform="none">↓ Темп. воды</Text>
                    </Flex>
                  </Th>
                  {m.columns.map((col, colIdx) => (
                    <Th key={colIdx} textAlign="center">{String(col)}</Th>
                  ))}
                </Tr>
              </Thead>
              <Tbody>
                {m.rows.map((row, rIdx) => (
                  <Tr key={rIdx}>
                    <Td borderRightWidth={1} borderColor={cardBorder} fontWeight="bold" bg={headerBg}>
                      {String(row)}
                    </Td>
                    {m.values[rIdx]?.map((v, cIdx) => (
                      <Td key={cIdx} bg={currentCase.warnings.length ? warningBg : undefined} textAlign="center">
                        {v === null || v === undefined ? '-' : typeof v === 'number' ? v.toFixed(4) : String(v)}
                      </Td>
                    ))}
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
        </Box>
      )}
    </Box>
  );
}

