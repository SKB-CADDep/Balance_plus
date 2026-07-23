import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ResultMatrixPage extends BasePage {
  readonly resultsContainer: Locator;
  readonly matrixTable: Locator;
  readonly exportExcelButton: Locator;
  readonly summaryCards: Locator;

  constructor(page: Page) {
    super(page);
    this.resultsContainer = page.locator('[data-testid="results-container"], .results-matrix');
    this.matrixTable = page.locator('table.matrix-viewer, [role="grid"]');
    this.exportExcelButton = page.locator('button:has-text("Экспорт в Excel"), button:has-text("Export")');
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