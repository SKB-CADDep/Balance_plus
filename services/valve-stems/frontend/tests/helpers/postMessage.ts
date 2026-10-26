import { Page } from '@playwright/test';

export interface InterceptedPostMessage {
  type: string;
  payload?: {
    input?: any;
    output?: any;
    stockId?: string;
  };
  [key: string]: any;
}

/**
 * Инициализирует перехват сообщений window.parent.postMessage и window message events
 */
export async function setupPostMessageListener(page: Page): Promise<void> {
  await page.addInitScript(() => {
    const win = window as any;
    win.__capturedMessages = [];

    // Слушаем входящие события
    window.addEventListener('message', (event) => {
      if (event.data && typeof event.data === 'object' && event.data.type) {
        win.__capturedMessages.push(event.data);
      }
    });

    // Перехватываем вызовы window.parent.postMessage
    try {
      const origPostMessage = win.parent?.postMessage;
      if (origPostMessage) {
        win.parent.postMessage = function (message: any, targetOrigin: string, ...args: any[]) {
          if (message && typeof message === 'object') {
            win.__capturedMessages.push(message);
          }
          try {
            return origPostMessage.call(win.parent, message, targetOrigin, ...args);
          } catch {
            // Игнорируем ошибки вызова в тестовой среде
          }
        };
      }
    } catch {
      // Игнорируем ошибки доступа
    }
  });
}

/**
 * Возвращает список всех пойманных postMessage сообщений
 */
export async function getCapturedPostMessages(page: Page): Promise<InterceptedPostMessage[]> {
  return page.evaluate(() => (window as any).__capturedMessages || []);
}

/**
 * Ожидает появления postMessage определённого типа
 */
export async function waitForPostMessage(
  page: Page,
  messageType: string,
  timeout = 5000
): Promise<InterceptedPostMessage> {
  const handle = await page.waitForFunction(
    (type) => {
      const msgs = (window as any).__capturedMessages || [];
      return msgs.find((m: any) => m.type === type);
    },
    messageType,
    { timeout }
  );
  return (await handle.jsonValue()) as InterceptedPostMessage;
}