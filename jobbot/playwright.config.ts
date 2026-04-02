# Playwright configuration for JobBot E2E tests

import { defineConfig, devices } from '@playwright/test';

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './api/tests/e2e',
  
  /* Run tests in files in parallel */
  fullyParallel: true,
  
  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  
  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 1 : undefined,
  
  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ['junit', { outputFile: 'playwright-results.xml' }]
  ],
  
  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    
    /* API URL for backend requests */
    apiBaseURL: process.env.API_URL || 'http://localhost:8000',
    
    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',
    
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Record video on failure */
    video: 'on-first-retry',
    
    /* Viewport size */
    viewport: { width: 1280, height: 720 },
    
    /* Ignore HTTPS errors during testing */
    ignoreHTTPSErrors: true,
  },
  
  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    
    /* Test against mobile viewports */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
    
    /* Test against branded browsers */
    {
      name: 'Microsoft Edge',
      use: { ...devices['Desktop Edge'], channel: 'msedge' },
    },
    
    {
      name: 'Google Chrome',
      use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    },
  ],
  
  /* Run local dev server before starting the tests */
  webServer: [
    {
      command: 'cd /mnt/c/Users/nacho/Downloads/jobobt && python -m jobbot.api.main',
      url: 'http://localhost:8000/health',
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
    {
      command: 'cd /mnt/c/Users/nacho/Downloads/jobobt/frontend && npm run dev',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
  ],
  
  /* Timeout for each test */
  timeout: 60000,
  
  /* Timeout for expect assertions */
  expect: {
    timeout: 10000,
  },
  
  /* Global setup and teardown */
  globalSetup: require.resolve('./api/tests/e2e/global-setup.ts'),
  globalTeardown: require.resolve('./api/tests/e2e/global-teardown.ts'),
});
