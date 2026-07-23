import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export interface CondenserFormData {
  steamFlow?: string;         // Расход пара (т/ч)
  coolingWaterTemp?: string;  // Температура охлаждающей воды (°C)
  waterFlowRate?: string;     // Расход охлаждающей воды (м³/ч)
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
    this.pageTitle = page.locator('h1, h2').filter({ hasText: /Расчет конденсатора|Condenser/i });
    this.condenserSelect = page.locator('select[name="condenser_id"], [data-testid="condenser-select"]');
    this.steamFlowInput = page.locator('input[name="steam_flow"], input[id="steamFlow"]');
    this.coolingWaterTempInput = page.locator('input[name="water_temp"], input[id="waterTemp"]');
    this.waterFlowRateInput = page.locator('input[name="water_flow"], input[id="waterFlow"]');
    this.materialSelect = page.locator('select[name="material_id"], [data-testid="material-select"]');
    this.calculateButton = page.locator('button[type="submit"]:has-text("Рассчитать"), button:has-text("Calculate")');
    this.errorMessage = page.locator('.error-message, [role="alert"]');
  }

  async open(): Promise<void> {
    await this.navigateTo('/calculator');
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
      await this.materialSelect.selectOption(data.materialId);
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