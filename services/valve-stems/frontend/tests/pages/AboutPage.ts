import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class AboutPage extends BasePage {
  readonly pageHeading: Locator;
  readonly pageContent: Locator;

  constructor(page: Page) {
    super(page);
    this.pageHeading = page.locator('h1, h2').first();
    this.pageContent = page.locator('main, [data-testid="about-page"], .chakra-container').first();
  }

  async open(): Promise<void> {
    await this.navigateTo('/about');
  }

  async expectLoaded(): Promise<void> {
    await expect(this.pageHeading).toBeVisible();
    await expect(this.pageContent).toBeVisible();
  }
}