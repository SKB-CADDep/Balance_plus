import { Page, Locator, expect } from '@playwright/test';

export abstract class BasePage {
  readonly page: Page;
  readonly headerLogo: Locator;
  readonly navHelpLink: Locator;
  readonly navAboutLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.headerLogo = page.locator('header img, header [data-testid="logo"]').first();
    this.navHelpLink = page.locator('a[href="/help"]').first();
    this.navAboutLink = page.locator('a[href="/about"]').first();
  }

  async navigateTo(path: string = '/'): Promise<void> {
    await this.page.goto(path);
    await this.waitForPageLoaded();
  }

  async waitForPageLoaded(): Promise<void> {
    await this.page.waitForLoadState('domcontentloaded');
    await this.page.waitForLoadState('networkidle');
  }

  async assertPageLoaded(): Promise<void> {
    await expect(this.page).not.toHaveURL(/error/);
  }
}