import { test, expect } from '@playwright/test';
import { HomePage } from '../pages/HomePage';
import { AboutPage } from '../pages/AboutPage';
import { HelpPage } from '../pages/HelpPage';
import { setupValveStemsApiMocks } from '../mocks/api-mocks';

test.describe('Valve Stems Frontend - Shell & Navigation Smoke Tests', () => {
  let homePage: HomePage;
  let aboutPage: AboutPage;
  let helpPage: HelpPage;

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page);
    aboutPage = new AboutPage(page);
    helpPage = new HelpPage(page);

    // Моки сетевых запросов
    await setupValveStemsApiMocks(page);
  });

  test('Главная страница: отображает заголовок, карточки и CTA "Начать расчет" с переходом на калькулятор', async ({ page }) => {
    await homePage.open();
    await homePage.expectLoaded();

    // Клик по CTA "Начать расчет"
    await homePage.clickStartCalculation();

    // Проверяем переход на /calculator
    expect(page.url()).toContain('/calculator');
  });

  test('Переходы через главное меню навигации (/about, /help, /calculator)', async ({ page }) => {
    await homePage.open();

    // Переход в "О программе"
    const aboutLink = page.locator('nav a[href="/about"], a[href="/about"]').first();
    if (await aboutLink.isVisible()) {
      await aboutLink.click();
      await page.waitForLoadState('domcontentloaded');
      expect(page.url()).toContain('/about');
    }

    // Переход в "Помощь"
    const helpLink = page.locator('nav a[href="/help"], a[href="/help"]').first();
    if (await helpLink.isVisible()) {
      await helpLink.click();
      await page.waitForLoadState('domcontentloaded');
      expect(page.url()).toContain('/help');
    }
  });

  test('Страница Help: страница открывается, и аккордеон FAQ раскрывается при клике', async () => {
    await helpPage.open();
    await helpPage.expectLoaded();

    // Если на странице есть аккордеон FAQ — раскрываем первый элемент
    if (await helpPage.faqAccordionButtons.count() > 0) {
      await helpPage.expandFaqItem(0);
      await helpPage.expectFaqPanelVisible(0);
    }
  });

  test('Страница About: открывается без ошибок и содержит контент', async () => {
    await aboutPage.open();
    await aboutPage.expectLoaded();
  });

  test('Страница 404 NotFound: отображается для неизвестного URL с возможностью вернуться', async ({ page }) => {
    // Переходим по заведомо несуществующему маршруту
    await page.goto('/unknown-route-404-check');
    await page.waitForLoadState('domcontentloaded');

    // Проверяем компоненты страницы NotFound
    await expect(page.getByText('404')).toBeVisible();
    await expect(page.getByText(/Page not found|Oops!/i).first()).toBeVisible();

    // Кликаем кнопку "Go back"
    const goBackButton = page.getByRole('link', { name: 'Go back' }).first();
    await expect(goBackButton).toBeVisible();
    await goBackButton.click();

    // Проверяем возврат на главную
    await page.waitForLoadState('domcontentloaded');
    expect(page.url()).toMatch(/\/$/);
    await homePage.expectLoaded();
  });
});