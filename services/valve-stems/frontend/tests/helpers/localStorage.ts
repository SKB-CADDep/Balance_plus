import { Page } from '@playwright/test';

export interface HistoryEntry {
  id: string;
  stockName: string;
  stockId: number;
  turbineName: string;
  turbineId: number;
  timestamp: number;
}

export const LOCAL_STORAGE_HISTORY_KEY = 'wsaCalculatorHistory';

export async function getHistoryFromLocalStorage(page: Page): Promise<HistoryEntry[]> {
  return page.evaluate((key) => {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : [];
  }, LOCAL_STORAGE_HISTORY_KEY);
}

export async function setHistoryInLocalStorage(page: Page, entries: HistoryEntry[]): Promise<void> {
  await page.evaluate(
    ({ key, data }) => {
      localStorage.setItem(key, JSON.stringify(data));
      window.dispatchEvent(new Event('wsaHistoryUpdated'));
    },
    { key: LOCAL_STORAGE_HISTORY_KEY, data: entries }
  );
}

export async function clearHistoryInLocalStorage(page: Page): Promise<void> {
  await page.evaluate((key) => {
    localStorage.removeItem(key);
    window.dispatchEvent(new Event('wsaHistoryUpdated'));
  }, LOCAL_STORAGE_HISTORY_KEY);
}

export function generateMockHistoryEntries(count: number): HistoryEntry[] {
  return Array.from({ length: count }, (_, i) => ({
    id: String(1000 + i),
    stockName: `РК-${i + 1}(1шт)`,
    stockId: 101,
    turbineName: `Турбина Т-${100 + i}`,
    turbineId: 1,
    timestamp: Date.now() - i * 60000,
  }));
}