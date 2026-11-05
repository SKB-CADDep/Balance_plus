import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class MainPage extends BasePage {
  readonly mainHeading: Locator;
  readonly searchInput: Locator;

  constructor(page: Page) {
    super(page);
    this.mainHeading = page.locator('h1, h2, h3').first();
    this.searchInput = page.getByRole('textbox').first();
  }

  async open(): Promise<void> {
    await this.navigateTo('/');
  }

  async expectHeadingVisible(): Promise<void> {
    await expect(this.mainHeading).toBeVisible();
  }
}