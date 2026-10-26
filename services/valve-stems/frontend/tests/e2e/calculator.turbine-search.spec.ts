/// <reference types="node" />
import { test, expect } from '@playwright/test';
import fs from 'fs';
import { TurbineSearchPage } from '../pages/TurbineSearchPage';

const mockTurbines = JSON.parse(
  fs.readFileSync(new URL('../mocks/turbines-search.json', import.meta.url), 'utf-8')
);

test.describe('Valve Stems Calculator - Step 1: Turbine Search', () => {
  let searchPage: TurbineSearchPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new TurbineSearchPage(page);
  });

  test('Пустое состояние: без ввода фильтров запрос к API не отправляется', async ({ page }) => {
    let apiRequested = false;
    await page.route('**/api/v1/turbines/search*', async (route) => {
      apiRequested = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTurbines),
      });
    });

    await searchPage.open();
    await expect(searchPage.pageHeading).toBeVisible();
    await searchPage.expectEmptyPromptVisible();

    await page.waitForTimeout(600);
    expect(apiRequested).toBeFalsy();
  });

  test('Поиск по марке турбины: отправляется запрос с debounce и отображаются результаты', async ({ page }) => {
    await page.route('**/api/v1/turbines/search*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTurbines),
      });
    });

    await searchPage.open();
    await searchPage.filterByModel('Т-110');

    // Проверяем отображение карточек результатов
    await searchPage.expectResultsCount(2);
    await expect(page.getByRole('heading', { name: 'Т-110/120-130' })).toBeVisible();
    await expect(page.getByText('Абаканская ТЭЦ')).toBeVisible();
  });

  test('Фильтрация по нескольким полям (станция, заводской номер, чертеж клапана)', async ({ page }) => {
    let capturedQuery: string | null = null;

    await page.route('**/api/v1/turbines/search*', async (route) => {
      capturedQuery = route.request().url();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([mockTurbines[0]]),
      });
    });

    await searchPage.open();
    await searchPage.filterByStation('Абаканская');
    await searchPage.filterByFactory('10452');
    await searchPage.filterByValve('УТЗ-304414');

    // Ждем выполнения дебаунса и ответа API
    await searchPage.expectResultsCount(1);

    expect(capturedQuery).toContain('station=%D0%90%D0%B1%D0%B0%D0%BA%D0%B0%D0%BD%D1%81%D0%BA%D0%B0%D1%8F');
    expect(capturedQuery).toContain('factory=10452');
    expect(capturedQuery).toContain('valve=%D0%A3%D0%A2%D0%97-304414');
  });

  test('Кнопка "Очистить" сбрасывает все поля ввода и возвращает стартовое состояние', async ({ page }) => {
    await page.route('**/api/v1/turbines/search*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTurbines),
      });
    });

    await searchPage.open();
    await searchPage.filterByModel('Т-110');
    await searchPage.expectResultsCount(2);

    // Нажимаем кнопку очистки
    await searchPage.clickClearFilters();

    // Проверяем, что инпуты пусты и снова видна стартовая подсказка
    await expect(searchPage.modelInput).toHaveValue('');
    await searchPage.expectEmptyPromptVisible();
  });

  test('Выбор турбины: клик по карточке переводит на шаг выбора клапанов', async ({ page }) => {
    await page.route('**/api/v1/turbines/search*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTurbines),
      });
    });

    // Мок получения клапанов выбранной турбины при переходе на шаг stockSelection
    await page.route('**/api/v1/turbines/1/valves*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTurbines[0].valves),
      });
    });

    await searchPage.open();
    await searchPage.filterByModel('Т-110');

    // Кликаем по первой найденной турбине
    await searchPage.selectTurbineByName('Т-110/120-130');

    await expect(searchPage.pageHeading).not.toBeVisible();
    await expect(page.getByText(/Т-110\/120-130/i).first()).toBeVisible();
  });

  test('Обработка ошибок API: при 500 ошибке сервера отображается сообщение и UI не виснет', async ({ page }) => {
    await page.route('**/api/v1/turbines/search*', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Внутренняя ошибка сервера при поиске' }),
      });
    });

    await searchPage.open();
    await searchPage.filterByModel('Любая турбина');

    // Проверяем отображение блока ошибки с текстом от бэкенда
    await searchPage.expectErrorVisible('Внутренняя ошибка сервера при поиске');
  });

  test('Отображение состояния "Проекты не найдены" при пустом результате поиска', async ({ page }) => {
    await page.route('**/api/v1/turbines/search*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await searchPage.open();
    await searchPage.filterByModel('НесуществующаяТурбина999');

    await searchPage.expectNoResultsVisible();
  });
});