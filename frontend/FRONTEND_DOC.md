# Hyper Events Frontend Documentation

React-based frontend for the Hyper Events tech event registration and ticketing platform. This frontend consumes the serverless AWS backend API and is designed for static hosting on AWS S3.

## Platform Overview

**Platform Name:** Hyper Events
**Purpose:** Ghana's premier tech event registration and ticketing platform
**Tech Stack:** React 18 + TypeScript + Vite + TailwindCSS
**Design System:** Modern typography with Plus Jakarta Sans and Space Grotesk fonts

## Repository Structure

```
.
├── frontend/
│   ├── tech-event/
│   │   ├── src/
│   │   │   ├── components/       # Reusable UI components
│   │   │   │   ├── layout/      # Navbar, Footer
│   │   │   │   ├── ui/          # Button, Card, Badge, Input
│   │   │   │   └── dialog/      # Modal dialogs
│   │   │   ├── pages/           # Page components
│   │   │   │   ├── HomePage.tsx
│   │   │   │   ├── EventsPage.tsx
│   │   │   │   ├── EventDetailsPage.tsx
│   │   │   │   ├── RegistrationPage.tsx
│   │   │   │   ├── MyRegistrationsPage.tsx
│   │   │   │   └── ConfirmationPage.tsx
│   │   │   ├── services/        # API client and integration layer
│   │   │   │   ├── backend-api.service.ts
│   │   │   │   ├── events.service.ts
│   │   │   │   └── registration.service.ts
│   │   │   ├── hooks/           # Custom React hooks
│   │   │   │   ├── useEvents.ts
│   │   │   │   ├── useRegistrations.ts
│   │   │   │   └── useStore.ts
│   │   │   ├── utils/           # Helper functions
│   │   │   │   ├── adapters.ts
│   │   │   │   └── formatters.ts
│   │   │   ├── types/           # TypeScript type definitions
│   │   │   │   └── index.ts
│   │   │   ├── data/            # Mock data
│   │   │   │   └── mockEvents.ts
│   │   │   ├── constants/       # App constants
│   │   │   │   └── index.ts
│   │   │   ├── index.css        # Global styles
│   │   │   └── main.tsx         # Application entry point
│   │   ├── public/              # Static assets (logos, favicon)
│   │   ├── package.json         # Dependencies and scripts
│   │   ├── vite.config.ts       # Vite configuration
│   │   ├── tsconfig.json        # TypeScript configuration
│   │   ├── tailwind.config.js   # TailwindCSS configuration
│   │   ├── .env.example         # Environment variables template
│   │   ├── INTEGRATION_SETUP.md # Backend API integration guide
│   │   └── S3_DEPLOYMENT.md     # S3 deployment guide
├── backend/                     # Serverless API backend
├── terraform/                   # Infrastructure as code
│   ├── frontend/                # S3 bucket Terraform config
│   └── backend/                 # Backend infrastructure
└── README.md
```

## Architecture

```
React App → API Client (Axios) → API Gateway → Lambda → DynamoDB
```

**Design choices:**
- **React 18** for the UI framework - component-based, declarative, excellent ecosystem
- **TypeScript** for type safety and better developer experience
- **Vite** for fast development and optimized production builds
- **TailwindCSS** for utility-first styling and consistent design system
- **TanStack Query (React Query)** for data fetching, caching, and synchronization
- **Zustand** for lightweight state management
- **React Hook Form + Zod** for form validation
- **Axios** for HTTP client with interceptors and error handling
- **React Router v6** for client-side routing
- **Responsive Design** - Mobile-first approach using TailwindCSS breakpoints
- **Environment Variables** - API base URL and feature flags configured via `.env`

## Design System

### Color Palette
- **Primary:** `#0F62FE` (IBM Blue)
- **Primary Hover:** `#0353E9`
- **Background:** `#FAFBFC` (Light gray)
- **Background Secondary:** `#F5F7FA`
- **Surface White:** `#FFFFFF`
- **Text Primary:** `#0F172A` (Slate 900)
- **Text Secondary:** `#475569` (Slate 600)
- **Text Tertiary:** `#94A3B8` (Slate 400)
- **Border Color:** `#E2E8F0` (Slate 200)
- **Success:** `#10B981` (Emerald 500)
- **Warning:** `#F59E0B` (Amber 500)
- **Error:** `#EF4444` (Red 500)

### Typography
- **Headings:** Space Grotesk (500-700 weights)
- **Body Text:** Plus Jakarta Sans (400-600 weights)
- **Line Height:** 1.6
- **Letter Spacing:** -0.02em for headings, -0.01em for buttons

### Components
- **Buttons:** Rounded corners (8px), subtle shadows, modern hover states
- **Cards:** Rounded corners (12px), modern elevation, subtle borders
- **Inputs:** Clean borders, focus states with brand color
- **Navigation:** Pill-shaped active states, smooth transitions

