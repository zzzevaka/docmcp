FROM mcr.microsoft.com/playwright:v1.57.0-noble

WORKDIR /app

RUN npm install -g @playwright/test@latest && npx playwright install --with-deps

COPY . .

CMD ["npx", "playwright", "test"]
