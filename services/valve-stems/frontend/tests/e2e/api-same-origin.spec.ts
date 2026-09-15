import { expect, test } from '@playwright/test';

test('Empty API base sends search to the frontend origin without duplicating /api', async ({ page }) => {
    await page.route('**/api/v1/turbines/search*', async (route) => {
        await route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
    });
    await page.goto('/calculator');
    const requestPromise = page.waitForRequest((request) =>
        new URL(request.url()).pathname.endsWith('/turbines/search'));
    await page.getByPlaceholder('Например, Т-110').fill('Т-110');
    const request = await requestPromise;
    const url = new URL(request.url());
    expect(url.origin).toBe(new URL(page.url()).origin);
    expect(url.pathname).toBe('/api/v1/turbines/search');
    expect(url.searchParams.get('q')).toBe('Т-110');
});
