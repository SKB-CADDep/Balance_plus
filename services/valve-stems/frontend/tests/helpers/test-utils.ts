import { Page, expect } from '@playwright/test';

export async function assertNoConsoleErrors(page: Page): Promise<() => void> {
  const errors: string[] = [];
  
  const listener = (msg: any) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  };

  page.on('console', listener);

  return () => {
    expect(errors, `Обнаружены console errors: ${errors.join('\n')}`).toEqual([]);
  };
}