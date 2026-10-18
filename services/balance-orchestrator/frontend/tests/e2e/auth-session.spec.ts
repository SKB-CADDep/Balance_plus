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
        body: JSON.stringify([{ id: 'btr', label: 'БТР', color: '#0070F3', modules: [] }]),
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

  test('Сохранение токена в localStorage и отображение профиля пользователя', async ({ page }) => {
    await headerPage.open();
    await page.evaluate(() => localStorage.setItem('authToken', 'valid-mock-token-xyz'));

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
    const token = await page.evaluate(() => localStorage.getItem('authToken'));
    expect(token).toBe('valid-mock-token-xyz');

    await headerPage.expectUserVisible('Константинопольский К.');
    await headerPage.expectAvatarLoaded();
  });

  test('Перехват 401 Unauthorized: очистка токена и редирект на экран входа с сохранением исходного URL', async ({ page }) => {
    await headerPage.open();
    await page.evaluate(() => localStorage.setItem('authToken', 'expired-mock-token'));

    await page.route('**/api/v1/user/me*', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Ошибка авторизации в GitLab' }),
      });
    });

    // Открываем URL с параметрами
    await headerPage.open('/?bureau=btr');

    // Проверяем редирект на /login с сохранением redirect URL
    await expect.poll(() => page.url()).toContain('/login');
    expect(page.url()).toContain('redirect=');

    // Проверяем очистку токена
    const token = await page.evaluate(() => localStorage.getItem('authToken'));
    expect(token).toBeNull();
  });

  test('Выход из системы (Logout): очищает токен из localStorage и перенаправляет на экран логина', async ({ page }) => {
    await page.route('**/api/v1/user/me*', async (route) => {
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
    await page.evaluate(() => localStorage.setItem('authToken', 'active-session-token'));
    await headerPage.expectUserVisible('Инженер УТЗ');

    // Нажимаем «Выйти»
    await headerPage.clickLogout();

    // Проверяем редирект
    await expect.poll(() => page.url()).toContain('/login');

    // Проверяем удаление токена
    const token = await page.evaluate(() => localStorage.getItem('authToken'));
    expect(token).toBeNull();
  });
});