/// <reference types="node" />
import { test, expect } from '@playwright/test';
import fs from 'fs';
import { TurbineSearchPage } from '../pages/TurbineSearchPage';
import { StockSelectionPage } from '../pages/StockSelectionPage';
import { StockInputPage } from '../pages/StockInputPage';
import { ResultsPage } from '../pages/ResultsPage';
import { navigateToStep3WithSelectedValves } from '../helpers/form-fillers';

const mockTurbines = JSON.parse(
  fs.readFileSync(new URL('../mocks/turbines-search.json', import.meta.url), 'utf-8')
);

const mockValves = JSON.parse(
  fs.readFileSync(new URL('../mocks/turbine-valves.json', import.meta.url), 'utf-8')
);

const mockUnits = JSON.parse(
  fs.readFileSync(new URL('../mocks/units.json', import.meta.url), 'utf-8')
);

const mockCalculationResult = JSON.parse(
  fs.readFileSync(new URL('../mocks/calculation-result.json', import.meta.url), 'utf-8')
);

const mockCalculationError = JSON.parse(
  fs.readFileSync(new URL('../mocks/calculation-error.json', import.meta.url), 'utf-8')
);

test.describe('Valve Stems Calculator - Step 4: Calculation Results', () => {
  let searchPage: TurbineSearchPage;
  let stockSelectionPage: StockSelectionPage;
  let stockInputPage: StockInputPage;
  let resultsPage: ResultsPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new TurbineSearchPage(page);
    stockSelectionPage = new StockSelectionPage(page);
    stockInputPage = new StockInputPage(page);
    resultsPage = new ResultsPage(page);

    // Мок поиска турбин (строго с /api/)
    await page.route(/\/api\/.*\/turbines.*search/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTurbines),
      });
    });

    // Мок списка клапанов (строго с /api/)
    await page.route(/\/api\/.*\/valves/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockValves),
      });
    });

    // Мок единиц измерения (строго с /api/)
    await page.route(/\/api\/.*\/units/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockUnits),
      });
    });
  });

  async function performSuccessfulCalculation(page: any) {
    // Мок успешного расчёта (строго с /api/)
    await page.route(/\/api\/.*calc/, async (route: any) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockCalculationResult),
      });
    });

    await navigateToStep3WithSelectedValves(searchPage, stockSelectionPage);

    // Заполняем промежуточные давления
    await stockInputPage.setIntermediatePressure(0, '15');
    await stockInputPage.setIntermediatePressure(1, '10');
    await stockInputPage.setIntermediatePressure(2, '5');

    // Нажимаем «Рассчитать»
    await stockInputPage.clickCalculate();
    await resultsPage.expectResultsLoaded();
  }

  test('Happy path: успешный расчёт отображает таблицы участков, потребителей и сводку отсосов', async ({ page }) => {
    await performSuccessfulCalculation(page);

    // Проверяем наличие всех 3 типов таблиц
    await resultsPage.expectTablesVisible();

    // Проверяем наличие строк с участками
    await expect(page.getByText('Участок 1').first()).toBeVisible();
    await expect(page.getByText('Участок 2').first()).toBeVisible();
    await expect(page.getByText('Участок 3').first()).toBeVisible();
  });

  test('Отображение расходов G, давления P, температуры T и энтальпии H', async ({ page }) => {
    await performSuccessfulCalculation(page);

    // Проверяем расчетные значения из мока
    await expect(page.getByText('0.1254').first()).toBeVisible(); // G
    await expect(page.getByText('130').first()).toBeVisible();     // P
    await expect(page.getByText('555').first()).toBeVisible();     // T
    await expect(page.getByText('832.9').first()).toBeVisible();   // H
  });

  test('Итоговая сводная таблица отсосов содержит данные деаэратора и эжектора', async ({ page }) => {
    await performSuccessfulCalculation(page);

    // Проверяем бейджи деаэратора и отсоса
    await expect(resultsPage.deaeratorBadges.first()).toBeVisible();
    await expect(resultsPage.ejectorBadges.first()).toBeVisible();

    // Проверяем отображение строки "Деаэратор" в итоговой таблице
    await expect(page.getByRole('cell', { name: 'Деаэратор' }).first()).toBeVisible();
  });

  test('Экспорт Excel: нажатие кнопки формирует файл и показывает уведомление', async ({ page }) => {
    await performSuccessfulCalculation(page);

    // Кликаем «Скачать Excel»
    await resultsPage.clickDownloadExcel();

    // Проверяем тост об успешном создании Excel-файла
    await expect(page.getByText('Excel файл успешно создан')).toBeVisible();
  });

  test('Генерация Draw.io схемы: успешная генерация и скачивание .drawio файла', async ({ page }) => {
    // Мок успешной генерации схемы (строго с /api/)
    await page.route(/\/api\/.*\/generate_scheme/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/xml',
        body: '<mxGraphModel><root><mxCell id="0"/></root></mxGraphModel>',
      });
    });

    await performSuccessfulCalculation(page);

    // Ожидаем событие скачивания браузером
    const downloadPromise = page.waitForEvent('download');
    await resultsPage.clickDownloadDrawio(0);

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.drawio');
  });

  test('Генерация Draw.io схемы: при ошибке сервера показывается toast', async ({ page }) => {
    // Мок ошибки генерации схемы (строго с /api/)
    await page.route(/\/api\/.*\/generate_scheme/, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Ошибка сервера при генерации схемы.' }),
      });
    });

    await performSuccessfulCalculation(page);

    await resultsPage.clickDownloadDrawio(0);

    // Проверяем тост с ошибкой
    await expect(page.getByText('Ошибка сервера при генерации схемы.')).toBeVisible();
  });

  test('Ошибка API при расчёте (500): показывает toast с ошибкой и не переходит на пустой экран', async ({ page }) => {
    // Мок ошибки при расчёте (строго с /api/)
    await page.route(/\/api\/.*calc/, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify(mockCalculationError),
      });
    });

    await navigateToStep3WithSelectedValves(searchPage, stockSelectionPage);

    await stockInputPage.setIntermediatePressure(0, '15');
    await stockInputPage.setIntermediatePressure(1, '10');
    await stockInputPage.setIntermediatePressure(2, '5');

    await stockInputPage.clickCalculate();

    // Проверяем сообщение об ошибке
    await expect(page.getByText(/Ошибка при выполнении расчета/i)).toBeVisible();
    await expect(page.getByText('Критическая ошибка расчёта: недопустимые термодинамические параметры пара')).toBeVisible();

    // Проверяем, что остались на экране ввода параметров, а не перешли на пустой Results
    await expect(stockInputPage.pageHeading).toBeVisible();
    await expect(resultsPage.summaryTableHeading).not.toBeVisible();
  });

  test('Кнопка "Изменить параметры расчета" возвращает на Шаг 3 (StockInputPage)', async ({ page }) => {
    await performSuccessfulCalculation(page);

    // Нажимаем «Изменить параметры расчета»
    await resultsPage.clickBack();

    // Проверяем возврат к Шагу 3 с сохраненными полями
    await expect(stockInputPage.pageHeading).toBeVisible();
    await expect(stockInputPage.pFreshInput).toHaveValue('130');
  });
});