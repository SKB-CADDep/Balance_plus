import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ResultsPage extends BasePage {
  readonly pageHeading: Locator;
  readonly backButton: Locator;
  readonly excelButton: Locator;
  readonly drawioButtons: Locator;

  readonly table1Heading: Locator;
  readonly table2Heading: Locator;
  readonly summaryTableHeading: Locator;

  readonly deaeratorBadges: Locator;
  readonly ejectorBadges: Locator;

  constructor(page: Page) {
    super(page);

    this.pageHeading = page.getByRole('heading', { name: /Результаты расчета:/i });
    this.backButton = page.getByRole('button', { name: 'Изменить параметры расчета' });
    this.excelButton = page.getByRole('button', { name: 'Скачать Excel' });
    this.drawioButtons = page.getByRole('button', { name: 'Схема' });

    this.table1Heading = page.getByText('Таблица 1 - Основные параметры участков');
    this.table2Heading = page.getByText(/Таблица 2 - Потребители/i);
    this.summaryTableHeading = page.getByRole('heading', { name: 'Итоговая сводная таблица отсосов' });

    this.deaeratorBadges = page.locator('.chakra-badge').filter({ hasText: 'Деаэратор' });
    this.ejectorBadges = page.locator('.chakra-badge').filter({ hasText: /Отсос №/ });
  }

  async expectResultsLoaded(): Promise<void> {
    await expect(this.pageHeading).toBeVisible();
    await expect(this.summaryTableHeading).toBeVisible();
  }

  async expectTablesVisible(): Promise<void> {
    await expect(this.table1Heading.first()).toBeVisible();
    await expect(this.table2Heading.first()).toBeVisible();
    await expect(this.summaryTableHeading).toBeVisible();
  }

  async clickDownloadExcel(): Promise<void> {
    await this.excelButton.click();
  }

  async clickDownloadDrawio(index: number = 0): Promise<void> {
    const btn = this.drawioButtons.nth(index);
    await expect(btn).toBeVisible();
    await btn.click();
  }

  async clickBack(): Promise<void> {
    await this.backButton.click();
    await this.waitForPageLoaded();
  }
}