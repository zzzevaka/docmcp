import { test, expect } from '@playwright/test';
import { generateUniqueEmail, getTestPassword, handleCookieNotice } from './helpers.js';

test.describe('Login', () => {
  test('successful login', async ({ page, request }) => {
    const email = generateUniqueEmail();
    const password = getTestPassword();

    // First, create a user via API
    await request.post('/api/v1/auth/register', {
      data: { email, password }
    });

    // Navigate to login page
    await page.goto('/login');

    // Handle cookie notice if it appears
    await handleCookieNotice(page);

    // Fill in login credentials
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill(password);

    // Click login button
    await page.locator('form').getByRole('button', { name: 'Login' }).click();

    // Wait for redirect to projects page
    await page.waitForURL('/projects');

    // Verify we are logged in by checking for the user avatar button
    await expect(page.locator('button').filter({ has: page.locator('div.rounded-full.bg-primary') })).toBeVisible();
  });

  test('login fails with correct error for wrong credentials', async ({ page, request }) => {
    const email = generateUniqueEmail();
    const password = getTestPassword();

    // First, create a user via API
    await request.post('/api/v1/auth/register', {
      data: { email, password }
    });

    // Navigate to login page
    await page.goto('/login');

    // Handle cookie notice if it appears
    await handleCookieNotice(page);

    // Try to login with wrong password
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill('wrongpassword123');

    // Click login button
    await page.locator('form').getByRole('button', { name: 'Login' }).click();

    // Verify error message is displayed
    await expect(page.getByText(/invalid.*email/i)).toBeVisible();

    // Verify we are still on login page
    await expect(page).toHaveURL('/login');
  });
});
