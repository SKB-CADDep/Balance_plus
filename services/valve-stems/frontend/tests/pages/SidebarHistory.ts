import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class SidebarHistory extends BasePage {
  readonly openSidebarButton: Locator;
  readonly drawerHeading: Locator;
  readonly drawerCloseButton: Locator;
  readonly emptyHistoryText: Locator;
  readonly clearAllButton: Locator;
  readonly historyEntryItems: Locator;
  readonly deleteEntryButtons: Locator;

  constructor(page: Page) {
    super(page);

    this.openSidebarButton = page.getByRole('button', { name: /Открыть историю расчетов/i });
    this.drawerHeading = page.getByRole('heading', { name: 'История' });
    this.drawerCloseButton = page.locator('.chakra-modal__close-btn, button[aria-label="Close"]').first();
    this.emptyHistoryText = page.getByText('История расчетов пуста.');
    this.clearAllButton = page.getByRole('button', { name: 'Очистить всю историю' });

    this.historyEntryItems = page.locator('div[role="button"]').filter({ has: page.getByRole('button', { name: 'Удалить запись' }) });
    this.deleteEntryButtons = page.getByRole('button', { name: 'Удалить запись' });
  }

  async openSidebar(): Promise<void> {
    await this.openSidebarButton.click();
    await expect(this.drawerHeading).toBeVisible();
  }

  async closeSidebar(): Promise<void> {
    await this.drawerCloseButton.click();
    await expect(this.drawerHeading).not.toBeVisible();
  }

  async clickHistoryEntry(index: number = 0): Promise<void> {
    const item = this.historyEntryItems.nth(index);
    await expect(item).toBeVisible();
    await item.click();
    await this.waitForPageLoaded();
  }

  async deleteHistoryEntry(index: number = 0): Promise<void> {
    const btn = this.deleteEntryButtons.nth(index);
    await expect(btn).toBeVisible();
    await btn.click();
  }

  async clickClearAll(): Promise<void> {
    await expect(this.clearAllButton).toBeVisible();
    await this.clearAllButton.click();
  }

  async expectHistoryCount(count: number): Promise<void> {
    await expect(this.historyEntryItems).toHaveCount(count);
  }

  async expectEmptyHistory(): Promise<void> {
    await expect(this.emptyHistoryText).toBeVisible();
  }

  async expectEntryVisible(stockName: string, turbineName?: string): Promise<void> {
    const item = this.historyEntryItems.filter({ hasText: stockName }).first();
    await expect(item).toBeVisible();
    if (turbineName) {
      await expect(item.getByText(turbineName)).toBeVisible();
    }
  }
}