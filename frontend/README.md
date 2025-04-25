# E-Commerce Recommender Frontend

A beautiful and modern React TypeScript frontend for the E-Commerce Recommender System.

## Features

- User authentication (login/signup)
- Product browsing and search
- Personalized recommendations
- Product detail pages
- User interactions (view, add to cart, purchase)
- Responsive design
- Modern Material-UI components

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Backend API running on http://localhost:5000

## Setup

1. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

2. Start the development server:
   ```bash
   npm start
   # or
   yarn start
   ```

3. Open your browser and navigate to http://localhost:3000

## Project Structure

```
src/
  ├── components/     # Reusable UI components
  ├── contexts/       # React contexts (auth, theme, etc.)
  ├── pages/          # Page components
  ├── App.tsx         # Main application component
  └── index.tsx       # Application entry point
```

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

## API Integration

The frontend integrates with the following backend endpoints:

- Authentication:
  - POST /api/signup
  - POST /api/login

- Products:
  - GET /api/products
  - GET /api/products/:id

- Interactions:
  - POST /api/interactions

- Recommendations:
  - GET /api/recommendations/:user_id

## Technologies Used

- React
- TypeScript
- Material-UI
- React Router
- Axios
- Emotion (for styled components)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 