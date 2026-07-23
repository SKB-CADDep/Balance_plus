import { test, expect } from '@playwright/test';
import { CondenserFormPage } from './pages/CondenserFormPage';

test.describe('Condenser Calculator - E2E Тесты', () => {
  let formPage: CondenserFormPage;

  test.beforeEach(async ({ page }) => {
    formPage = new CondenserFormPage(page);
    await formPage.open();
  });

  test('Должна успешно отображаться страница и кнопка расчета', async () => {
    await expect(formPage.calculateButton).toBeVisible();
  });

  test('Визуальный регресс: проверка внешнего вида формы', async () => {
    await formPage.assertPageMatchScreenshot('condenser-form.png');
  });
});