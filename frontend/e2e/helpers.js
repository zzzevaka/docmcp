/**
 * Generate a unique username using timestamp and random number
 * @returns {string} Unique email address
 */
export function generateUniqueEmail() {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 10000);
  return `test_${timestamp}_${random}@example.com`;
}

/**
 * Get test password
 * @returns {string} Test password
 */
export function getTestPassword() {
  return 'testpassword123';
}

/**
 * Handle cookie notice if it appears
 * @param {import('@playwright/test').Page} page - Playwright page object
 */
export async function handleCookieNotice(page) {
  const cookieButton = page.getByRole('button', { name: 'I Understand' });
  try {
    await cookieButton.waitFor({ timeout: 2000 });
    await cookieButton.click();
  } catch (error) {
    // Cookie notice might not appear, that's ok
  }
}
