import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class StockSelectionPage extends BasePage {
  readonly projectHeading: Locator;
  readonly stepHeading: Locator;
  readonly changeProjectButton: Locator;
  readonly nextButton: Locator;
  readonly emptyValvesMessage: Locator;
  readonly valveListItems: Locator;

  constructor(page: Page) {
    super(page);

    this.projectHeading = page.getByRole('heading', { name: /Выбранный проект:/i });
    this.stepHeading = page.getByRole('heading', { name: /Укажите количество для необходимых клапанов/i });
    this.changeProjectButton = page.getByRole('button', { name: /Изменить проект/i });
    this.nextButton = page.getByRole('button', { name: /Далее \(Выбрано:/i });
    this.emptyValvesMessage = page.getByText('Для данного проекта клапаны не найдены.');
    
    // Элементы списка клапанов с полями ввода количества
    this.valveListItems = page.locator('li').filter({ has: page.locator('input') });
  }

  async setValveQuantity(valveNameOrIndex: string | number, quantity: number): Promise<void> {
    const item = typeof valveNameOrIndex === 'number'
      ? this.valveListItems.nth(valveNameOrIndex)
      : this.valveListItems.filter({ hasText: valveNameOrIndex }).first();

    await expect(item).toBeVisible();
    const input = item.locator('input');
    await input.fill(String(quantity));
  }

  async clickNext(): Promise<void> {
    await expect(this.nextButton).toBeEnabled();
    await this.nextButton.click();
    await this.waitForPageLoaded();
  }

  async clickChangeProject(): Promise<void> {
    await this.changeProjectButton.click();
    await this.waitForPageLoaded();
  }

  async expectValveCardVisible(valveName: string, valveType?: string): Promise<void> {
    const item = this.valveListItems.filter({ hasText: valveName }).first();
    await expect(item).toBeVisible();
    if (valveType) {
      await expect(item.getByText(valveType, { exact: true })).toBeVisible();
    }
  }

  async expectNextButtonDisabled(): Promise<void> {
    await expect(this.nextButton).toBeDisabled();
  }

  async expectNextButtonEnabled(expectedCount?: number): Promise<void> {
    await expect(this.nextButton).toBeEnabled();
    if (expectedCount !== undefined) {
      await expect(this.nextButton).toContainText(`Далее (Выбрано: ${expectedCount})`);
    }
  }

  async expectEmptyValvesMessageVisible(): Promise<void> {
    await expect(this.emptyValvesMessage).toBeVisible();
  }
}