# TaskMaster Web Frontend

A modern, responsive web application for task management built with Next.js, TypeScript, and Tailwind CSS.

## 🚀 Features

### Current Implementation

- ✅ **Authentication System**: Complete JWT-based authentication with login/register
- ✅ **Protected Routes**: Automatic redirection for unauthenticated users
- ✅ **Dark Mode**: Built-in theme support with system preference detection
- ✅ **Responsive Design**: Mobile-first approach with responsive layouts
- ✅ **Modern UI**: Clean interface using shadcn/ui components
- ✅ **Type Safety**: Full TypeScript support with strict typing
- ✅ **Testing**: Unit tests for authentication components and services

### Planned Features

- 📋 Task Management (CRUD operations)
- 👥 Project Collaboration
- 📊 Analytics Dashboard
- 🔔 Real-time Notifications
- 📅 Calendar Integration
- 🔍 Advanced Search
- 📱 PWA Support

## 🛠️ Tech Stack

- **Framework**: Next.js 15.4+ with App Router
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS v4 (CSS-first approach)
- **UI Components**: shadcn/ui + Radix UI
- **Icons**: Lucide React
- **Authentication**: JWT tokens with localStorage
- **HTTP Client**: Native fetch API
- **Testing**: Jest + React Testing Library

## 📁 Project Structure

```
apps/web/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Authentication pages group
│   │   ├── login/         # Login page
│   │   └── register/      # Registration page
│   ├── (dashboard)/       # Dashboard pages group
│   │   ├── dashboard/     # Main dashboard
│   │   ├── tasks/         # Task management
│   │   ├── projects/      # Project management
│   │   └── ...           # Other dashboard pages
│   ├── layout.tsx         # Root layout with providers
│   └── page.tsx           # Landing page
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── auth/             # Authentication components
│   │   └── protected-route.tsx
│   └── layouts/          # Layout components
│       ├── dashboard-layout.tsx
│       └── header.tsx
├── contexts/             # React contexts
│   └── auth-context.tsx  # Authentication context
├── lib/                  # Utilities and services
│   ├── auth.ts          # Authentication service
│   └── utils.ts         # Utility functions
├── public/              # Static assets
├── styles/              # Global styles
├── tests/               # Test files
│   ├── components/      # Component tests
│   ├── contexts/        # Context tests
│   └── lib/            # Service tests
└── types/              # TypeScript type definitions
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- pnpm package manager
- Backend API running on http://localhost:8000

### Development

From the monorepo root:

```bash
# Install dependencies
pnpm install

# Start the frontend development server
pnpm dev:web

# Or start both frontend and backend
pnpm dev
```

The application will be available at http://localhost:3000

### Testing

```bash
# Run tests from monorepo root
pnpm test:web

# Or from the web directory
cd apps/web
npm test

# Run tests in watch mode
npm test -- --watch

# Generate coverage report
npm test -- --coverage
```

## 🔐 Authentication

The app uses JWT-based authentication with the following flow:

1. User logs in with credentials
2. Backend returns JWT token
3. Token is stored in localStorage
4. Token is included in all API requests
5. Protected routes check for valid token
6. Automatic redirect to login if token is invalid/expired

### Auth Service (`lib/auth.ts`)

- `login()`: Authenticate user
- `register()`: Create new account
- `logout()`: Clear session
- `getCurrentUser()`: Fetch user profile
- `isAuthenticated()`: Check auth status

### Auth Context (`contexts/auth-context.tsx`)

Provides authentication state and methods to all components:

- `user`: Current user object
- `isAuthenticated`: Boolean auth status
- `isLoading`: Loading state
- `login()`, `register()`, `logout()`: Auth methods

### Protected Routes

All dashboard pages are automatically protected using the `ProtectedRoute` component.

## 🎨 UI Components

The app uses [shadcn/ui](https://ui.shadcn.com/) for consistent, accessible components:

- **Button**: Various styles and sizes
- **Card**: Content containers
- **Input**: Form inputs with validation
- **Label**: Form labels
- **Alert**: User notifications
- **Select**: Dropdown selections
- **Textarea**: Multi-line inputs
- **ScrollArea**: Scrollable containers
- **Separator**: Visual dividers
- **Sheet**: Side panels
- **Tabs**: Tabbed interfaces

## 🌙 Dark Mode

Dark mode is built-in with automatic system preference detection:

```tsx
// Toggle theme programmatically
import { useTheme } from 'next-themes';

const { theme, setTheme } = useTheme();
setTheme('dark'); // 'light', 'dark', or 'system'
```

## 📱 Responsive Design

The app uses a mobile-first approach with responsive breakpoints:

- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

## 🧪 Testing

The app includes comprehensive unit tests for:

- Authentication service
- Auth context provider
- Protected route component

Test utilities are provided in `tests/setup.ts` for mocking common dependencies.

## 📝 Environment Variables

Create a `.env.local` file in the web directory:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Feature Flags (optional)
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_PWA=false
```

## 🚀 Deployment

The frontend can be deployed to any platform that supports Next.js:

### Vercel (Recommended)

```bash
# From monorepo root
vercel --cwd apps/web
```

### Docker

```bash
# Build the image
docker build -f apps/web/Dockerfile -t taskmaster-web .

# Run the container
docker run -p 3000:3000 taskmaster-web
```

## 🤝 Contributing

1. Follow the monorepo's commit conventions
2. Write tests for new features
3. Ensure all tests pass before submitting PR
4. Follow the existing code style
5. Update documentation as needed

## 📄 License

This project is part of the Task Management System monorepo and follows the same license.
