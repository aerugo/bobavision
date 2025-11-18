# Admin UI Development Guide

## Purpose

This guide provides detailed instructions for developing the **React + TypeScript admin interface** for the Kids Single-Button Media Station. Follow this guide when working on frontend-related tasks.

**Technology Stack**: React 18+, TypeScript, Vite, Tailwind CSS, Vitest, React Testing Library

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Testing Strategy](#testing-strategy)
5. [Component Architecture](#component-architecture)
6. [Phase-Specific Guides](#phase-specific-guides)
7. [Common Tasks](#common-tasks)
8. [Styling Guidelines](#styling-guidelines)

---

## Quick Start

### Initial Setup (Phase 0)

```bash
cd admin

# Install Bun (if not already installed)
curl -fsSL https://bun.sh/install | bash

# Install dependencies
bun install

# Install additional packages (if needed)
bun add -D tailwindcss postcss autoprefixer
bun add -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event
bun add -D @vitest/ui jsdom

# Initialize Tailwind (if not already configured)
bunx tailwindcss init -p
```

### Running Development Server

```bash
# Start dev server
bun run dev

# Open browser to http://localhost:5173
```

### Running Tests

```bash
# Run all tests
bun test

# Run tests in watch mode
bun run test:watch

# Run tests with coverage
bun run test:coverage

# Run tests with UI
bun run test:ui
```

### Building for Production

```bash
# Build for production
bun run build

# Preview production build
bun run preview
```

---

## Project Structure

```
admin/
├── CLAUDE.md              ← You are here
├── package.json           ← Dependencies
├── tsconfig.json          ← TypeScript config
├── vite.config.ts         ← Vite config
├── tailwind.config.js     ← Tailwind config
├── postcss.config.js      ← PostCSS config
├── index.html             ← Entry HTML
│
├── src/
│   ├── main.tsx           ← App entry point
│   ├── App.tsx            ← Root component
│   ├── index.css          ← Global styles
│   │
│   ├── pages/             ← Page components
│   │   ├── Dashboard.tsx      ← Dashboard page
│   │   ├── Library.tsx        ← Video library page
│   │   ├── Queue.tsx          ← Queue management page
│   │   └── Settings.tsx       ← Settings page
│   │
│   ├── components/        ← Reusable components
│   │   ├── layout/
│   │   │   ├── Layout.tsx     ← Main layout wrapper
│   │   │   ├── Header.tsx     ← Header bar
│   │   │   └── Navigation.tsx ← Nav menu
│   │   │
│   │   ├── video/
│   │   │   ├── VideoCard.tsx  ← Video display card
│   │   │   ├── VideoList.tsx  ← List of videos
│   │   │   └── VideoFilter.tsx← Filter controls
│   │   │
│   │   ├── queue/
│   │   │   ├── QueueItem.tsx  ← Single queue item
│   │   │   └── QueueList.tsx  ← Draggable queue list
│   │   │
│   │   └── common/
│   │       ├── Button.tsx     ← Button component
│   │       ├── Card.tsx       ← Card component
│   │       ├── Input.tsx      ← Input component
│   │       ├── Loading.tsx    ← Loading spinner
│   │       └── ErrorMessage.tsx← Error display
│   │
│   ├── services/          ← API and business logic
│   │   ├── api.ts         ← API client
│   │   └── types.ts       ← TypeScript types
│   │
│   ├── hooks/             ← Custom React hooks
│   │   ├── useVideos.ts   ← Videos data hook
│   │   ├── useClients.ts  ← Clients data hook
│   │   └── useQueue.ts    ← Queue data hook
│   │
│   └── utils/             ← Helper functions
│       ├── formatTime.ts  ← Time formatting
│       └── api.ts         ← API utilities
│
└── tests/
    ├── setup.ts           ← Test setup
    ├── components/        ← Component tests
    ├── pages/             ← Page tests
    └── services/          ← Service tests
```

---

## Development Workflow

### TDD Cycle for Frontend Features

#### Example: Implementing VideoCard Component

**Step 1: 🔴 RED - Write Failing Test**

```typescript
// tests/components/VideoCard.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { VideoCard } from '../../src/components/video/VideoCard'

describe('VideoCard', () => {
  it('displays video title and duration', () => {
    // Arrange
    const video = {
      id: 1,
      title: 'Test Video',
      path: 'test.mp4',
      duration_seconds: 600,
      is_placeholder: false,
      tags: ['cartoon']
    }

    // Act
    render(<VideoCard video={video} />)

    // Assert
    expect(screen.getByText('Test Video')).toBeInTheDocument()
    expect(screen.getByText(/10:00/)).toBeInTheDocument()  // 600s = 10min
  })
})
```

Run: `bun test`
Expected: **FAIL** (component doesn't exist)

Commit: `[PHASE-3] test: add test for VideoCard component`

**Step 2: 🟢 GREEN - Make Test Pass**

```typescript
// src/components/video/VideoCard.tsx
import React from 'react'

interface Video {
  id: number
  title: string
  path: string
  duration_seconds: number
  is_placeholder: boolean
  tags: string[]
}

interface VideoCardProps {
  video: Video
}

export function VideoCard({ video }: VideoCardProps) {
  const minutes = Math.floor(video.duration_seconds / 60)
  const seconds = video.duration_seconds % 60

  return (
    <div>
      <h3>{video.title}</h3>
      <span>{minutes}:{seconds.toString().padStart(2, '0')}</span>
    </div>
  )
}
```

Run: `bun test`
Expected: **PASS**

Commit: `[PHASE-3] feat: implement basic VideoCard component`

**Step 3: ♻️ REFACTOR - Add Styling**

```typescript
// src/components/video/VideoCard.tsx
import React from 'react'

interface Video {
  id: number
  title: string
  path: string
  duration_seconds: number
  is_placeholder: boolean
  tags: string[]
}

interface VideoCardProps {
  video: Video
  onQueue?: (videoId: number) => void
}

export function VideoCard({ video, onQueue }: VideoCardProps) {
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold text-gray-900">{video.title}</h3>
        {video.is_placeholder && (
          <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">
            Placeholder
          </span>
        )}
      </div>

      <div className="flex gap-2 mb-2">
        {video.tags.map(tag => (
          <span key={tag} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
            {tag}
          </span>
        ))}
      </div>

      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-500">{formatDuration(video.duration_seconds)}</span>
        {onQueue && (
          <button
            onClick={() => onQueue(video.id)}
            className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 transition-colors"
          >
            Add to Queue
          </button>
        )}
      </div>
    </div>
  )
}
```

Run: `bun test`
Expected: **STILL PASS**

Commit: `[PHASE-3] refactor: add styling to VideoCard`

---

## Testing Strategy

### Test Setup

```typescript
// tests/setup.ts
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'

// Cleanup after each test
afterEach(() => {
  cleanup()
})
```

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
    coverage: {
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'tests/']
    }
  }
})
```

### Testing Components

```typescript
// tests/components/Button.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../../src/components/common/Button'

describe('Button', () => {
  it('renders button with text', () => {
    render(<Button>Click Me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click Me</Button>)

    fireEvent.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledOnce()
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click Me</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

### Testing API Client

```typescript
// tests/services/api.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ApiClient } from '../../src/services/api'

// Mock fetch
global.fetch = vi.fn()

describe('ApiClient', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('fetches videos from server', async () => {
    // Arrange
    const mockVideos = [
      { id: 1, title: 'Video 1', path: 'video1.mp4' }
    ]

    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockVideos
    })

    const client = new ApiClient('http://localhost:8000')

    // Act
    const videos = await client.getVideos()

    // Assert
    expect(videos).toEqual(mockVideos)
    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/videos')
  })

  it('throws error when fetch fails', async () => {
    // Arrange
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 500
    })

    const client = new ApiClient('http://localhost:8000')

    // Act & Assert
    await expect(client.getVideos()).rejects.toThrow()
  })
})
```

### Testing Custom Hooks

```typescript
// tests/hooks/useVideos.test.ts
import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useVideos } from '../../src/hooks/useVideos'

// Mock API client
vi.mock('../../src/services/api', () => ({
  ApiClient: vi.fn().mockImplementation(() => ({
    getVideos: vi.fn().mockResolvedValue([
      { id: 1, title: 'Video 1' }
    ])
  }))
}))

describe('useVideos', () => {
  it('fetches videos on mount', async () => {
    // Act
    const { result } = renderHook(() => useVideos())

    // Assert - Initially loading
    expect(result.current.loading).toBe(true)

    // Wait for fetch to complete
    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.videos).toHaveLength(1)
    expect(result.current.videos[0].title).toBe('Video 1')
  })
})
```

---

## Component Architecture

### Page Components

Page components represent routes and orchestrate multiple smaller components.

```typescript
// src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react'
import { Layout } from '../components/layout/Layout'
import { ClientCard } from '../components/client/ClientCard'
import { useClients } from '../hooks/useClients'
import { Loading } from '../components/common/Loading'
import { ErrorMessage } from '../components/common/ErrorMessage'

export function Dashboard() {
  const { clients, loading, error, refresh } = useClients()

  if (loading) return <Loading />
  if (error) return <ErrorMessage message={error} />

  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6">Dashboard</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clients.map(client => (
            <ClientCard key={client.client_id} client={client} />
          ))}
        </div>
      </div>
    </Layout>
  )
}
```

### Container Components

Handle data fetching and state management, pass data to presentational components.

```typescript
// src/components/video/VideoList.tsx
import React from 'react'
import { VideoCard } from './VideoCard'
import { Video } from '../../services/types'

interface VideoListProps {
  videos: Video[]
  onQueue: (videoId: number) => void
}

export function VideoList({ videos, onQueue }: VideoListProps) {
  if (videos.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No videos found. Try scanning your library.
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {videos.map(video => (
        <VideoCard key={video.id} video={video} onQueue={onQueue} />
      ))}
    </div>
  )
}
```

### Presentational Components

Pure components that only handle display based on props.

```typescript
// src/components/common/Card.tsx
import React, { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      {children}
    </div>
  )
}
```

---

## Phase-Specific Guides

### Phase 0: Project Setup

**Tasks**:
1. Initialize Vite project with React + TypeScript
2. Install dependencies
3. Configure Tailwind CSS
4. Configure Vitest
5. Create initial structure

**Checklist**:
- [ ] Vite project initialized
- [ ] Dependencies installed (React, Tailwind, Vitest, etc.)
- [ ] Tailwind configured
- [ ] Test framework working
- [ ] Can run `bun run dev` and see app
- [ ] Can run `bun test` and see tests pass

**Initial Setup Commands**:

```bash
# Install Bun (if not already installed)
curl -fsSL https://bun.sh/install | bash

# Install dependencies
bun install

# Install Tailwind (if needed)
bun add -D tailwindcss postcss autoprefixer
bunx tailwindcss init -p

# Install testing libraries (if needed)
bun add -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @vitest/ui
```

**Tailwind Configuration**:

```javascript
// tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Package.json Scripts**:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:coverage": "vitest --coverage",
    "test:ui": "vitest --ui"
  }
}
```

### Phase 3: Queue & Admin UI

**Goal**: Build all admin pages and functionality

**TDD Tasks by Feature**:

#### 1. API Client

```typescript
// tests/services/api.test.ts
describe('ApiClient', () => {
  it('getVideos returns list of videos', async () => { ... })
  it('getClients returns list of clients', async () => { ... })
  it('getQueue returns queue for client', async () => { ... })
  it('addToQueue adds video to client queue', async () => { ... })
})
```

#### 2. Dashboard Page

```typescript
// tests/pages/Dashboard.test.tsx
describe('Dashboard', () => {
  it('displays list of clients', async () => { ... })
  it('shows play count vs limit for each client', async () => { ... })
  it('shows loading state while fetching', () => { ... })
  it('shows error when fetch fails', () => { ... })
})
```

#### 3. Library Page

```typescript
// tests/pages/Library.test.tsx
describe('Library', () => {
  it('displays grid of video cards', async () => { ... })
  it('filters videos by search text', () => { ... })
  it('filters videos by tags', () => { ... })
  it('adds video to queue when button clicked', () => { ... })
})
```

#### 4. Queue Page

```typescript
// tests/pages/Queue.test.tsx
describe('Queue', () => {
  it('displays queue items in order', async () => { ... })
  it('removes item when delete clicked', () => { ... })
  it('clears entire queue when clear clicked', () => { ... })
  it('reorders queue when items dragged', () => { ... })
})
```

#### 5. Settings Page

```typescript
// tests/pages/Settings.test.tsx
describe('Settings', () => {
  it('displays current daily limit', async () => { ... })
  it('updates daily limit when saved', () => { ... })
  it('triggers library rescan when button clicked', () => { ... })
})
```

---

## Common Tasks

### Creating a New Component

1. **Write test first**:
```typescript
// tests/components/MyComponent.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MyComponent } from '../../src/components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" />)
    expect(screen.getByText('Test')).toBeInTheDocument()
  })
})
```

2. **Create component**:
```typescript
// src/components/MyComponent.tsx
import React from 'react'

interface MyComponentProps {
  title: string
}

export function MyComponent({ title }: MyComponentProps) {
  return <div>{title}</div>
}
```

3. **Run test**: `bun test`

### Creating a Custom Hook

```typescript
// src/hooks/useVideos.ts
import { useState, useEffect } from 'react'
import { ApiClient } from '../services/api'
import { Video } from '../services/types'

export function useVideos() {
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchVideos = async () => {
    try {
      setLoading(true)
      const api = new ApiClient(import.meta.env.VITE_API_URL || 'http://localhost:8000')
      const data = await api.getVideos()
      setVideos(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch videos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchVideos()
  }, [])

  return { videos, loading, error, refresh: fetchVideos }
}
```

### Adding Routing

```bash
# Install React Router with Bun
bun add react-router-dom
```

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { Library } from './pages/Library'
import { Queue } from './pages/Queue'
import { Settings } from './pages/Settings'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/library" element={<Library />} />
        <Route path="/queue/:clientId" element={<Queue />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  )
}
```

### Handling Loading States

```typescript
// src/components/common/Loading.tsx
export function Loading() {
  return (
    <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    </div>
  )
}
```

### Handling Errors

```typescript
// src/components/common/ErrorMessage.tsx
interface ErrorMessageProps {
  message: string
  onRetry?: () => void
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <p className="text-red-800">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 text-red-600 hover:text-red-800 underline"
        >
          Try Again
        </button>
      )}
    </div>
  )
}
```

---

## Styling Guidelines

### Tailwind Best Practices

1. **Use semantic class names** for complex repeated styles:

```typescript
// src/index.css
@layer components {
  .btn-primary {
    @apply bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors;
  }

  .card {
    @apply bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow;
  }
}
```

2. **Use spacing consistently**:
- Use Tailwind's spacing scale: `p-4`, `mb-6`, etc.
- Standard gaps: `gap-4` for grids, `space-y-4` for vertical stacks

3. **Responsive design**:
```typescript
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
```

### Color Palette

Use Tailwind's default colors for consistency:
- **Primary**: Blue (`bg-blue-500`, `text-blue-600`)
- **Success**: Green (`bg-green-500`, `text-green-600`)
- **Warning**: Yellow (`bg-yellow-500`, `text-yellow-600`)
- **Error**: Red (`bg-red-500`, `text-red-600`)
- **Neutral**: Gray (`bg-gray-100`, `text-gray-700`)

### Typography

```typescript
<h1 className="text-3xl font-bold mb-6">Page Title</h1>
<h2 className="text-2xl font-semibold mb-4">Section Title</h2>
<h3 className="text-xl font-medium mb-3">Subsection</h3>
<p className="text-base text-gray-700">Body text</p>
<span className="text-sm text-gray-500">Secondary text</span>
```

---

## TypeScript Types

### Core Types

```typescript
// src/services/types.ts

export interface Video {
  id: number
  path: string
  title: string
  tags: string[]
  is_placeholder: boolean
  duration_seconds: number
  created_at: string
}

export interface Client {
  client_id: string
  friendly_name: string
  daily_limit: number
  tag_filters: string[]
  created_at: string
  updated_at: string
}

export interface QueueItem {
  id: number
  client_id: string
  video_id: number
  position: number
  created_at: string
  video: Video
}

export interface PlayLog {
  id: number
  client_id: string
  video_id: number
  played_at: string
  is_placeholder: boolean
  completed: boolean
}

export interface ClientStats {
  client_id: string
  plays_today: number
  daily_limit: number
  recent_plays: PlayLog[]
}

export interface NextVideoResponse {
  url: string
  title: string
  placeholder: boolean
}
```

### API Client

```typescript
// src/services/api.ts
import { Video, Client, QueueItem, ClientStats } from './types'

export class ApiClient {
  constructor(private baseUrl: string) {}

  async getVideos(filters?: { search?: string; tags?: string }): Promise<Video[]> {
    const params = new URLSearchParams(filters as any)
    const response = await fetch(`${this.baseUrl}/api/videos?${params}`)
    if (!response.ok) throw new Error('Failed to fetch videos')
    return response.json()
  }

  async getClients(): Promise<Client[]> {
    const response = await fetch(`${this.baseUrl}/api/clients`)
    if (!response.ok) throw new Error('Failed to fetch clients')
    return response.json()
  }

  async getQueue(clientId: string): Promise<QueueItem[]> {
    const response = await fetch(`${this.baseUrl}/api/queue/${clientId}`)
    if (!response.ok) throw new Error('Failed to fetch queue')
    return response.json()
  }

  async addToQueue(clientId: string, videoIds: number[]): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/queue/${clientId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_ids: videoIds })
    })
    if (!response.ok) throw new Error('Failed to add to queue')
  }

  async clearQueue(clientId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/queue/${clientId}/clear`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to clear queue')
  }

  async updateClientSettings(clientId: string, settings: Partial<Client>): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/clients/${clientId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    })
    if (!response.ok) throw new Error('Failed to update client')
  }

  async scanLibrary(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/videos/scan`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to scan library')
  }

  async getStats(clientId: string): Promise<ClientStats> {
    const response = await fetch(`${this.baseUrl}/api/stats/${clientId}`)
    if (!response.ok) throw new Error('Failed to fetch stats')
    return response.json()
  }
}
```

---

## Best Practices

### Component Organization

1. **Props interface first**
2. **Component function**
3. **Helper functions at bottom**

```typescript
// Good structure
interface MyComponentProps {
  title: string
  onAction: () => void
}

