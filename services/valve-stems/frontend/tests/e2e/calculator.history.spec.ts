/// <reference types="node" />
import { test, expect } from '@playwright/test';
import fs from 'fs';
import { TurbineSearchPage } from '../pages/TurbineSearchPage';
import { StockSelectionPage } from '../pages/StockSelectionPage';
import { StockInputPage } from '../pages/StockInputPage';
import { ResultsPage } from '../pages/ResultsPage';
import { SidebarHistory } from '../pages/SidebarHistory';
import { navigateToStep3WithSelectedValves } from '../helpers/form-fillers';
import {
  setHistoryInLocalStorage,
  getHistoryFromLocalStorage,
  generateMockHistoryEntries,
  clearHistoryInLocalStorage,
} from '../helpers/localStorage';

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

test.describe('Valve Stems Calculator - Local Storage History', () => {
  let searchPage: TurbineSearchPage;
  let stockSelectionPage: StockSelectionPage;
  let stockInputPage: StockInputPage;
  let resultsPage: ResultsPage;
  let sidebarHistory: SidebarHistory;

  test.beforeEach(async ({ page }) => {
    searchPage = new TurbineSearchPage(page);
    stockSelectionPage = new StockSelectionPage(page);
    stockInputPage = new StockInputPage(page);
    resultsPage = new ResultsPage(page);
    sidebarHistory = new SidebarHistory(page);

    // 1. Автоматический ответ на любые CORS OPTIONS preflight запросы
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

    // 2. Мок поиска турбин
    await page.route(/\/api\/.*\/turbines.*search/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockTurbines),
      });
    });

    // 3. Мок списка клапанов
    await page.route(/\/api\/.*\/valves/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockValves),
      });
    });

    // 4. Мок единиц измерения
    await page.route(/\/api\/.*\/units/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockUnits),
      });
    });

    // 5. Мок информации о турбине по ID
    await page.route('**/*turbines/1*', async (route) => {
      if (route.request().url().includes('/valves')) {
        await route.fallback();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({
          id: 1,
          name: 'Т-110/120-130',
          station_name: 'Абаканская ТЭЦ',
          station_number: '1',
          factory_number: '10452',
        }),
      });
    });
  });

  test('После успешного расчёта появляется запись в истории без ручного refresh страницы', async ({ page }) => {
    await page.route(/\/api\/.*calc/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockCalculationResult),
      });
    });

    await navigateToStep3WithSelectedValves(searchPage, stockSelectionPage);
    await stockInputPage.setIntermediatePressure(0, '15');
    await stockInputPage.setIntermediatePressure(1, '10');
    await stockInputPage.setIntermediatePressure(2, '5');

    await clearHistoryInLocalStorage(page);

    await stockInputPage.clickCalculate();
    await resultsPage.expectResultsLoaded();

    await sidebarHistory.openSidebar();

    await sidebarHistory.expectHistoryCount(1);
    await sidebarHistory.expectEntryVisible('РК(2шт) + СК(1шт)', 'Т-110/120-130');

    const stored = await getHistoryFromLocalStorage(page);
    expect(stored).toHaveLength(1);
    expect(stored[0].stockName).toBe('РК(2шт) + СК(1шт)');
  });

  test('Открытие Sidebar отображает список сохранённых записей', async ({ page }) => {
    await searchPage.open();

    const mockEntries = generateMockHistoryEntries(3);
    await setHistoryInLocalStorage(page, mockEntries);

    await sidebarHistory.openSidebar();

    await sidebarHistory.expectHistoryCount(3);
    await sidebarHistory.expectEntryVisible('РК-1(1шт)', 'Турбина Т-100');
  });

  test('Клик по записи в истории загружает результат расчёта по ID', async ({ page }) => {
    const historyEntry = {
      id: '999',
      stockName: 'РК(2шт) + СК(1шт)',
      stockId: 101,
      turbineName: 'Т-110/120-130',
      turbineId: 1,
      timestamp: Date.now(),
    };

    // Мок получения расчета по ID 999
    await page.route('**/*999*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': '*',
        },
        body: JSON.stringify({
          id: 999,
          user_name: 'Engineer',
          stock_name: 'РК(2шт) + СК(1шт)',
          turbine_name: 'Т-110/120-130',
          calc_timestamp: new Date().toISOString(),
          input_data: JSON.stringify({
            turbine_id: 1,
            globals: {
              P_fresh: 130,
              P_fresh_unit: 'кгс/см²',
              T_fresh: 555,
              T_fresh_unit: '°C',
              H_fresh: null,
              H_fresh_unit: 'ккал/кг',
              P_air: 1.033,
              P_air_unit: 'кгс/см²',
              T_air: 20,
              T_air_unit: '°C',
              P_lst_leak_off: 0.97,
              P_lst_leak_off_unit: 'кгс/см²',
            },
            groups: [
              {
                valve_id: 101,
                type: 'РК',
                valve_names: ['Клапан РК-1'],
                quantity: 2,
                p_values: [130, 15, 1.033],
                p_values_unit: 'кгс/см²',
                p_leak_offs: [15],
                p_leak_offs_unit: 'кгс/см²',
              },
            ],
          }),
          output_data: JSON.stringify(mockCalculationResult),
        }),
      });
    });

    await searchPage.open();
    await setHistoryInLocalStorage(page, [historyEntry]);

    // Открываем сайдбар и кликаем по записи
    await sidebarHistory.openSidebar();
    await sidebarHistory.clickHistoryEntry(0);

    // Проверяем появление тоста об успешной загрузке данных расчёта из истории
    await expect(page.getByText(/Расчет.*загружен/i)).toBeVisible();
  });

  test('Очистка истории удаляет все записи из UI и localStorage', async ({ page }) => {
    await searchPage.open();

    const mockEntries = generateMockHistoryEntries(2);
    await setHistoryInLocalStorage(page, mockEntries);

    await sidebarHistory.openSidebar();
    await sidebarHistory.expectHistoryCount(2);

    await sidebarHistory.clickClearAll();

    await sidebarHistory.expectEmptyHistory();
    const stored = await getHistoryFromLocalStorage(page);
    expect(stored).toHaveLength(0);
  });

  test('Лимит 20 записей: при добавлении новой старая вытесняется', async ({ page }) => {
    await page.route(/\/api\/.*calc/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify(mockCalculationResult),
      });
    });

    await searchPage.open();

    const initial20Entries = generateMockHistoryEntries(20);
    await setHistoryInLocalStorage(page, initial20Entries);

    await navigateToStep3WithSelectedValves(searchPage, stockSelectionPage);
    await stockInputPage.setIntermediatePressure(0, '15');
    await stockInputPage.setIntermediatePressure(1, '10');
    await stockInputPage.setIntermediatePressure(2, '5');

    await stockInputPage.clickCalculate();
    await resultsPage.expectResultsLoaded();

    const updatedHistory = await getHistoryFromLocalStorage(page);
    expect(updatedHistory).toHaveLength(20);
    expect(updatedHistory[0].stockName).toBe('РК(2шт) + СК(1шт)');
  });

  test('Ошибка загрузки по битому ID: отображает toast и возвращает к поиску турбин', async ({ page }) => {
    const brokenEntry = {
      id: '888',
      stockName: 'Битый расчет',
      stockId: 101,
      turbineName: 'Т-110',
      turbineId: 1,
      timestamp: Date.now(),
    };

    await page.route('**/*888*', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': '*',
        },
        body: JSON.stringify({ detail: 'Расчет не найден в базе данных' }),
      });
    });

    await searchPage.open();
    await setHistoryInLocalStorage(page, [brokenEntry]);

    await sidebarHistory.openSidebar();
    await sidebarHistory.clickHistoryEntry(0);

    await expect(page.getByText('Ошибка загрузки из истории')).toBeVisible();
    await expect(searchPage.pageHeading).toBeVisible();
  });
});