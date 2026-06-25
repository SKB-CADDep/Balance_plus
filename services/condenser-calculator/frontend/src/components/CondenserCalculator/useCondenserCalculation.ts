import { useMutation } from '@tanstack/react-query';
import { CalculationsService, type CalculationInput, type CalculationOutput } from '../../client';

export function useCondenserCalculation() {
  return useMutation({
    mutationFn: (data: CalculationInput) =>
      CalculationsService.calculateApiV1CalculatePost({ requestBody: data }) as Promise<CalculationOutput>,
  });
}

