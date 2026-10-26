import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class TurbineSearchPage extends BasePage {
  readonly pageHeading: Locator;
  readonly modelInput: Locator;
  readonly stationInput: Locator;
  readonly factoryInput: Locator;
  readonly valveInput: Locator;
  readonly clearButton: Locator;
  readonly emptyPromptText: Locator;
  readonly noResultsText: Locator;
  readonly errorBox: Locator;
  readonly resultItems: Locator;

  constructor(page: Page) {
    super(page);

    this.pageHeading = page.getByRole('heading', { name: 'Поиск проекта' });
    this.modelInput = page.getByPlaceholder('Например, Т-110');
    this.stationInput = page.getByPlaceholder('Например, Абаканская');
    this.factoryInput = page.getByPlaceholder('№');
    this.valveInput = page.getByPlaceholder('УТЗ-304414');
    this.clearButton = page.getByRole('button', { name: 'Очистить' });

    this.emptyPromptText = page.getByText('Введите параметры для поиска');
    this.noResultsText = page.getByText('Проекты не найдены. Попробуйте изменить критерии поиска.');
    this.errorBox = page.getByText('Произошла ошибка при поиске!');
    
    this.resultItems = page.locator('li').filter({ has: page.locator('h2, h3, h4') });
  }

  async open(): Promise<void> {
    await this.navigateTo('/calculator');
  }

  async filterByModel(model: string): Promise<void> {
    await this.modelInput.fill(model);
  }

  async filterByStation(station: string): Promise<void> {
    await this.stationInput.fill(station);
  }

  async filterByFactory(factory: string): Promise<void> {
    await this.factoryInput.fill(factory);
  }

  async filterByValve(valve: string): Promise<void> {
    await this.valveInput.fill(valve);
  }

  async clickClearFilters(): Promise<void> {
    await this.clearButton.click();
  }

  async selectTurbineByIndex(index: number = 0): Promise<void> {
    const item = this.resultItems.nth(index);
    await expect(item).toBeVisible();
    await item.click();
  }

  async selectTurbineByName(name: string): Promise<void> {
    const item = this.resultItems.filter({ hasText: name }).first();
    await expect(item).toBeVisible();
    await item.click();
  }

  async expectEmptyPromptVisible(): Promise<void> {
    await expect(this.emptyPromptText).toBeVisible();
  }

  async expectResultsCount(count: number): Promise<void> {
    await expect(this.resultItems).toHaveCount(count);
  }

  async expectNoResultsVisible(): Promise<void> {
    await expect(this.noResultsText).toBeVisible();
  }

  async expectErrorVisible(detailMessage?: string): Promise<void> {
    await expect(this.errorBox).toBeVisible();
    if (detailMessage) {
      await expect(this.page.getByText(detailMessage)).toBeVisible();
    }
  }
}