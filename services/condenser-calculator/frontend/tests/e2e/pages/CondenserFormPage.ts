import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export interface CondenserFormData {
  steamFlow?: string;         // Расход пара (G_steam)
  coolingWaterTemp?: string;  // Температура воды вход (t1_main)
  waterFlowRate?: string;     // Расход воды (W_main)
  materialId?: string;        // Материал трубок
}

export class CondenserFormPage extends BasePage {
  readonly pageTitle: Locator;
  readonly condenserSelect: Locator;
  readonly steamFlowInput: Locator;
  readonly coolingWaterTempInput: Locator;
  readonly waterFlowRateInput: Locator;
  readonly materialSelect: Locator;
  readonly calculateButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    super(page);

    this.pageTitle = page.getByRole('heading', { name: /Калькулятор|Расч[её]т|Condenser/i }).first();
    this.condenserSelect = page.getByRole('combobox', { name: /Конденсатор/i }).first();
    this.steamFlowInput = page.getByRole('textbox', { name: /Расход пара/i }).first();
    this.coolingWaterTempInput = page.getByRole('textbox', { name: /Темп\. воды вход/i }).first();
    this.waterFlowRateInput = page.getByRole('textbox', { name: /Расход воды \(W_main\)|W_main/i }).first();
    this.materialSelect = page.getByRole('combobox', { name: /Материал трубок/i }).first();
    this.calculateButton = page.getByRole('button', { name: /Рассчитать|Calculate/i }).first();
    this.errorMessage = page.locator('.error-message, [role="alert"]').first();
  }

  async open(): Promise<void> {
    await this.navigateTo('/');

    const selectCondenserBtn = this.page.locator(
      'button:has-text("Выбрать"), [data-testid="select-condenser"], .condenser-card button, a[href*="calculator"]'
    ).first();

    if (await selectCondenserBtn.isVisible()) {
      await selectCondenserBtn.click();
    } else {
      const startCalcBtn = this.page.locator('button:has-text("Рассчитать"), button:has-text("Перейти к расчету")').first();
      if (await startCalcBtn.isVisible()) {
        await startCalcBtn.click();
      }
    }

    await this.waitForPageLoaded();
  }

  async fillForm(data: CondenserFormData): Promise<void> {
    if (data.steamFlow) {
      await this.steamFlowInput.fill(data.steamFlow);
    }
    if (data.coolingWaterTemp) {
      await this.coolingWaterTempInput.fill(data.coolingWaterTemp);
    }
    if (data.waterFlowRate) {
      await this.waterFlowRateInput.fill(data.waterFlowRate);
    }
    if (data.materialId) {
      try {
        await this.materialSelect.selectOption({ label: data.materialId });
      } catch {
        await this.materialSelect.selectOption(data.materialId);
      }
    }
  }

  async submitCalculation(): Promise<void> {
    await this.calculateButton.click();
  }

  async performCalculation(data: CondenserFormData): Promise<void> {
    await this.fillForm(data);
    await this.submitCalculation();
  }

  async expectValidationError(expectedText?: string | RegExp): Promise<void> {
    await expect(this.errorMessage).toBeVisible();
    if (expectedText) {
      await expect(this.errorMessage).toContainText(expectedText);
    }
  }
}