export function MyComponent({ title, onAction }: MyComponentProps) {
  // State
  const [count, setCount] = useState(0)

  // Effects
  useEffect(() => {
    // ...
  }, [])

  // Event handlers
  const handleClick = () => {
    setCount(count + 1)
    onAction()
  }

  // Render
  return (
    <div>
      {/* JSX */}
    </div>
  )
}

// Helper functions
function formatHelper(value: string): string {
  return value.toUpperCase()
}
```

### Error Handling

```typescript
async function fetchData() {
  try {
    const data = await api.getVideos()
    setVideos(data)
  } catch (error) {
    if (error instanceof Error) {
      setError(error.message)
    } else {
      setError('An unexpected error occurred')
    }
  }
}
```

### Performance Optimization

```typescript
import { memo, useCallback, useMemo } from 'react'

// Memoize expensive computations
const sortedVideos = useMemo(() => {
  return videos.sort((a, b) => a.title.localeCompare(b.title))
}, [videos])

// Memoize callbacks
const handleQueue = useCallback((videoId: number) => {
  addToQueue(clientId, [videoId])
}, [clientId])

// Memoize components
export const VideoCard = memo(VideoCardComponent)
```

---

## Troubleshooting

### Build Errors

```bash
# Clear build cache
rm -rf dist node_modules
bun install
bun run build
```

### Type Errors

```typescript
// Use type assertions when necessary
const element = document.getElementById('root') as HTMLElement

// Define proper types for API responses
interface ApiResponse {
  data: Video[]
  error?: string
}
```

### Test Failures

```bash
# Run tests in watch mode to debug
bun run test:watch

# Run single test file
bun test -- VideoCard.test.tsx

# View test UI
bun run test:ui
```

---

## Next Steps

1. **Complete Phase 0 tasks** (see [Grand Plan](../docs/grand_plan.md))
2. **Follow TDD cycle** for all components
3. **Build pages incrementally** starting with Dashboard
4. **Test on mobile browsers** early and often

---

**Ready to build? Open the Grand Plan, pick a task, and start with a test!**
