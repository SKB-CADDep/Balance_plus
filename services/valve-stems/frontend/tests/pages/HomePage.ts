import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class HomePage extends BasePage {
  readonly mainHeading: Locator;
  readonly ctaStartButton: Locator;
  readonly featureCardsHeadings: Locator;
  readonly calculatorFeatureButton: Locator;
  readonly aboutFeatureButton: Locator;
  readonly helpFeatureButton: Locator;

  constructor(page: Page) {
    super(page);

    // Заголовок "Добро пожаловать в WSAPropertiesCalculator"
    this.mainHeading = page.getByRole('heading', { name: /Добро пожаловать в/i }).first();
    
    // Кнопка CTA "Начать расчет"
    this.ctaStartButton = page.getByRole('link', { name: 'Начать расчет' }).first();

    // Заголовки feature-карточек
    this.featureCardsHeadings = page.getByRole('heading', { level: 3 });

    // Кнопки на самих карточках
    this.calculatorFeatureButton = page.getByRole('link', { name: 'К калькулятору' }).first();
    this.aboutFeatureButton = page.getByRole('link', { name: 'Подробнее' }).first();
    this.helpFeatureButton = page.getByRole('link', { name: 'Перейти в Помощь' }).first();
  }

  async open(): Promise<void> {
    await this.navigateTo('/');
  }

  async clickStartCalculation(): Promise<void> {
    await this.ctaStartButton.click();
    await this.waitForPageLoaded();
  }

  async expectLoaded(): Promise<void> {
    await expect(this.mainHeading).toBeVisible();
    await expect(this.ctaStartButton).toBeVisible();
    await expect(this.featureCardsHeadings).toHaveCount(3);
  }
}