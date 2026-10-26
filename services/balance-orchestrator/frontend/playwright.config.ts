import { defineConfig, devices } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import os from 'os';

/**
 * Автоматический поиск любого уже установленного Chromium на диске:
 * 1. Системный Chromium в Linux (/usr/bin/...)
 * 2. Любая уже скачанная версия в кэше ~/.cache/ms-playwright/
 */
function findExistingChromium(): string | undefined {
  if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH && fs.existsSync(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH)) {
    return process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
  }

  const systemPaths = [
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
  ];
  for (const p of systemPaths) {
    if (fs.existsSync(p)) return p;
  }

  const cacheDir = path.join(os.homedir(), '.cache', 'ms-playwright');
  if (fs.existsSync(cacheDir)) {
    const entries = fs.readdirSync(cacheDir);
    for (const entry of entries) {
      if (entry.startsWith('chromium-')) {
        const candidate = path.join(cacheDir, entry, 'chrome-linux', 'chrome');
        if (fs.existsSync(candidate)) return candidate;
      }
    }
  }

  return undefined;
}

const customExecutablePath = findExistingChromium();

export default defineConfig({
  testDir: './tests',
  timeout: 30 * 1000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off', // <-- Отключаем видео, чтобы не требовался ffmpeg
    viewport: { width: 1280, height: 720 },
  },

  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        ...(customExecutablePath ? { launchOptions: { executablePath: customExecutablePath } } : {}),
      },
    },
  ],

  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 3000',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 60 * 1000,
  },
});