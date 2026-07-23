import { Page, Locator, expect } from '@playwright/test';

export abstract class BasePage {
  readonly page: Page;
  readonly headerLogo: Locator;
  readonly themeToggleBtn: Locator;
  readonly navHelpLink: Locator;
  readonly navAboutLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.headerLogo = page.locator('header img, header [data-testid="logo"]');
    this.themeToggleBtn = page.locator('button[aria-label*="theme"], button:has-text("Тема")');
    this.navHelpLink = page.locator('nav a[href="/help"]');
    this.navAboutLink = page.locator('nav a[href="/about"]');
  }

  async navigateTo(path: string = '/'): Promise<void> {
    await this.page.goto(path);
    await this.waitForPageLoaded();
  }

  async waitForPageLoaded(): Promise<void> {
    await this.page.waitForLoadState('domcontentloaded');
    await this.page.waitForLoadState('networkidle');
  }

  async assertPageMatchScreenshot(snapshotName: string): Promise<void> {
    await expect(this.page).toHaveScreenshot(snapshotName);
  }

  async toggleTheme(): Promise<void> {
    await this.themeToggleBtn.click();
  }
}