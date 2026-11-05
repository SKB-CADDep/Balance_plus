/// <reference types="node" />
import { test, expect } from '@playwright/test';
import fs from 'fs';
import { HomePage } from '../pages/HomePage';
import { TurbineSearchPage } from '../pages/TurbineSearchPage';
import { StockSelectionPage } from '../pages/StockSelectionPage';
import { StockInputPage } from '../pages/StockInputPage';
import { ResultsPage } from '../pages/ResultsPage';

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

test.describe('Valve Stems Calculator - Full Happy Path (Mocked CI)', () => {
  let homePage: HomePage;
  let searchPage: TurbineSearchPage;
  let stockSelectionPage: StockSelectionPage;
  let stockInputPage: StockInputPage;
  let resultsPage: ResultsPage;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    searchPage = new TurbineSearchPage(page);
    stockSelectionPage = new StockSelectionPage(page);
    stockInputPage = new StockInputPage(page);
    resultsPage = new ResultsPage(page);

    await page.route('**/*', async (route) => {
      if (route.request().method() === 'OPTIONS') {
        await route.fulfill({
          status: 204,
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*',
          },
        });
        return;
      }
      await route.fallback();
    });

    await page.route(/\/api\/.*\/turbines.*search/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockTurbines),
      });
    });

    await page.route(/\/api\/.*\/valves/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockValves),
      });
    });

    await page.route(/\/api\/.*\/units/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockUnits),
      });
    });

    await page.route(/\/api\/.*calc/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockCalculationResult),
      });
    });
  });

  test('Сквозной сценарий "Как инженер": от Главной до результатов и выгрузки Excel', async ({ page }) => {
    // -------------------------------------------------------------------------
    // 1. Главная страница
    // -------------------------------------------------------------------------
    await homePage.open();
    await homePage.expectLoaded();

    await homePage.clickStartCalculation();
    expect(page.url()).toContain('/calculator');

    // -------------------------------------------------------------------------
    // 2. Шаг 1: Поиск и выбор турбины (TurbineSearch)
    // -------------------------------------------------------------------------
    await searchPage.expectEmptyPromptVisible();
    await searchPage.filterByModel('Т-110');
    await searchPage.expectResultsCount(2);

    await searchPage.selectTurbineByName('Т-110/120-130');

    // -------------------------------------------------------------------------
    // 3. Шаг 2: Выбор состава клапанов (StockSelection)
    // -------------------------------------------------------------------------
    await expect(stockSelectionPage.projectHeading).toContainText('Т-110/120-130');
    await stockSelectionPage.expectValveCardVisible('Клапан РК-1', 'РК');
    await stockSelectionPage.expectValveCardVisible('Клапан СК-1', 'СК');

    await stockSelectionPage.setValveQuantity('Клапан РК-1', 2);
    await stockSelectionPage.setValveQuantity('Клапан СК-1', 1);
    await stockSelectionPage.expectNextButtonEnabled(3);

    await stockSelectionPage.clickNext();

    await expect(stockInputPage.pageHeading).toBeVisible();
    await expect(stockInputPage.subtitleInfo).toContainText('Турбина: Т-110/120-130 | Выбрано клапанов: 2');

    await stockInputPage.setIntermediatePressure(0, '15'); // РК-1 (Камера 1)
    await stockInputPage.setIntermediatePressure(1, '10'); // СК-1 (Камера 1)
    await stockInputPage.setIntermediatePressure(2, '5');  // СК-1 (Камера 2)

    await stockInputPage.clickCalculate();

    await resultsPage.expectResultsLoaded();
    await resultsPage.expectTablesVisible();

    await expect(page.getByText('0.1254').first()).toBeVisible();
    await expect(page.getByText('130').first()).toBeVisible();
    await expect(page.getByText('555').first()).toBeVisible();

    await expect(resultsPage.deaeratorBadges.first()).toBeVisible();
    await expect(resultsPage.ejectorBadges.first()).toBeVisible();

    await resultsPage.clickDownloadExcel();
    await expect(page.getByText('Excel файл успешно создан')).toBeVisible();
  });
});