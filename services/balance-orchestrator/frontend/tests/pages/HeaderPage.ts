import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class HeaderPage {
  readonly page: Page;
  readonly header: Locator;
  readonly logoText: Locator;
  readonly profileName: Locator;
  readonly avatar: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.locator('header.top-bar');
    this.logoText = page.locator('.logo-text');
    this.profileName = page.locator('.profile-name');
    this.avatar = page.locator('.avatar');
    this.logoutButton = page.locator('.logout-btn');
  }

  async open(path: string = '/'): Promise<void> {
    await this.page.goto(path);
    await this.page.waitForLoadState('domcontentloaded');
  }

  async expectUserVisible(name: string): Promise<void> {
    await expect(this.profileName).toBeVisible();
    await expect(this.profileName).toHaveText(name);
  }

  async expectAvatarLoaded(): Promise<void> {
    await expect(this.avatar).toBeVisible();
  }

  async clickLogout(): Promise<void> {
    await this.logoutButton.click();
  }
}