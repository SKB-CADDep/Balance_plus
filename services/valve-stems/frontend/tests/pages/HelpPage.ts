import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class HelpPage extends BasePage {
  readonly pageHeading: Locator;
  readonly faqAccordionButtons: Locator;
  readonly faqAccordionPanels: Locator;

  constructor(page: Page) {
    super(page);
    this.pageHeading = page.locator('h1, h2').first();
    this.faqAccordionButtons = page.locator('button.chakra-accordion__button, button[aria-expanded]');
    this.faqAccordionPanels = page.locator('.chakra-accordion__panel, [role="region"]');
  }

  async open(): Promise<void> {
    await this.navigateTo('/help');
  }

  async expandFaqItem(index: number = 0): Promise<void> {
    const button = this.faqAccordionButtons.nth(index);
    await button.click();
  }

  async expectFaqPanelVisible(index: number = 0): Promise<void> {
    const panel = this.faqAccordionPanels.nth(index);
    await expect(panel).toBeVisible();
  }

  async expectLoaded(): Promise<void> {
    await expect(this.pageHeading).toBeVisible();
  }
}