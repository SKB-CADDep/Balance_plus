import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class StockInputPage extends BasePage {
  readonly pageHeading: Locator;
  readonly subtitleInfo: Locator;
  readonly changeValvesButton: Locator;
  readonly calculateButton: Locator;

  readonly radioTemperature: Locator;
  readonly radioEnthalpy: Locator;

  readonly pFreshInput: Locator;
  readonly pFreshUnitSelect: Locator;

  readonly thBox: Locator;
  readonly thInput: Locator;
  readonly thUnitSelect: Locator;

  readonly pAirInput: Locator;
  readonly tAirInput: Locator;
  readonly pLstLeakOffInput: Locator;

  readonly intermediateChamberInputs: Locator;
  readonly errorMessages: Locator;

  constructor(page: Page) {
    super(page);

    this.pageHeading = page.getByRole('heading', { name: 'Параметры расчёта' });
    this.subtitleInfo = page.getByText(/Турбина:.*\|.*Выбрано клапанов:/i);
    this.changeValvesButton = page.getByRole('button', { name: 'Изменить состав клапанов' });
    this.calculateButton = page.getByRole('button', { name: 'Рассчитать' });

    // Ролевые локаторы радиокнопок
    this.radioTemperature = page.getByRole('radio', { name: 'Температура' });
    this.radioEnthalpy = page.getByRole('radio', { name: 'Энтальпия' });

    // Давление свежего пара
    const pFreshControl = page.locator('.chakra-form-control').filter({ hasText: 'Давление свежего пара' }).first();
    this.pFreshInput = pFreshControl.locator('input').first();
    this.pFreshUnitSelect = pFreshControl.locator('select').first();

    // Блок переключения Температура / Энтальпия (Box с RadioGroup)
    this.thBox = page.getByRole('radiogroup').locator('..');
    this.thInput = this.thBox.locator('input[type="text"], input.chakra-input').first();
    this.thUnitSelect = this.thBox.locator('select').first();

    // Давление воздуха
    const pAirControl = page.locator('.chakra-form-control').filter({ hasText: 'Давление воздуха' }).first();
    this.pAirInput = pAirControl.locator('input').first();

    // Температура воздуха
    const tAirControl = page.locator('.chakra-form-control').filter({ hasText: 'Температура воздуха' }).first();
    this.tAirInput = tAirControl.locator('input').first();

    // Давление последнего отсоса
    const pLstControl = page.locator('.chakra-form-control').filter({ hasText: 'Давление последнего отсоса' }).first();
    this.pLstLeakOffInput = pLstControl.locator('input').first();

    // Промежуточные камеры
    this.intermediateChamberInputs = page.locator('.chakra-form-control').filter({ hasText: /Давление в камере \d+:/ }).locator('input');
    this.errorMessages = page.locator('.chakra-form__error-message, [role="alert"], div[id*="feedback"]');
  }

  async selectTemperatureMode(): Promise<void> {
    await this.page.locator('.chakra-radio__label:has-text("Температура")').click();
    // Инициируем обновление контроллера формы для вызова re-render
    await this.pFreshInput.fill('130 ');
    await this.pFreshInput.fill('130');
  }

  async selectEnthalpyMode(): Promise<void> {
    await this.page.locator('.chakra-radio__label:has-text("Энтальпия")').click();
    // Инициируем обновление контроллера формы для вызова re-render
    await this.pFreshInput.fill('130 ');
    await this.pFreshInput.fill('130');
  }

  async setPFresh(value: string, unit?: string): Promise<void> {
    await this.pFreshInput.fill(value);
    if (unit) {
      await this.pFreshUnitSelect.selectOption(unit);
    }
  }

  async setThValue(value: string, unit?: string): Promise<void> {
    await this.thInput.fill(value);
    if (unit) {
      await this.thUnitSelect.selectOption(unit);
    }
  }

  async setIntermediatePressure(index: number, value: string): Promise<void> {
    const input = this.intermediateChamberInputs.nth(index);
    await input.fill(value);
  }

  async clickCalculate(): Promise<void> {
    await this.calculateButton.click();
  }

  async clickChangeValves(): Promise<void> {
    await this.changeValvesButton.click();
    await this.waitForPageLoaded();
  }

  async expectValidationErrorMessage(expectedText: string | RegExp): Promise<void> {
    await expect(this.errorMessages.filter({ hasText: expectedText }).first()).toBeVisible();
  }
}