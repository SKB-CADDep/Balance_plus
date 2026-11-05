import { Page } from '@playwright/test';
import { mockTurbinesData, mockValvesData, mockCalculationResultData } from '../fixtures/test-data';

export async function setupValveStemsApiMocks(page: Page): Promise<void> {
  // Мок списка турбин
  await page.route('**/api/**/turbines*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockTurbinesData),
    });
  });

  // Мок клапанов
  await page.route('**/api/**/valves*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockValvesData),
    });
  });

  // Мок расчета штоков
  await page.route('**/api/**/*calc*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockCalculationResultData),
    });
  });
}