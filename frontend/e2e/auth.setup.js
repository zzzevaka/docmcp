import { test as setup, expect } from '@playwright/test';
import fs from 'fs';
import { handleCookieNotice } from './helpers.js';

const authFile = 'e2e/.auth/user.json';
const credentialsFile = 'e2e/.auth/credentials.json';

setup('authenticate', async ({ page }) => {
  // Read credentials from file
  const credentials = JSON.parse(fs.readFileSync(credentialsFile, 'utf8'));

  // Navigate to login page
  await page.goto('/login');

  // Handle cookie notice if it appears
  await handleCookieNotice(page);

  // Fill in login credentials
  await page.getByLabel('Email', { exact: true }).fill(credentials.email);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);

  // Click login button
  await page.locator('form').getByRole('button', { name: 'Login' }).click();

  // Wait for redirect to projects page (/ redirects to /projects)
  await page.waitForURL('/projects');

  // Verify we are logged in by checking for the user avatar button
  await expect(page.locator('button').filter({ has: page.locator('div.rounded-full.bg-primary') })).toBeVisible();

  // Save auth state
  await page.context().storageState({ path: authFile });
});
