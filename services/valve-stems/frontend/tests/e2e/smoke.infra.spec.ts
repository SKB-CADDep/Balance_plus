import { test, expect } from '@playwright/test';
import { MainPage } from '../pages/MainPage';
import { setupValveStemsApiMocks } from '../mocks/api-mocks';

test.describe('Valve Stems Frontend - Infrastructure Smoke Test', () => {
  let mainPage: MainPage;

  test.beforeEach(async ({ page }) => {
    mainPage = new MainPage(page);
    // Настройка моков сетевых запросов
    await setupValveStemsApiMocks(page);
  });

  test('Инфраструктура тестов исправна: страница открывается на порту 3001 без ошибок', async ({ page }) => {
    // 1. Переходим на главную страницу
    await mainPage.open();

    // 2. Проверяем, что заголовок видимый и страница загружена
    await mainPage.expectHeadingVisible();

    // 3. Проверяем корректный URL (согласованный порт 3001)
    expect(page.url()).toContain('3001');
  });
});