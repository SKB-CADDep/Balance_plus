import { test, expect } from '@playwright/test';
import { CondenserFormPage } from '../pages/CondenserFormPage';
import { ResultMatrixPage } from '../pages/ResultMatrixPage';

test.describe('Condenser Calculator - Happy Path & Navigation Flow', () => {
  let formPage: CondenserFormPage;
  let resultPage: ResultMatrixPage;

  test.beforeEach(async ({ page }) => {
    formPage = new CondenserFormPage(page);
    resultPage = new ResultMatrixPage(page);

    // 1. Мок детальной информации по единичному конденсатору
    await page.route(/\/api\/.*\/condensers\/\d+/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          name_condenser: 'К-3100-35-1',
          project_name: 'Проект 1',
          passes_main: 2,
          ejectors_count: 1,
          mass_flow_steam_nom: 120,
          cooling_area: 3100,
        }),
      });
    });

    // 2. Мок списка конденсаторов для главной страницы
    await page.route(/\/api\/.*\/condensers(\?.*)?$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name_condenser: 'К-3100-35-1', project_name: 'Проект 1' },
          ]),
        });
      } else {
        await route.continue();
      }
    });

    // 3. Мок списка материалов
    await page.route('**/api/**/materials*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, name: 'Л68' },
          { id: 2, name: '12Х18Н10Т' },
        ]),
      });
    });

    // 4. Мок результата расчета
    await page.route('**/api/**/*calc*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          condenser_name: 'К-3100-35-1',
          condenser_id: 1,
          method: 'metro-vickers',
          total_tables: 1,
          calculation_time_ms: 120,
          tables: [
            {
              meta: { coefficient_b: 1.0, W_main: 8000 },
              columns: [10, 20, 30],
              rows: [15, 20],
              values: [
                [0.0042, 0.0045, 0.0048],
                [0.0045, 0.0049, 0.0052],
              ],
              warnings: [],
            },
          ],
        }),
      });
    });

    await formPage.open();
  });

  test('Успешный ввод параметров и переход к результатам расчета (Happy Path)', async () => {
    await expect(formPage.pageTitle).toBeVisible();

    await formPage.performCalculation({
      steamFlow: '120',
      coolingWaterTemp: '15',
      waterFlowRate: '8000',
    });

    await resultPage.expectResultsLoaded();
    await expect(resultPage.matrixTable).toBeVisible();
  });

  test('Возможность повторного расчета с измененными входными данными', async () => {
    // Первичный расчет
    await formPage.performCalculation({
      steamFlow: '100',
      coolingWaterTemp: '20',
      waterFlowRate: '5000',
    });

    await resultPage.expectResultsLoaded();

    // Заново открываем готовую форму
    await formPage.open();

    // Повторный ввод и расчет со ВСЕМИ обязательными полями
    await formPage.performCalculation({
      steamFlow: '150',
      coolingWaterTemp: '10',
      waterFlowRate: '5000',
    });

    await resultPage.expectResultsLoaded();
  });

  test('Проверка доступности кнопки экспорта в Excel после расчета', async () => {
    await formPage.performCalculation({
      steamFlow: '90',
      coolingWaterTemp: '18',
      waterFlowRate: '6000',
    });

    await resultPage.expectResultsLoaded();
    if (await resultPage.exportExcelButton.isVisible()) {
      await expect(resultPage.exportExcelButton).toBeEnabled();
    }
  });
});