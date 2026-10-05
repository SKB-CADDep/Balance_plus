import { test, expect } from '@playwright/test';
import { HeaderPage } from '../pages/HeaderPage';

test.describe('Balance Orchestrator Frontend - Auth Session & User Profile E2E', () => {
  let headerPage: HeaderPage;

  test.beforeEach(async ({ page }) => {
    headerPage = new HeaderPage(page);

    await page.route('**/api/v1/config/bureaus*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'btr',
            label: 'БТР',
            color: '#0070F3',
            modules: [{ id: 'btr-valve-stems', label: 'Штоки клапанов' }],
          },
        ]),
      });
    });

    await page.route('**/api/v1/tasks*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });
  });

  test('Успешная загрузка сессии: в шапке отображается ФИО и аватар пользователя', async ({ page }) => {
    await page.route('**/api/v1/user/me*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          name: 'Константинопольский К.',
          username: 'k.konstantinopolsky',
          avatar_url: 'https://gitlab.example.com/avatar.png',
        }),
      });
    });

    await headerPage.open();

    await headerPage.expectUserVisible('Константинопольский К.');
    await headerPage.expectAvatarLoaded();

    await expect(headerPage.logoText).toHaveText('Баланс +');
  });

  test('Перехват 401 Unauthorized: приложение не падает в белый экран при невалидной сессии', async ({ page }) => {
    await page.route('**/api/v1/user/me*', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Ошибка авторизации в GitLab' }),
      });
    });

    await headerPage.open();

    await expect(headerPage.logoText).toBeVisible();
    await expect(page.locator('.layout')).toBeVisible();

    await expect(page.getByText('Все задачи')).toBeVisible();
  });

  test('Перехват 503 Service Unavailable: обработка неконфигурированного GitLab', async ({ page }) => {
    await page.route('**/api/v1/user/me*', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Не заданы обязательные настройки GitLab' }),
      });
    });

    await headerPage.open();

    await expect(headerPage.header).toBeVisible();
    await expect(page.locator('.task-grid')).toBeVisible();
  });

  test('Кнопка "↻ Обновить" инициирует повторный опрос эндпоинта пользователя', async ({ page }) => {
    let userRequestsCount = 0;

    await page.route('**/api/v1/user/me*', async (route) => {
      userRequestsCount++;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          name: 'Инженер УТЗ',
          username: 'engineer',
          avatar_url: '',
        }),
      });
    });

    await headerPage.open();
    await headerPage.expectUserVisible('Инженер УТЗ');
    expect(userRequestsCount).toBe(1);

    const refreshBtn = page.getByRole('button', { name: /Обновить/i });
    await expect(refreshBtn).toBeVisible();
    await refreshBtn.click();

    await expect.poll(() => userRequestsCount).toBe(2);
  });
});