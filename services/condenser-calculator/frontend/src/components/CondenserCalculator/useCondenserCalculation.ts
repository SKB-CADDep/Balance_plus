import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import type { CondenserFormValues, CondenserMatrixResult } from './types';

export type CondenserCalculationRequest = CondenserFormValues & {
  condenser_id?: string;
  material_id?: string;
};

export type CondenserCalculationResponse =
  | Array<CondenserMatrixResult>
  | {
      results: Array<CondenserMatrixResult>;
    };

export function useCondenserCalculation() {
  return useMutation({
    mutationFn: async (data: CondenserCalculationRequest) => {
      const resp = await axios.post<CondenserCalculationResponse>(
        '/api/v1/condensers/calculate',
        data,
        { headers: { 'Content-Type': 'application/json' } },
      );
      return resp.data;
    },
  });
}

