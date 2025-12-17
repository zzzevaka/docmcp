import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',

  // Global setup and teardown
  globalSetup: './e2e/global-setup.js',
  globalTeardown: './e2e/global-teardown.js',

  // Test execution settings
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 0 : 0,
  workers: process.env.CI ? 1 : undefined,

  // Timeout settings
  timeout: 30 * 1000,
  expect: {
    timeout: 5000,
  },

  // Reporter configuration
  reporter: [
    ['html'],
    ['list'],
    ...(process.env.CI ? [['github']] : []),
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://frontend:5173',

    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    // Browser context options
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,

    // API testing
    extraHTTPHeaders: {
      'Accept': 'application/json',
    },
  },

  projects: [
    // Setup project for authentication
    {
      name: 'setup',
      testMatch: /.*\.setup\.js/,
    },

    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
      },
      dependencies: ['setup'],
    },
  ],
});
