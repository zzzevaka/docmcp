# DocuMur Frontend

Frontend application for DocuMur.

## Tech Stack

- React 18
- Vite
- React Router
- Tailwind CSS
- Shadcn/ui components

## Development

The frontend is designed to run in Docker. See the main project README for setup instructions.

## Project Structure

```
frontend/
├── src/
│   ├── components/        # Reusable UI components
│   ├── pages/            # Page components
│   ├── lib/              # Utility functions
│   ├── App.jsx           # Main application component
│   ├── main.jsx          # Application entry point
│   └── index.css         # Global styles
├── index.html            # HTML template
├── vite.config.js        # Vite configuration
├── tailwind.config.js    # Tailwind configuration
├── package.json          # Dependencies
└── README.md
```

## Running Tests

```bash
npm test
```
