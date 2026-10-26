/// <reference types="node" />
import { test, expect, Page } from '@playwright/test';
import fs from 'fs';
import { TurbineSearchPage } from '../pages/TurbineSearchPage';
import { StockSelectionPage } from '../pages/StockSelectionPage';
import { StockInputPage } from '../pages/StockInputPage';
import { ResultsPage } from '../pages/ResultsPage';
import { setupPostMessageListener, waitForPostMessage } from '../helpers/postMessage';

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

test.describe('Valve Stems Calculator - Embedded Mode & Balance+ Integration', () => {
  let searchPage: TurbineSearchPage;
  let stockSelectionPage: StockSelectionPage;
  let stockInputPage: StockInputPage;
  let resultsPage: ResultsPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new TurbineSearchPage(page);
    stockSelectionPage = new StockSelectionPage(page);
    stockInputPage = new StockInputPage(page);
    resultsPage = new ResultsPage(page);

    // Устанавливаем перехватчик postMessage до загрузки страницы
    await setupPostMessageListener(page);

    // Мок поиска турбин
    await page.route(/\/api\/.*\/turbines.*search/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockTurbines),
      });
    });

    // Мок списка клапанов
    await page.route(/\/api\/.*\/valves/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockValves),
      });
    });

    // Мок единиц измерения
    await page.route(/\/api\/.*\/units/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockUnits),
      });
    });

    // Мок расчёта
    await page.route(/\/api\/.*calc/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockCalculationResult),
      });
    });
  });

  async function navigateToEmbeddedResults(page: Page) {
    await page.goto('/calculator?embedded=true&taskId=task_123&projectId=proj_456');

    await searchPage.filterByModel('Т-110');
    await searchPage.selectTurbineByName('Т-110/120-130');
    await stockSelectionPage.setValveQuantity('Клапан РК-1', 2);
    await stockSelectionPage.setValveQuantity('Клапан СК-1', 1);
    await stockSelectionPage.clickNext();

    await stockInputPage.setIntermediatePressure(0, '15');
    await stockInputPage.setIntermediatePressure(1, '10');
    await stockInputPage.setIntermediatePressure(2, '5');
    await stockInputPage.clickCalculate();
    await resultsPage.expectResultsLoaded();
  }

  test('Открытие в embedded-режиме: отображаются кнопки "Сохранить в Balance+" и "Вернуться в Balance+"', async ({ page }) => {
    await navigateToEmbeddedResults(page);

    const saveToIdeBtn = page.getByRole('button', { name: /Сохранить в Balance\+/i });
    await expect(saveToIdeBtn).toBeVisible();

    const closeBtn = page.getByRole('button', { name: /Вернуться в Balance\+/i });
    await expect(closeBtn).toBeVisible();

    await expect(resultsPage.backButton).not.toBeVisible();
  });

  test('«Сохранить в Balance+» отправляет postMessage WSA_CALCULATION_COMPLETE с input, output и stockId', async ({ page }) => {
    await navigateToEmbeddedResults(page);

    const saveToIdeBtn = page.getByRole('button', { name: /Сохранить в Balance\+/i });
    await saveToIdeBtn.click();

    const message = await waitForPostMessage(page, 'WSA_CALCULATION_COMPLETE');

    expect(message).toBeDefined();
    expect(message.type).toBe('WSA_CALCULATION_COMPLETE');
    expect(message.payload).toBeDefined();

    // Проверяем с безопасным оператором опциональной цепочки
    expect(message.payload?.input).toBeDefined();
    expect(message.payload?.input.turbine_id).toBe(1);
    expect(message.payload?.input.globals.P_fresh).toBe(130);

    expect(message.payload?.output).toBeDefined();
    expect(message.payload?.output.total_leakage).toBe(0.4521);

    expect(message.payload?.stockId).toContain('РК');

    await expect(page.getByText('Отправлено в Balance+')).toBeVisible();
  });

  test('Кнопка «Вернуться в Balance+» отправляет postMessage WSA_CLOSE', async ({ page }) => {
    await navigateToEmbeddedResults(page);

    const closeBtn = page.getByRole('button', { name: /Вернуться в Balance\+/i });
    await closeBtn.click();

    const message = await waitForPostMessage(page, 'WSA_CLOSE');
    expect(message).toBeDefined();
    expect(message.type).toBe('WSA_CLOSE');
  });

  test.skip(
    'WSA_RESTORE_STATE / WSA_READY: восстановление состояния из оркестратора (Known Gap: #VALVE-GAP-01)',
    async ({ page }) => {
      await page.goto('/calculator?embedded=true');
      await page.evaluate(() => {
        window.postMessage({
          type: 'WSA_RESTORE_STATE',
          payload: { turbineId: 1, currentStep: 'stockSelection' },
        }, '*');
      });
      await expect(page.getByRole('heading', { name: /Выбранный проект/i })).toBeVisible();
    }
  );

  test('Standalone режим без embedded=true: отображает стандартные кнопки без интеграционных postMessage', async ({ page }) => {
    await page.goto('/calculator');

    await searchPage.filterByModel('Т-110');
    await searchPage.selectTurbineByName('Т-110/120-130');
    await stockSelectionPage.setValveQuantity('Клапан РК-1', 2);
    await stockSelectionPage.setValveQuantity('Клапан СК-1', 1);
    await stockSelectionPage.clickNext();

    await stockInputPage.setIntermediatePressure(0, '15');
    await stockInputPage.setIntermediatePressure(1, '10');
    await stockInputPage.setIntermediatePressure(2, '5');
    await stockInputPage.clickCalculate();
    await resultsPage.expectResultsLoaded();

    await expect(resultsPage.backButton).toBeVisible();

    await expect(page.getByRole('button', { name: /Сохранить в Balance\+/i })).not.toBeVisible();
    await expect(page.getByRole('button', { name: /Вернуться в Balance\+/i })).not.toBeVisible();
  });
});