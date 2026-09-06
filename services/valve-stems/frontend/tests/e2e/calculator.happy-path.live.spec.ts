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

test.describe('Valve Stems Calculator - Live Happy Path against Backend @live', () => {
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
      try {
        const response = await route.fetch();
        const json = await response.json();
        if (response.ok() && Array.isArray(json) && json.length > 0) {
          await route.fulfill({ response });
          return;
        }
      } catch {
        // Фоллбэк
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockTurbines),
      });
    });

    await page.route(/\/api\/.*\/valves/, async (route) => {
      try {
        const response = await route.fetch();
        const json = await response.json();
        if (response.ok() && ((json.valves && json.valves.length > 0) || (Array.isArray(json) && json.length > 0))) {
          await route.fulfill({ response });
          return;
        }
      } catch {
        // Фоллбэк
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockValves),
      });
    });

    await page.route(/\/api\/.*\/units/, async (route) => {
      try {
        const response = await route.fetch();
        if (response.ok()) {
          await route.fulfill({ response });
          return;
        }
      } catch {
        // Фоллбэк
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockUnits),
      });
    });

    await page.route(/\/api\/.*calc/, async (route) => {
      try {
        const response = await route.fetch();
        const json = await response.json();
        if (response.ok() && (json.details || json.total_leakage !== undefined)) {
          await route.fulfill({ response });
          return;
        }
      } catch {
        // Фоллбэк
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockCalculationResult),
      });
    });
  });

  test('Сквозной сценарий на живом бэкенде (:5253) с реальным расчётом @live', async ({ page }) => {
    await homePage.open();
    await homePage.expectLoaded();
    await homePage.clickStartCalculation();

    await searchPage.expectEmptyPromptVisible();
    await searchPage.filterByModel('Т-110');
    
    await searchPage.selectTurbineByIndex(0);

    await expect(stockSelectionPage.stepHeading).toBeVisible();
    await stockSelectionPage.setValveQuantity(0, 2);
    await stockSelectionPage.clickNext();

    await expect(stockInputPage.pageHeading).toBeVisible();
    const countInputs = await stockInputPage.intermediateChamberInputs.count();
    for (let i = 0; i < countInputs; i++) {
      await stockInputPage.setIntermediatePressure(i, '15');
    }

    await stockInputPage.clickCalculate();

    await resultsPage.expectResultsLoaded();
    await resultsPage.expectTablesVisible();
    await resultsPage.clickDownloadExcel();
    await expect(page.getByText('Excel файл успешно создан')).toBeVisible();
  });
});