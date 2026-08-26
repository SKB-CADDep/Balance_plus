/// <reference types="node" />
import { test, expect } from '@playwright/test';
import fs from 'fs';
import { TurbineSearchPage } from '../pages/TurbineSearchPage';
import { StockSelectionPage } from '../pages/StockSelectionPage';
import { StockInputPage } from '../pages/StockInputPage';
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

test.describe('Valve Stems Calculator - Step 3: Stock Input & Calculation', () => {
  let searchPage: TurbineSearchPage;
  let stockSelectionPage: StockSelectionPage;
  let stockInputPage: StockInputPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new TurbineSearchPage(page);
    stockSelectionPage = new StockSelectionPage(page);
    stockInputPage = new StockInputPage(page);

    // Мок поиска турбин
    await page.route(/turbines.*search/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockTurbines),
      });
    });

    // Мок списка клапанов
    await page.route(/valves/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockValves),
      });
    });

    // Мок единиц измерения
    await page.route(/units/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockUnits),
      });
    });

    // Переходим на Шаг 3 перед каждым тестом
    await navigateToStep3WithSelectedValves(searchPage, stockSelectionPage);
  });

  test('Отображение дефолтных значений и полей глобальных параметров', async () => {
    await expect(stockInputPage.pageHeading).toBeVisible();
    await expect(stockInputPage.subtitleInfo).toContainText('Турбина: Т-110/120-130 | Выбрано клапанов: 2');

    // Проверка дефолтных значений
    await expect(stockInputPage.pFreshInput).toHaveValue('130');
    await expect(stockInputPage.pFreshUnitSelect).toHaveValue('кгс/см²');
    await expect(stockInputPage.thInput).toHaveValue('555');
    await expect(stockInputPage.thUnitSelect).toHaveValue('°C');
    await expect(stockInputPage.pAirInput).toHaveValue('1.033');
    await expect(stockInputPage.tAirInput).toHaveValue('20');
    await expect(stockInputPage.pLstLeakOffInput).toHaveValue('0.97');
    await expect(stockInputPage.radioTemperature).toBeChecked();
  });

  test('Переключение режима T ↔ H (температура и энтальпия)', async () => {
    // По умолчанию режим "Температура" (значение 555 °C)
    await expect(stockInputPage.radioTemperature).toBeChecked();
    await expect(stockInputPage.thInput).toHaveValue('555');
    await expect(stockInputPage.thUnitSelect).toHaveValue('°C');

    // Переключаем на "Энтальпия"
    await stockInputPage.selectEnthalpyMode();
    await expect(stockInputPage.radioEnthalpy).toBeChecked();

    // Возвращаем на "Температура"
    await stockInputPage.selectTemperatureMode();
    await expect(stockInputPage.radioTemperature).toBeChecked();
    await expect(stockInputPage.thInput).toHaveValue('555');
  });

  test('Число полей промежуточных отсосов соответствует геометрии клапанов', async () => {
    // Клапан 1: count_parts=3 -> 1 промежуточный отсос
    // Клапан 2: count_parts=4 -> 2 промежуточных отсоса
    // Итого должно быть ровно 3 поля ввода камер
    await expect(stockInputPage.intermediateChamberInputs).toHaveCount(3);
  });

  test('Валидация полей: пустое поле, не-число и точность более 4 знаков', async () => {
    // 1. Пустое поле -> нажимаем "Рассчитать" -> Ошибка "Обязательно"
    await stockInputPage.pFreshInput.fill('');
    await stockInputPage.clickCalculate();
    await stockInputPage.expectValidationErrorMessage('Обязательно');

    // 2. Не-число -> нажимаем "Рассчитать" -> Ошибка "Неверный формат"
    await stockInputPage.pFreshInput.fill('abc');
    await stockInputPage.clickCalculate();
    await stockInputPage.expectValidationErrorMessage('Неверный формат');

    // 3. Точность более 4 знаков (130.12345) -> Ошибка "Неверный формат"
    await stockInputPage.pFreshInput.fill('130.12345');
    await stockInputPage.clickCalculate();
    await stockInputPage.expectValidationErrorMessage('Неверный формат');

    // 4. Корректная точность 4 знака (130.1234) -> Валидно, ошибка исчезает
    await stockInputPage.pFreshInput.fill('130.1234');
    await stockInputPage.clickCalculate();
    await expect(stockInputPage.errorMessages.filter({ hasText: 'Неверный формат' })).toHaveCount(0);
  });

  test('Смена единиц измерения через dropdown и отправка корректного MultiCalculationParams', async ({ page }) => {
    let capturedPayload: any = null;

    // Мок эндпоинта расчёта
    await page.route(/calc/, async (route) => {
      capturedPayload = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          id: 123,
          results: { total_leakage: 0.12 },
        }),
      });
    });

    // 1. Меняем единицы давления свежего пара на МПа
    await stockInputPage.setPFresh('12.5', 'МПа');

    // 2. Заполняем обязательные промежуточные давления в камерах
    await stockInputPage.setIntermediatePressure(0, '15'); // Клапан 1, Камера 1
    await stockInputPage.setIntermediatePressure(1, '10'); // Клапан 2, Камера 1
    await stockInputPage.setIntermediatePressure(2, '5');  // Клапан 2, Камера 2

    // 3. Отправляем расчёт
    await stockInputPage.clickCalculate();

    // Проверяем структуру отправленного MultiCalculationParams
    expect(capturedPayload).not.toBeNull();
    expect(capturedPayload.turbine_id).toBe(1);
    expect(capturedPayload.globals.P_fresh).toBe(12.5);
    expect(capturedPayload.globals.P_fresh_unit).toBe('МПа');
    expect(capturedPayload.globals.T_fresh).toBe(555);
    expect(capturedPayload.groups).toHaveLength(2);
    expect(capturedPayload.groups[0].quantity).toBe(2);
    expect(capturedPayload.groups[1].quantity).toBe(1);

    // Проверяем переход на экран результатов
    await expect(page.getByText(/Расчет выполнен успешно/i)).toBeVisible();
  });

  test('Кнопка "Изменить состав клапанов" возвращает на Шаг 2', async () => {
    await stockInputPage.clickChangeValves();

    // Проверяем возврат к экрану выбора клапанов
    await expect(stockSelectionPage.projectHeading).toBeVisible();
    await expect(stockSelectionPage.stepHeading).toBeVisible();
  });
});