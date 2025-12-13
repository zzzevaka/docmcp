import { test, expect } from '@playwright/test';
import { generateUniqueEmail, getTestPassword, handleCookieNotice } from './helpers.js';

test.describe('Registration', () => {
  test('successful registration', async ({ page }) => {
    const email = generateUniqueEmail();
    const password = getTestPassword();

    // Navigate to registration page
    await page.goto('/register');

    // Handle cookie notice if it appears
    await handleCookieNotice(page);

    // Fill in registration form
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByLabel('Confirm Password', { exact: true }).fill(password);

    // Click register button
    await page.locator('form').getByRole('button', { name: 'Register' }).click();

    // Wait for redirect to projects page (successful registration should log in and redirect)
    await page.waitForURL('/projects');

    // Verify we are logged in by checking for the user avatar button
    await expect(page.locator('button').filter({ has: page.locator('div.rounded-full.bg-primary') })).toBeVisible();
  });
});
