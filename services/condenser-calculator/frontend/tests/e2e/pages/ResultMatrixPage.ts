import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ResultMatrixPage extends BasePage {
  readonly resultsContainer: Locator;
  readonly matrixTable: Locator;
  readonly exportExcelButton: Locator;
  readonly summaryCards: Locator;

  constructor(page: Page) {
    super(page);

    this.resultsContainer = page.locator(
      '[data-testid="results-container"], .results-matrix, table, h2:has-text("Результаты")'
    ).first();

    this.matrixTable = page.locator('table').first();

    this.exportExcelButton = page.locator(
      'button:has-text("Экспорт"), button:has-text("Excel"), button:has-text("Export"), button:has-text("Скачать")'
    ).first();

    this.summaryCards = page.locator('.summary-card, [data-testid="summary-card"]');
  }

  async expectResultsLoaded(): Promise<void> {
    await expect(this.resultsContainer).toBeVisible({ timeout: 10000 });
  }

  async getSummaryValue(label: string): Promise<string> {
    const card = this.summaryCards.filter({ hasText: label });
    return (await card.textContent()) || '';
  }

  async clickExportExcel(): Promise<void> {
    await this.exportExcelButton.click();
  }
}