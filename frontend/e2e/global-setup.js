import { chromium, request } from '@playwright/test';
import { generateUniqueEmail, getTestPassword } from './helpers.js';
import fs from 'fs';

async function globalSetup() {
  console.log('Running global setup...');

  const baseURL = process.env.BASE_URL || 'http://localhost:5173';
  console.log('Using baseURL:', baseURL);

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    const response = await page.goto(`${baseURL}/health`);
    if (!response?.ok()) {
      throw "Backend health check failed";
    }

     const apiContext = await request.newContext({
       baseURL,
     });

     const email = generateUniqueEmail();
     const password = getTestPassword();

     await apiContext.post('/api/v1/auth/register', {
       data: {
         email,
         password
       }
     });

     // Save credentials for auth.setup.js to use
     const credentials = { email, password };
     fs.writeFileSync('e2e/.auth/credentials.json', JSON.stringify(credentials, null, 2));

  } catch (error) {
    console.error('Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }

  console.log('Global setup completed');
}

export default globalSetup;
