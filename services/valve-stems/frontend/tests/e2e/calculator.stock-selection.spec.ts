/// <reference types="node" />
import { test, expect } from '@playwright/test';
import fs from 'fs';
import { TurbineSearchPage } from '../pages/TurbineSearchPage';
import { StockSelectionPage } from '../pages/StockSelectionPage';

const mockTurbines = JSON.parse(
  fs.readFileSync(new URL('../mocks/turbines-search.json', import.meta.url), 'utf-8')
);

const mockValves = JSON.parse(
  fs.readFileSync(new URL('../mocks/turbine-valves.json', import.meta.url), 'utf-8')
);

test.describe('Valve Stems Calculator - Step 2: Stock Selection', () => {
  let searchPage: TurbineSearchPage;
  let stockSelectionPage: StockSelectionPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new TurbineSearchPage(page);
    stockSelectionPage = new StockSelectionPage(page);

    await page.route(/turbines.*search/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTurbines),
      });
    });

    await page.route(/valves/, async (route) => {
      const url = route.request().url();
      if (url.includes('/turbines/2') || url.includes('turbine_id=2') || url.includes('turbineId=2')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ count: 0, valves: [] }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockValves),
        });
      }
    });

    await page.route(/units/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          pressure: ['кгс/см²', 'МПа', 'бар'],
          temperature: ['°C', 'K'],
          enthalpy: ['ккал/кг', 'кДж/кг'],
        }),
      });
    });
  });

  test('Загрузка списка клапанов для выбранной турбины с отображением названия и типов', async () => {
    await searchPage.open();
    await searchPage.filterByModel('Т-110');
    await searchPage.selectTurbineByName('Т-110/120-130');

    await expect(stockSelectionPage.projectHeading).toContainText('Т-110/120-130');
    await expect(stockSelectionPage.stepHeading).toBeVisible();

    await stockSelectionPage.expectValveCardVisible('Клапан РК-1', 'РК');
    await stockSelectionPage.expectValveCardVisible('Клапан СК-1', 'СК');
  });

  test('Блокировка перехода при totalSelected = 0', async () => {
    await searchPage.open();
    await searchPage.filterByModel('Т-110');
    await searchPage.selectTurbineByName('Т-110/120-130');

    await stockSelectionPage.expectNextButtonDisabled();
  });

  test('Ввод quantity для одного и нескольких клапанов с динамическим обновлением счётчика', async () => {
    await searchPage.open();
    await searchPage.filterByModel('Т-110');
    await searchPage.selectTurbineByName('Т-110/120-130');

    // Указываем 2 шт для первого клапана
    await stockSelectionPage.setValveQuantity('Клапан РК-1', 2);
    await stockSelectionPage.expectNextButtonEnabled(2);

    // Добавляем 3 шт для второго клапана -> сумма 5
    await stockSelectionPage.setValveQuantity('Клапан СК-1', 3);
    await stockSelectionPage.expectNextButtonEnabled(5);
  });

  test('Кнопка "Изменить проект" возвращает на шаг поиска турбины', async () => {
    await searchPage.open();
    await searchPage.filterByModel('Т-110');
    await searchPage.selectTurbineByName('Т-110/120-130');

    await stockSelectionPage.clickChangeProject();

    await expect(searchPage.pageHeading).toBeVisible();
  });

  test('Переход на Шаг 3 (ввод параметров) с корректным составом выбранных клапанов', async ({ page }) => {
    await searchPage.open();
    await searchPage.filterByModel('Т-110');
    await searchPage.selectTurbineByName('Т-110/120-130');

    await stockSelectionPage.setValveQuantity('Клапан РК-1', 2);
    await stockSelectionPage.setValveQuantity('Клапан СК-1', 1);

    await stockSelectionPage.clickNext();

    await expect(page.getByRole('heading', { name: 'Параметры расчёта' })).toBeVisible();
    await expect(page.getByText(/Турбина:\s*Т-110\/120-130\s*\|\s*Выбрано клапанов:\s*2/i)).toBeVisible();
  });

  test('Отображение сообщения при пустом списке клапанов у турбины', async () => {
    await searchPage.open();
    await searchPage.filterByModel('К-300');
    await searchPage.selectTurbineByName('К-300-240');

    await stockSelectionPage.expectEmptyValvesMessageVisible();
    await stockSelectionPage.expectNextButtonDisabled();
  });
});