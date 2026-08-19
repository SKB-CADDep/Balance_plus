export const mockTurbinesData = [
  {
    id: 1,
    name: 'Турбина К-300-240',
    type: 'Паровая',
    valves_count: 4,
  },
  {
    id: 2,
    name: 'Турбина Т-100/120-130',
    type: 'Теплофикационная',
    valves_count: 2,
  },
];

export const mockValvesData = [
  {
    id: 101,
    turbine_id: 1,
    name: 'Клапан регулирующий №1',
    stem_diameter: 25.0,
  },
];

export const mockCalculationResultData = {
  status: 'success',
  calculation_id: 'calc_999',
  results: {
    stem_length_calculated: 145.5,
    margin_safety: 1.25,
  },
};