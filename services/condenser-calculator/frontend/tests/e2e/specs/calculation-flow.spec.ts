import { test, expect } from '@playwright/test';
import { CondenserFormPage } from '../pages/CondenserFormPage';
import { ResultMatrixPage } from '../pages/ResultMatrixPage';

test.describe('Condenser Calculator - Happy Path & Navigation Flow', () => {
  let formPage: CondenserFormPage;
  let resultPage: ResultMatrixPage;

  test.beforeEach(async ({ page }) => {
    formPage = new CondenserFormPage(page);
    resultPage = new ResultMatrixPage(page);

    // Переход на страницу калькулятора через POM
    await formPage.open();
  });

  test('Успешный ввод параметров и переход к результатам расчета (Happy Path)', async () => {
    // 1. Проверяем отображение заголовка формы калькулятора
    await expect(formPage.pageTitle).toBeVisible();

    // 2. Заполняем форму валидными значениями и отправляем расчет
    await formPage.performCalculation({
      steamFlow: '120',
      coolingWaterTemp: '15',
      waterFlowRate: '8000',
      materialId: '1',
    });

    // 3. Проверяем, что результаты расчета загрузились
    await resultPage.expectResultsLoaded();

    // 4. Проверяем наличие таблицы матрицы результатов
    await expect(resultPage.matrixTable).toBeVisible();
  });

  test('Возможность повторного расчета с измененными входными данными', async () => {
    // 1. Первичный расчет
    await formPage.performCalculation({
      steamFlow: '100',
      coolingWaterTemp: '20',
      waterFlowRate: '5000',
    });

    await resultPage.expectResultsLoaded();

    // 2. Повторное заполнение формы другими значениями
    await formPage.fillForm({
      steamFlow: '150',
      coolingWaterTemp: '10',
    });
    await formPage.submitCalculation();

    // 3. Подтверждаем обновленную загрузку результатов
    await resultPage.expectResultsLoaded();
  });

  test('Проверка доступности кнопки экспорта в Excel после расчета', async () => {
    await formPage.performCalculation({
      steamFlow: '90',
      coolingWaterTemp: '18',
      waterFlowRate: '6000',
    });

    await resultPage.expectResultsLoaded();
    await expect(resultPage.exportExcelButton).toBeVisible();
    await expect(resultPage.exportExcelButton).toBeEnabled();
  });
});