### Responsive Breakpoints
- **Mobile:** < 768px
- **Tablet:** 768px - 1024px
- **Desktop:** >= 1024px

## API Integration

See [backend/API.md](../backend/API.md) for full request/response contracts.

| Method | Path | Description |
|---|---|---|
| `GET` | `/events` | List all events with computed availability status |
| `POST` | `/register` | Register for an event |
| `GET` | `/registrations/{email}` | View a participant's registrations |
| `DELETE` | `/registration/{id}` | Cancel a registration |

### Configuration

Set the backend API URL and feature flags as environment variables in `.env`:

```bash
# Backend API URL
VITE_API_BASE_URL=https://your-api-gateway-url.amazonaws.com/dev

# Use mock data instead of real API (true/false)
VITE_USE_MOCK_DATA=false
```

### Data Adapters

The frontend uses adapter functions to map between backend and frontend data structures:

- `adaptBackendEvent()` - Converts backend event response to frontend event type
- `adaptBackendRegistration()` - Converts backend registration response to frontend registration type
- `adaptRegistrationRequest()` - Converts frontend registration request to backend format

See [INTEGRATION_SETUP.md](./tech-event/INTEGRATION_SETUP.md) for detailed integration instructions.

## Getting Started

### Prerequisites
- Node.js >= 18
- npm or yarn
- Backend API deployed and accessible (for production use)

### 1. Install dependencies
```bash
cd frontend/tech-event
npm install
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and set VITE_API_BASE_URL and VITE_USE_MOCK_DATA
```

### 3. Run development server
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### 4. Build for production
```bash
npm run build
```

Output will be in `dist/` directory.

## Deployment

The frontend is designed for static hosting on AWS S3. For detailed deployment instructions, see [S3_DEPLOYMENT.md](./tech-event/S3_DEPLOYMENT.md).

### Quick Deploy

```bash
# Make deployment script executable
chmod +x deploy-s3.sh

# Deploy to S3
./deploy-s3.sh <bucket-name> <region> <api-url> <use-mock-data>
```

### Example
```bash
./deploy-s3.sh hypervisor-event-ticketing-bucket us-east-1 https://3yf8dopk35.execute-api.us-east-1.amazonaws.com/dev false
```

### Important Notes

- Logos must be in the `public/` folder for proper Vite bundling
- When deploying to production, ensure the backend's `frontend_origin` Terraform variable is updated to your actual frontend domain to lock down CORS
- The deployment script automatically creates a `.env.production` file during build

## Features

### Event Browsing
- View all available events with filtering by category
- Event cards show title, date, location, capacity, and status
- Responsive grid layout for different screen sizes

### Event Registration
- Registration form with validation
- Real-time availability checking
- Email-based registration confirmation
- Ticket ID generation

### My Registrations
- View all registrations by email (backend API requirement)
- Filter and search registrations
- Cancel registrations with confirmation
- Download ticket as image

### Responsive Design
- Mobile-first approach
- Responsive logos (desktop/mobile variants)
- Touch-friendly interface
- Optimized for various screen sizes

### Backend Integration
- Real AWS backend API integration
- Mock data fallback for development
- Error handling and loading states
- Data caching with React Query

## Assets

### Logos
- `hyperlogo-desktop.png` - Used for desktop screens (>=768px)
- `hyperlogo-mobile.png` - Used for mobile screens and favicon

Logos are placed in the `public/` folder and served from the root path (`/hyperlogo-desktop.png`, `/hyperlogo-mobile.png`).

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API endpoint | - |
| `VITE_USE_MOCK_DATA` | Use mock data instead of API | `true` |

## Notes

- No authentication is currently implemented - backend endpoints are public
- Email lookups are case-insensitive (server-side normalization)
- Rate limit: 10 requests/sec sustained, burst of 20
- All dates are in ISO 8601 format
- Registration IDs are UUIDs
- The app uses client-side routing with React Router
- S3 static hosting returns `index.html` for all routes to enable SPA navigation

## Troubleshooting

### Logos not loading
- Ensure logos are in the `public/` folder
- Check file paths in components use `/` prefix
- Verify logos are not in `src/assets/` (use `public/` instead)

### API errors
- Verify `VITE_API_BASE_URL` is correct in `.env`
- Check CORS configuration on backend
- Ensure backend is deployed and accessible
- Check browser console for specific errors

### Build errors
- Clear node_modules: `rm -rf node_modules package-lock.json`
- Reinstall: `npm install`
- Check TypeScript errors in IDE
- Verify all imports are correct

### Deployment issues
- See [S3_DEPLOYMENT.md](./tech-event/S3_DEPLOYMENT.md) for detailed troubleshooting
- Check AWS credentials are configured
- Verify S3 bucket exists and has proper permissions
- Ensure bucket policy allows public read access
