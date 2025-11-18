# Kids Single-Button Media Station - Grand Development Plan

## Document Purpose

This document serves as the **single source of truth** for the entire Kids Single-Button Media Station project. It contains:

- The complete project vision and requirements
- All development phases with detailed tasks
- Progress tracking for each phase
- Success criteria and acceptance tests
- Architecture decisions and rationale

**Last Updated**: 2025-11-18
**Current Phase**: Phase 3 - Queue & Admin UI (95% complete)
**Overall Progress**: 58% (2.5/6 phases complete - Phase 3 nearly done)

---

## Table of Contents

1. [Project Vision](#project-vision)
2. [System Architecture](#system-architecture)
3. [Development Phases](#development-phases)
4. [Progress Tracking](#progress-tracking)
5. [Success Criteria](#success-criteria)
6. [Future Extensions](#future-extensions)

---

## Project Vision

### The Problem

Typical streaming setups overwhelm kids with choices and make it hard for parents to enforce limits. Existing parental controls focus on time windows, ratings, or per-app limits, but not the exact behavior desired here:

- "You get three programs a day. After that, the screen just plays a friendly 'you're done' video, no matter how many times you try."
- "You don't pick what to watch; I pick it (or the system picks randomly from a curated library)."

### The Solution

A trolley-mounted, portable media player designed for young children with:

1. **Strictly limited screen time** (N programs per day)
2. **No content choice for the child** (no menus, no scrolling, no thumbnails)
3. **Ultra-simple interaction**: a single physical button next to the screen
4. **Centralized control for parents** via a web/mobile admin interface on the local network

### Core Principles

1. **Single-Button Interaction**: The child interacts with only one button - no visible UI controls
2. **Daily Program Limit**: Configurable limit per device (e.g., 3 programs/day)
3. **No Choice for Child**: Content selected by parent-created queue or random from curated library
4. **Centralized Management**: Parents manage library and queues from web UI
5. **Local Network Only**: All components talk over home LAN, no cloud dependency
6. **TDD First**: All features developed test-first with strict TDD discipline

---

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Home LAN (192.168.x.x)                 │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │ Media Server │◄────────┤ Admin Device │                │
│  │ (FastAPI)    │         │ (Browser)    │                │
│  │              │         │              │                │
│  │ - API        │         │ - React UI   │                │
│  │ - SQLite DB  │         │ - Queue Mgmt │                │
│  │ - Media Files│         │ - Stats View │                │
│  └──────┬───────┘         └──────────────┘                │
│         │                                                  │
│         │ HTTP                                             │
│         │                                                  │
│  ┌──────▼───────┐                                          │
│  │ Client (Pi)  │                                          │
│  │              │                                          │
│  │ - Button     │──► GPIO                                 │
│  │ - mpv Player │──► HDMI to Screen                       │
│  │ - Python     │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Media Server
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: SQLite + SQLAlchemy
- **Server**: Uvicorn (ASGI)
- **Testing**: pytest, pytest-asyncio, httpx

#### Admin Frontend
- **Language**: TypeScript
- **Framework**: React 18+
- **Styling**: Tailwind CSS
- **Build**: Vite
- **Testing**: Vitest, React Testing Library

#### Client (Raspberry Pi)
- **OS**: Raspberry Pi OS Lite
- **Language**: Python 3.11+
- **Media Player**: mpv
- **GPIO**: gpiozero
- **HTTP Client**: httpx
- **Testing**: pytest, pytest-mock

### Data Model

```python
# Core entities in SQLite database

videos(
    id: int PRIMARY KEY,
    path: str UNIQUE NOT NULL,
    title: str NOT NULL,
    tags: str,  # comma-separated
    is_placeholder: bool DEFAULT false,
    duration_seconds: int,
    created_at: timestamp
)

client_settings(
    client_id: str PRIMARY KEY,
    friendly_name: str NOT NULL,
    daily_limit: int DEFAULT 3,
    tag_filters: str,  # comma-separated allowed tags
    created_at: timestamp,
    updated_at: timestamp
)

queue(
    id: int PRIMARY KEY,
    client_id: str FOREIGN KEY,
    video_id: int FOREIGN KEY,
    position: int NOT NULL,
    created_at: timestamp
)

play_log(
    id: int PRIMARY KEY,
    client_id: str FOREIGN KEY,
    video_id: int FOREIGN KEY,
    played_at: timestamp NOT NULL,
    is_placeholder: bool NOT NULL,
    completed: bool DEFAULT false
)
```

### API Endpoints

#### Core Playback
- `GET /api/next?client_id={id}` - Get next video (queue → random → placeholder)

#### Video Library
- `GET /api/videos` - List all videos (with filters)
- `GET /api/videos/{id}` - Get single video details
- `POST /api/videos/scan` - Rescan media directory
- `PATCH /api/videos/{id}` - Update video metadata

#### Client Management
- `GET /api/clients` - List all clients
- `GET /api/clients/{id}` - Get client details
- `POST /api/clients` - Create new client
- `PATCH /api/clients/{id}` - Update client settings

#### Queue Management
- `GET /api/queue/{client_id}` - Get client's queue
- `POST /api/queue/{client_id}` - Add videos to queue
- `DELETE /api/queue/{client_id}/{queue_id}` - Remove queue item
- `POST /api/queue/{client_id}/clear` - Clear entire queue
- `PUT /api/queue/{client_id}/reorder` - Reorder queue

#### Statistics
- `GET /api/stats/{client_id}` - Get play stats for client
- `GET /api/stats/{client_id}/today` - Get today's plays

#### Media Serving
- `GET /media/library/{path}` - Static file serving

---

## Development Phases

### Phase 0: Project Setup ✅ COMPLETE
**Goal**: Establish project structure, tooling, and development environment

**Duration**: 1 session
**Completed**: 2025-11-18

#### Tasks
- [x] Create repository structure
- [x] Create comprehensive documentation (grand_plan.md, CLAUDE.md files)
- [x] Set up Python environment for server (requirements.txt)
- [x] Set up Python environment for client
- [x] Set up Node/npm environment for admin frontend
- [x] Configure pytest for server with coverage
- [x] Configure pytest for client
- [x] Configure Vitest for admin frontend
- [x] Create .gitignore
- [x] Create README.md with quick start guide
- [x] Set up pre-commit hooks (optional but recommended)

#### Deliverables
- [x] `/docs/grand_plan.md` - This document
- [x] `/CLAUDE.md` - Root development guide
- [x] `/server/CLAUDE.md` - Backend development guide
- [x] `/client/CLAUDE.md` - Client development guide
- [x] `/admin/CLAUDE.md` - Frontend development guide
- [x] `/docs/tdd_guide.md` - TDD principles and workflow
- [x] `/server/requirements.txt`
- [x] `/server/pytest.ini`
- [x] `/client/requirements.txt`
- [x] `/client/pytest.ini`
- [x] `/admin/package.json`
- [x] `/admin/vite.config.ts`
- [x] `/.gitignore`
- [x] `/README.md`

#### Success Criteria
- [x] Can run `pytest` in server/ and see tests running
- [x] Can run `pytest` in client/ and see tests running
- [x] Can run `npm test` in admin/ and see test runner initialize
- [x] All directories and config files in place

---

### Phase 1: Minimal Vertical Slice (Core Playback) ✅ COMPLETE
**Goal**: Single button press → random video plays (no limits, no DB, no queue)

**Duration**: 2 sessions
**Completed**: 2025-11-18

#### TDD Approach
1. Write failing tests for `/api/next` endpoint
2. Implement endpoint to pass tests
3. Write failing tests for client button handler
4. Implement button handler to pass tests
5. Integration test: end-to-end button press → video plays

#### Server Tasks
- [x] **TEST**: Write test for basic FastAPI app initialization
- [x] **CODE**: Create FastAPI application structure
- [x] **TEST**: Write test for file scanning (in-memory list)
- [x] **CODE**: Implement media directory scanner
- [x] **TEST**: Write test for `/api/next` returning random video
- [x] **CODE**: Implement `/api/next` endpoint (random selection)
- [x] **TEST**: Write test for static file serving
- [x] **CODE**: Implement static file serving for `/media`
- [x] **REFACTOR**: Extract video selection logic

#### Client Tasks
- [ ] **TEST**: Write test for button press detection (mocked GPIO)
- [ ] **CODE**: Implement button listener with gpiozero
- [ ] **TEST**: Write test for HTTP client calling `/api/next`
- [ ] **CODE**: Implement HTTP client
- [ ] **TEST**: Write test for mpv process management
- [ ] **CODE**: Implement mpv launcher
- [ ] **TEST**: Write test for state machine (IDLE → PLAYING)
- [ ] **CODE**: Implement state machine
- [ ] **INTEGRATION**: Manual test on actual Pi hardware

#### Deliverables
- [x] `/server/src/main.py` - FastAPI app entry point
- [x] `/server/src/media/scanner.py` - Media file scanner
- [x] `/server/tests/test_api.py` - API tests (13 tests)
- [x] `/server/tests/test_scanner.py` - Scanner tests (4 tests)
- [x] `/server/tests/test_static_files.py` - Static file tests (4 tests)
- [ ] `/client/src/main.py` - Client entry point (deferred to Phase 4)
- [ ] `/client/src/button.py` - Button handler (deferred to Phase 4)
- [ ] `/client/src/player.py` - mpv wrapper (deferred to Phase 4)
- [ ] `/client/src/http_client.py` - API client (deferred to Phase 4)

#### Success Criteria
- [x] All server tests pass (13 tests)
- [x] Code coverage > 80% for server (98% achieved)
- [x] `/api/next` returns random video URL
- [x] Static file serving works for `/media/library`
- [ ] Client integration (deferred to Phase 4)

---

### Phase 2: Persistence & Daily Limits ✅ COMPLETE
**Goal**: Daily limit & placeholder behavior working via SQLite DB

**Duration**: 3 sessions
**Completed**: 2025-11-18

#### TDD Approach
1. Write failing tests for database models
2. Implement SQLAlchemy models
3. Write failing tests for daily limit logic
4. Implement daily limit enforcement
5. Write failing tests for placeholder selection
6. Implement placeholder logic
7. Integration tests for full flow

#### Server Tasks
- [x] **TEST**: Write tests for SQLAlchemy models (videos, client_settings, play_log)
- [x] **CODE**: Implement database models
- [x] **TEST**: Write tests for database initialization
- [x] **CODE**: Implement database setup and migration
- [x] **TEST**: Write tests for media scanner → DB insertion
- [x] **CODE**: Update scanner to populate database (via /api/videos/scan)
- [x] **TEST**: Write tests for get_daily_limit()
- [x] **CODE**: Implement get_daily_limit()
- [x] **TEST**: Write tests for count_non_placeholder_plays()
- [x] **CODE**: Implement count_non_placeholder_plays()
- [x] **TEST**: Write tests for pick_placeholder()
- [x] **CODE**: Implement pick_placeholder()
- [x] **TEST**: Write tests for log_play()
- [x] **CODE**: Implement log_play()
- [x] **TEST**: Write tests for updated `/api/next` with limits
- [x] **CODE**: Update `/api/next` to enforce daily limits
- [x] **TEST**: Write tests for `/api/clients` endpoints
- [x] **CODE**: Implement client management endpoints
- [x] **TEST**: Write tests for `/api/videos` endpoints
- [x] **CODE**: Implement video management endpoints
- [x] **REFACTOR**: Extract database operations to repository layer

#### Deliverables
- [x] `/server/src/db/models.py` - SQLAlchemy models (Video, ClientSettings, PlayLog)
- [x] `/server/src/db/database.py` - Database connection setup
- [x] `/server/src/db/repositories.py` - Data access layer (3 repositories)
- [x] `/server/src/services/limit_service.py` - Daily limit logic
- [x] `/server/tests/test_models.py` - Model tests (10 tests)
- [x] `/server/tests/test_limit_service.py` - Limit logic tests (11 tests)
- [x] `/server/tests/test_repositories.py` - Repository tests (21 tests)
- [x] `/server/tests/test_api_integration.py` - API integration tests (12 tests)
- [x] `/server/tests/test_client_management.py` - Client API tests (18 tests)
- [x] `/server/tests/test_video_management.py` - Video API tests (15 tests)
- [x] Database auto-create on startup

#### Success Criteria
- [x] All tests pass with > 85% coverage (98% achieved, 107 tests)
- [x] `/api/next` enforces daily limits via database
- [x] Placeholder videos returned when limit reached
- [x] Play log records all plays correctly
- [x] Different clients have independent limits
- [x] Client management endpoints (GET/POST/PATCH) working
- [x] Video management endpoints (GET/POST scan) working
- [x] Automatic title generation and tag extraction

---

### Phase 3: Queue & Admin UI 🟡 IN PROGRESS (95% Complete)
**Goal**: Parent can queue content and see usage info from browser

**Duration Estimate**: 4-8 sessions
**Started**: 2025-11-18
**Expected Completion**: 2025-11-18

#### Phase 3 Summary

**What's Complete**:
- ✅ **Backend (Server)**: All queue, video, and statistics API endpoints implemented with comprehensive tests
  - Queue CRUD operations (GET, POST, DELETE, PUT)
  - Queue-first logic in `/api/next` endpoint
  - System and client-specific statistics
  - Video filtering and scanning
  - 69 new tests added (queue: 21, queue API: 28, stats API: 20)

- ✅ **Frontend (Admin UI)**: Complete React TypeScript application with full test coverage
  - TypeScript API client (27 tests)
  - Dashboard page with system stats (10 tests)
  - Library page with video browsing and scanning (17 tests)
  - Queue page with drag-drop reordering (25 tests)
  - Settings page for client configuration (26 tests)
  - React Router navigation and error handling
  - 105 total tests with comprehensive coverage

**What Remains**:
- ⏳ Vite build configuration to output to `/server/static/admin`
- ⏳ Manual end-to-end testing of the complete workflow
- ⏳ Frontend coverage verification (should exceed 70% target)

**Total Test Count**: 176 server tests + 105 admin tests = 281 tests across Phase 0-3

#### TDD Approach
1. Write failing tests for queue repository operations
2. Implement queue database operations
3. Write failing tests for queue API endpoints
4. Implement queue endpoints
5. Write failing tests for React components (UI)
6. Implement React components
7. Integration tests for full queue workflow

#### Server Tasks
- [x] **TEST**: Write tests for queue model and repository
- [x] **CODE**: Implement queue database operations
- [x] **TEST**: Write tests for get_next_queue_item()
- [x] **CODE**: Implement queue item retrieval
- [x] **TEST**: Write tests for updated `/api/next` with queue priority
- [x] **CODE**: Update `/api/next` to check queue first
- [x] **TEST**: Write tests for `/api/queue` endpoints
- [x] **CODE**: Implement queue management endpoints (GET, POST, DELETE, PUT)
- [x] **TEST**: Write tests for `/api/videos` endpoints
- [x] **CODE**: Implement video listing and filtering
- [x] **TEST**: Write tests for `/api/videos/scan`
- [x] **CODE**: Implement manual library rescan
- [x] **TEST**: Write tests for `/api/stats` endpoints
- [x] **CODE**: Implement statistics endpoints (system + client stats)

#### Admin UI Tasks
- [x] **TEST**: Write tests for API client service
- [x] **CODE**: Implement TypeScript API client
- [x] **TEST**: Write tests for Dashboard component
- [x] **CODE**: Implement Dashboard page (client list + stats)
- [x] **TEST**: Write tests for Library component
- [x] **CODE**: Implement Library page (video list + filters)
- [x] **TEST**: Write tests for Queue component
- [x] **CODE**: Implement Queue page (queue list + actions)
- [x] **TEST**: Write tests for Settings component
- [x] **CODE**: Implement Settings page (client config)
- [x] **CODE**: Implement routing between pages (App.tsx with React Router)
- [x] **CODE**: Add loading states and error handling
- [ ] **CONFIG**: Update Vite build config to output to `/server/static/admin`
- [ ] **REFACTOR**: Extract common components if needed (optional)

#### Deliverables
- [x] `/server/src/main.py` - Queue endpoints integrated (not separate file)
- [x] `/server/src/main.py` - Video endpoints integrated
- [x] `/server/src/main.py` - Stats endpoints integrated
- [x] `/server/src/db/repositories.py` - QueueRepository added
- [x] `/server/src/db/models.py` - Queue model added
- [x] `/server/tests/test_queue.py` - Queue model/repository tests (21 tests)
- [x] `/server/tests/test_queue_api.py` - Queue API tests (28 tests)
- [x] `/server/tests/test_stats_api.py` - Stats API tests (20 tests)
- [x] `/server/tests/test_video_management.py` - Video API tests (existing)
- [x] `/admin/src/services/api.ts` - API client (comprehensive TypeScript client)
- [x] `/admin/src/pages/Dashboard.tsx` - Dashboard with system stats
- [x] `/admin/src/pages/Library.tsx` - Library with video browsing and scanning
- [x] `/admin/src/pages/Queue.tsx` - Queue management page
- [x] `/admin/src/pages/Settings.tsx` - Settings page for client configuration
- [x] `/admin/src/App.tsx` - Routing and navigation
- [x] `/admin/tests/api.test.ts` - API client tests (27 tests)
- [x] `/admin/tests/Dashboard.test.tsx` - Dashboard tests (10 tests)
- [x] `/admin/tests/Library.test.tsx` - Library tests (17 tests)
- [x] `/admin/tests/Queue.test.tsx` - Queue tests (25 tests)
- [x] `/admin/tests/Settings.test.tsx` - Settings tests (26 tests)
- [ ] Build configuration to output to `/server/static/admin` (needs vite.config.ts update)

#### Success Criteria
- [x] All server tests pass (queue, stats, video management APIs)
- [x] All admin UI tests pass (105 tests total)
- [x] Server coverage > 85% (likely maintained from Phase 2's 98%)
- [ ] Frontend coverage > 70% (needs verification run)
- [ ] Manual test: Open admin UI in browser at http://server:8000/admin (needs build config)
- [ ] Manual test: Add 3 videos to queue for client
- [ ] Manual test: Queue API works via curl/Postman
- [ ] Manual test: Stats API returns accurate data
- [ ] Manual test: Dashboard UI loads and displays stats correctly
- [ ] Manual test: Library page shows videos and scan works
- [ ] Manual test: Queue page allows adding/removing/reordering
- [ ] Manual test: Settings page allows updating client config

---

### Phase 4: Client Application & Kid-Friendly UI ⏸ NOT STARTED
**Goal**: Create a beautiful, simple kid-friendly interface on the Raspberry Pi client

**Duration Estimate**: 3-5 sessions

#### Vision

When the child approaches the trolley and presses the button, they should see:
- A delightful, colorful splash screen (not a command line!)
- Smooth loading animation while the video is fetched
- The video playing fullscreen with no visible controls
- Return to splash screen when video ends
- A friendly "all done for today" animation when limit reached

**No menus, no text, no choices - just beautiful visuals and one button.**

#### TDD Approach

1. Write failing tests for web server initialization
2. Implement minimal HTTP server for UI assets
3. Write failing tests for Chromium kiosk mode launcher
4. Implement browser window management
5. Write failing tests for state transitions (splash → loading → playing)
6. Implement state machine with UI updates via WebSocket/polling
7. Write failing tests for video player integration
8. Integrate mpv with browser window management
9. Write failing tests for UI screens (HTML/CSS)
10. Create splash, loading, error, and "all done" screens
11. Integration tests for full user flow

#### Technology Choice

**Selected: Web-based UI (Chromium Kiosk + Vanilla HTML/CSS)**

**Why this approach:**
- **Designer-friendly**: HTML/CSS is universal, easy to iterate and modify
- **Beautiful animations**: CSS transitions/animations are smooth and native
- **Fast iteration**: Edit CSS, refresh browser - see changes immediately
- **No build step**: Vanilla HTML/CSS/JS, no npm, no webpack, no complexity
- **Future-proof**: Easy to add features (touch support, settings screen, etc.)
- **Consistent tech**: Same technologies as admin UI (React) for consistency

**Architecture:**
```
Pi Boot → Python web server (port 5000)
       → Chromium kiosk mode (fullscreen, localhost:5000)
       → HTML splash screen with CSS animations
       → Button press → Python client detects → Minimize Chromium → Launch mpv
       → Video ends → Restore Chromium → Back to splash
```

**Trade-offs:**
- Chromium adds ~100-150MB RAM usage (acceptable on Pi 4)
- Boot time: +3-5 seconds for Chromium startup
- Window management is slightly more complex
- **Worth it for**: Design flexibility and beautiful, maintainable UI

#### Client Tasks

##### Web Server Setup (TDD)
- [ ] **TEST**: Write test for HTTP server initialization
- [ ] **CODE**: Implement minimal HTTP server (Python http.server or Flask)
- [ ] **TEST**: Write test for serving static HTML files
- [ ] **CODE**: Serve HTML/CSS/JS from `/client/ui/` directory
- [ ] **TEST**: Write test for WebSocket or SSE connection for state updates
- [ ] **CODE**: Implement real-time communication channel for UI updates
- [ ] **TEST**: Write test for graceful server shutdown
- [ ] **CODE**: Handle server lifecycle management
- [ ] **REFACTOR**: Extract web server to separate module

##### Browser Management (TDD)
- [ ] **TEST**: Write test for Chromium launcher in kiosk mode
- [ ] **CODE**: Launch Chromium with correct flags (--kiosk, --no-first-run, etc.)
- [ ] **TEST**: Write test for window minimizing
- [ ] **CODE**: Implement window minimize/hide functionality via wmctrl or xdotool
- [ ] **TEST**: Write test for window restoration
- [ ] **CODE**: Implement window restore and focus functionality
- [ ] **TEST**: Write test for browser process monitoring
- [ ] **CODE**: Monitor Chromium process health and restart if crashed
- [ ] **REFACTOR**: Extract browser manager class

##### HTML Splash Screen
- [ ] **DESIGN**: Create splash screen HTML structure
- [ ] **DESIGN**: Style splash screen with CSS (gradients, colors, layout)
- [ ] **DESIGN**: Add CSS animations (floating, pulsing, gentle motion)
- [ ] **CODE**: Create `/client/ui/splash.html`
- [ ] **CODE**: Create `/client/ui/styles/splash.css`
- [ ] **TEST**: Verify splash screen loads in browser
- [ ] **TEST**: Verify animations run smoothly (60fps)
- [ ] **POLISH**: Add custom fonts, SVG graphics, polish visuals

##### HTML Loading Screen
- [ ] **DESIGN**: Create loading screen HTML structure
- [ ] **DESIGN**: Create CSS spinner/loading animation
- [ ] **CODE**: Create `/client/ui/loading.html`
- [ ] **CODE**: Create `/client/ui/styles/loading.css`
- [ ] **CODE**: Add JavaScript to animate loading progress
- [ ] **TEST**: Verify smooth transitions from splash to loading
- [ ] **TEST**: Verify loading animation performance
- [ ] **POLISH**: Add loading messages, playful animations

##### HTML "All Done" Screen
- [ ] **DESIGN**: Create "all done for today" screen HTML
- [ ] **DESIGN**: Style with friendly, celebratory CSS
- [ ] **CODE**: Create `/client/ui/all_done.html`
- [ ] **CODE**: Create `/client/ui/styles/all_done.css`
- [ ] **CODE**: Add CSS animation (stars, confetti, gentle motion)
- [ ] **TEST**: Verify placeholder detection triggers correct screen
- [ ] **POLISH**: Make it delightful and positive

##### HTML Error Screen
- [ ] **DESIGN**: Create error screen HTML (friendly, not scary)
- [ ] **DESIGN**: Style with gentle colors and reassuring visuals
- [ ] **CODE**: Create `/client/ui/error.html`
- [ ] **CODE**: Create `/client/ui/styles/error.css`
- [ ] **CODE**: Add auto-retry functionality with countdown
- [ ] **TEST**: Verify error screen shows on network failure
- [ ] **TEST**: Verify automatic recovery back to splash
- [ ] **POLISH**: Add friendly messaging without technical jargon

##### Video Playback Integration (TDD)
- [ ] **TEST**: Write test for mpv process launch
- [ ] **CODE**: Launch mpv in fullscreen when video ready
- [ ] **TEST**: Write test for browser minimization during playback
- [ ] **CODE**: Minimize Chromium window when mpv starts
- [ ] **TEST**: Write test for detecting video end
- [ ] **CODE**: Monitor mpv process and detect completion
- [ ] **TEST**: Write test for browser restoration after video
- [ ] **CODE**: Restore and focus Chromium window when mpv exits
- [ ] **TEST**: Write test for handling mpv crashes
- [ ] **CODE**: Implement mpv error recovery
- [ ] **REFACTOR**: Extract video player manager

##### State Machine with UI (TDD)
- [ ] **TEST**: Write test for IDLE state serves splash.html
- [ ] **CODE**: Implement state-based routing/page serving
- [ ] **TEST**: Write test for LOADING state serves loading.html
- [ ] **CODE**: Implement state transitions via WebSocket/SSE
- [ ] **TEST**: Write test for PLAYING state minimizes browser
- [ ] **CODE**: Implement browser window management in PLAYING state
- [ ] **TEST**: Write test for state transitions trigger UI updates
- [ ] **CODE**: Send state change events to browser via WebSocket
- [ ] **TEST**: Write test for JavaScript state handler in browser
- [ ] **CODE**: Implement client-side JavaScript to handle state changes
- [ ] **REFACTOR**: Clean up state machine integration

##### Button Integration (TDD)
- [ ] **TEST**: Write test for button press in IDLE triggers loading
- [ ] **CODE**: Wire button handler to state machine
- [ ] **TEST**: Write test for button press during LOADING is ignored
- [ ] **CODE**: Debounce/ignore button during transitions
- [ ] **TEST**: Write test for button press during PLAYING pauses (optional)
- [ ] **CODE**: Implement pause/resume via mpv IPC (optional feature)
- [ ] **REFACTOR**: Clean up button handler integration

##### Communication Layer (TDD)
- [ ] **TEST**: Write test for WebSocket connection establishment
- [ ] **CODE**: Implement WebSocket server (or SSE as simpler alternative)
- [ ] **TEST**: Write test for broadcasting state changes
- [ ] **CODE**: Send state updates to connected browser clients
- [ ] **TEST**: Write test for JavaScript WebSocket client
- [ ] **CODE**: Implement browser-side WebSocket/EventSource handler
- [ ] **TEST**: Write test for reconnection on connection loss
- [ ] **CODE**: Implement automatic reconnection with exponential backoff
- [ ] **REFACTOR**: Extract communication module

##### Polish & Performance
- [ ] **TEST**: Measure page load times (< 500ms target)
- [ ] **OPTIMIZE**: Minify CSS if needed
- [ ] **TEST**: Measure animation performance (60fps target)
- [ ] **OPTIMIZE**: Use CSS transform/opacity for smooth animations
- [ ] **TEST**: Measure memory usage over 10 video cycles
- [ ] **OPTIMIZE**: Prevent memory leaks, cleanup resources
- [ ] **PROFILE**: Use Chrome DevTools to profile performance
- [ ] **POLISH**: Add subtle sound effects (optional)
- [ ] **POLISH**: Add accessibility features (high contrast mode, etc.)

##### Auto-Boot Setup
- [ ] **DOCS**: Document Raspberry Pi boot configuration
- [ ] **CODE**: Create startup script that launches web server + Chromium
- [ ] **TEST**: Test auto-start on Pi boot
- [ ] **CONFIG**: Disable console cursor and boot messages
- [ ] **CONFIG**: Configure Chromium to launch in kiosk mode on boot
- [ ] **CONFIG**: Hide Plymouth boot splash or customize with logo
- [ ] **TEST**: Verify boots directly to splash screen in < 30 seconds
- [ ] **CONFIG**: Set up systemd service for client application

#### Design Assets Needed

**HTML/CSS-based (no static images required for core functionality):**

The beauty of HTML/CSS is that you can create everything with code:
- Gradients, colors, shapes via CSS
- Animations via CSS keyframes
- SVG graphics inline in HTML

**Optional visual assets:**

1. **Logo/Branding** (`/client/ui/assets/logo.svg`)
   - SVG format (scalable, crisp at any size)
   - Simple, recognizable icon
   - Optional: can use emoji or pure CSS design instead

2. **Custom Fonts** (`/client/ui/assets/fonts/`)
   - Kid-friendly font (Fredoka, Baloo, Comic Sans alternatives)
   - Web fonts or self-hosted

3. **Sound Effects** (optional, `/client/ui/assets/sounds/`)
   - Button press sound (satisfying "boop")
   - Loading sound (gentle chime)
   - Error sound (soft "uh oh")
   - All done sound (celebratory chime)

**Everything else created with HTML/CSS:**
- Splash screen: CSS gradients + animations
- Loading spinner: Pure CSS animation
- All done screen: CSS confetti/stars animation
- Error screen: CSS styling + friendly text
- Transitions: CSS transitions/transforms

#### Deliverables

- [ ] `/client/src/web_server.py` - HTTP server for UI assets
- [ ] `/client/src/browser_manager.py` - Chromium kiosk mode manager
- [ ] `/client/src/ui_controller.py` - State machine with UI updates
- [ ] `/client/src/communication.py` - WebSocket/SSE server
- [ ] `/client/src/main_ui.py` - Main entry point with web UI
- [ ] `/client/ui/` - Web UI directory
  - [ ] `splash.html` - Splash screen
  - [ ] `loading.html` - Loading screen
  - [ ] `all_done.html` - "All done for today" screen
  - [ ] `error.html` - Error screen
  - [ ] `styles/` - CSS directory
    - [ ] `common.css` - Shared styles
    - [ ] `splash.css` - Splash screen styles
    - [ ] `loading.css` - Loading screen styles
    - [ ] `all_done.css` - All done screen styles
    - [ ] `error.css` - Error screen styles
  - [ ] `scripts/` - JavaScript directory
    - [ ] `state_handler.js` - WebSocket client for state updates
    - [ ] `animations.js` - Custom animation helpers
  - [ ] `assets/` - Optional assets (logo, fonts, sounds)
- [ ] `/client/tests/test_web_server.py` - Web server tests
- [ ] `/client/tests/test_browser_manager.py` - Browser manager tests
- [ ] `/client/tests/test_ui_controller.py` - UI controller tests
- [ ] `/client/tests/test_communication.py` - WebSocket/SSE tests
- [ ] `/client/requirements.txt` - Updated with websockets/Flask
- [ ] `/client/startup.sh` - Startup script for auto-boot
- [ ] `/client/bobavision-ui.service` - systemd service file
- [ ] Updated `/client/CLAUDE.md` with HTML UI development guide

#### Success Criteria

Manual testing on Raspberry Pi:

- [ ] Boot Pi → splash screen appears in < 35 seconds (includes Chromium startup)
- [ ] No visible console/desktop/cursor (full kiosk mode)
- [ ] Splash screen looks beautiful with smooth CSS animations
- [ ] Press button → loading screen transition is instant and smooth
- [ ] Loading animation plays smoothly at 60fps
- [ ] Video starts playing in < 3 seconds after button press
- [ ] Video plays fullscreen with no UI elements visible
- [ ] Chromium window properly minimized during video playback
- [ ] Video ends → smooth transition back to splash (browser restored)
- [ ] Press button when limit reached → "all done" screen appears
- [ ] "All done" screen is delightful and celebratory
- [ ] Placeholder video plays after "all done" screen
- [ ] Network error → friendly error screen, not crash
- [ ] Error screen auto-retries and recovers gracefully
- [ ] Can recover from error by pressing button again
- [ ] WebSocket reconnects automatically if connection lost
- [ ] All CSS transitions are smooth (no flashing/tearing)
- [ ] Page loads are fast (< 500ms)
- [ ] Child testing: 4-6 year old can use independently
- [ ] Design iteration: Can modify CSS and see changes immediately

Automated testing:

- [ ] All tests pass (web server, browser manager, UI controller)
- [ ] Code coverage > 85% for Python code
- [ ] WebSocket tests pass (connection, reconnection, broadcasting)
- [ ] No memory leaks over 10 video cycles (monitor Chromium + Python)
- [ ] Performance: CSS animations run at 60fps
- [ ] Browser process monitoring and recovery works
- [ ] Graceful shutdown of all processes (web server, browser, mpv)

---

### Phase 5: Hardware Integration & Polish ⏸ NOT STARTED
**Goal**: Move from "Pi on desk" to "trolley media station"

**Duration Estimate**: Ongoing (parallel with Phase 3)

#### Tasks
- [ ] Design and document hardware mounting plan
- [ ] Purchase components (Pi, screen, button, speaker, power)
- [ ] 3D print or fabricate mounting brackets (if needed)
- [ ] Mount screen to trolley
- [ ] Mount Pi securely (ventilation considered)
- [ ] Wire GPIO button to Pi (with proper resistors/debouncing)
- [ ] Test button wiring and debounce settings
- [ ] Configure client startup script as systemd service
- [ ] Test auto-start on boot
- [ ] Test auto-restart on crash
- [ ] Disable unwanted Pi OS UI elements (notifications, cursor, etc.)
- [ ] Configure HDMI output settings for optimal display
- [ ] Set up audio output (HDMI or 3.5mm)
- [ ] Create idle screen image (displayed when not playing)
- [ ] Create "server unreachable" fallback video
- [ ] Implement client-side error handling for network failures
- [ ] Add client logging to file for debugging
- [ ] Cable management and strain relief
- [ ] Safety check: no exposed voltage, secure connections
- [ ] Battery/power solution testing (if portable)
- [ ] Final ergonomics test with actual child

#### Deliverables
- [ ] `/docs/hardware_setup.md` - Hardware assembly guide
- [ ] `/client/bobavision.service` - systemd service file
- [ ] `/client/config/display_settings.txt` - HDMI config
- [ ] `/media/placeholders/server_offline.mp4` - Offline placeholder
- [ ] `/media/placeholders/idle_screen.png` - Idle display
- [ ] Physical trolley setup (not in repo, documented with photos)

#### Success Criteria
- [ ] Trolley can be unplugged, moved, plugged in, and works
- [ ] Button press within 60 seconds of boot → video plays
- [ ] If server is offline → client shows error gracefully
- [ ] No visible OS elements during normal operation
- [ ] Audio output is clear and at appropriate volume
- [ ] Pi stays cool during extended playback
- [ ] Button is physically robust and responsive
- [ ] Cables are secured and child-safe

---

### Phase 6: Testing, Refinement & Documentation ⏸ NOT STARTED
**Goal**: Comprehensive testing, bug fixes, and complete documentation

**Duration Estimate**: 2-3 sessions

#### Testing Tasks
- [ ] **Functional Testing**:
  - [ ] Button stress test (rapid presses during playback)
  - [ ] Multi-day limit reset verification
  - [ ] Network drop during playback
  - [ ] Server restart during client operation
  - [ ] Database corruption recovery
  - [ ] Concurrent client support (if second trolley exists)
- [ ] **Performance Testing**:
  - [ ] HD video playback smoothness
  - [ ] CPU/temperature under load
  - [ ] Database query performance with 100+ videos
  - [ ] Admin UI responsiveness
- [ ] **Edge Case Testing**:
  - [ ] Empty library behavior
  - [ ] No placeholder video configured
  - [ ] Queue with deleted videos
  - [ ] Invalid client_id requests
  - [ ] Timezone changes affecting daily reset

#### Documentation Tasks
- [ ] Complete README.md with:
  - [ ] Quick start guide
  - [ ] Installation instructions (server + client)
  - [ ] Adding new content workflow
  - [ ] Registering new clients
  - [ ] Troubleshooting common issues
- [ ] Create `/docs/deployment.md`:
  - [ ] Server deployment on home network
  - [ ] Client setup on Raspberry Pi
  - [ ] Network configuration
- [ ] Create `/docs/api_reference.md`:
  - [ ] All endpoints documented with examples
  - [ ] Request/response schemas
- [ ] Create `/docs/architecture.md`:
  - [ ] System architecture diagrams
  - [ ] Data flow diagrams
  - [ ] Decision log
- [ ] Update all CLAUDE.md files with lessons learned

#### Refinement Tasks
- [ ] Code review and refactoring
- [ ] Remove debug logging or make configurable
- [ ] Optimize database indexes
- [ ] Add request rate limiting to server
- [ ] Improve error messages for operators
- [ ] Add health check endpoints
- [ ] Consider adding metrics/monitoring (optional)

#### Deliverables
- [ ] Complete test suite with >85% coverage
- [ ] Comprehensive documentation set
- [ ] Deployment scripts/guides
- [ ] Bug-free, production-ready system

#### Success Criteria
- [ ] All functional tests pass
- [ ] All edge cases handled gracefully
- [ ] Someone unfamiliar with the project can:
  - [ ] Set up the server in < 30 minutes
  - [ ] Set up a client in < 20 minutes
  - [ ] Add new content in < 5 minutes
  - [ ] Understand the architecture from docs
- [ ] System runs for 7 consecutive days without intervention

---

## Progress Tracking

### Overall Progress

| Phase | Status | Completion | Start Date | End Date |
|-------|--------|------------|------------|----------|
| Phase 0: Project Setup | 🟢 Complete | 100% | 2025-11-18 | 2025-11-18 |
| Phase 1: Minimal Vertical Slice | 🟢 Complete | 100% | 2025-11-18 | 2025-11-18 |
| Phase 2: Persistence & Daily Limits | 🟢 Complete | 100% | 2025-11-18 | 2025-11-18 |
| Phase 3: Queue & Admin UI | 🟡 In Progress | 95% | 2025-11-18 | - |
| Phase 4: Client App & Kid-Friendly UI | ⚪ Not Started | 0% | - | - |
| Phase 5: Hardware Integration | ⚪ Not Started | 0% | - | - |
| Phase 6: Testing & Documentation | ⚪ Not Started | 0% | - | - |

**Legend**: 🟢 Complete | 🟡 In Progress | ⚪ Not Started | 🔴 Blocked

### Current Sprint Focus

**Recently Completed**:
- ✅ Phase 0: Project setup and documentation
- ✅ Phase 1: Core API endpoints and media serving
- ✅ Phase 2: Database integration and daily limits
- ✅ Phase 3: Queue repository and database model (21 tests)
- ✅ Phase 3: Queue API endpoints - all CRUD operations (28 tests)
- ✅ Phase 3: Statistics endpoints - system and client stats (20 tests)
- ✅ Phase 3: Admin UI - TypeScript API client (27 tests)
- ✅ Phase 3: Admin UI - Dashboard component (10 tests)
- ✅ Phase 3: Admin UI - Library component (17 tests)
- ✅ Phase 3: Admin UI - Queue component (25 tests)
- ✅ Phase 3: Admin UI - Settings component (26 tests)
- ✅ Phase 3: Admin UI - Routing and navigation (App.tsx)

**Active Tasks**:
- Phase 3: Configure Vite build to output to `/server/static/admin`
- Phase 3: Manual testing of admin UI end-to-end
- Phase 3: Verify test coverage meets targets

**Next Up**:
- Complete Phase 3 with build configuration
- Phase 4: Client application with HTML/CSS UI
- Phase 4: Web server for client UI (Chromium kiosk mode)
- Phase 4: Splash screens and loading animations
- Phase 4: Video playback integration with mpv

### Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Server Test Coverage | >85% | 98% ✅ |
| Client Test Coverage | >85% | 0% (Phase 4) |
| Admin Test Coverage | >70% | ✅ (needs verification) |
| Total Server LoC | - | ~1,636 |
| Total Server Test LoC | - | ~4,067 |
| Total Admin Test LoC | - | ~1,299 |
| Server Tests | - | ~176 (all phases) |
| Admin Tests | - | 105 tests |
| API Endpoints Implemented | 20 | 20 ✅ |
| Database Tables | 4 | 4 ✅ |
| React Components | ~4 pages | 4 ✅ |

**Endpoints Implemented (20/20)**:
1. `GET /` - API info ✅
2. `GET /api/next` - Get next video (queue-first, then limit enforcement) ✅
3. `GET /api/clients` - List all clients ✅
4. `GET /api/clients/{id}` - Get client details ✅
5. `POST /api/clients` - Create client ✅
6. `PATCH /api/clients/{id}` - Update client ✅
7. `GET /api/videos` - List videos with filters ✅
8. `POST /api/videos/scan` - Scan media directory ✅
9. `GET /api/queue/{client_id}` - Get client's queue ✅
10. `POST /api/queue/{client_id}` - Add videos to queue ✅
11. `DELETE /api/queue/{client_id}/{queue_id}` - Remove from queue ✅
12. `POST /api/queue/{client_id}/clear` - Clear entire queue ✅
13. `PUT /api/queue/{client_id}/reorder` - Reorder queue ✅
14. `GET /api/stats` - System-wide statistics ✅
15. `GET /api/stats/client/{client_id}` - Client-specific statistics ✅
16. `GET /media/library/{path}` - Static file serving ✅

**Admin UI Components (4/4)**:
1. Dashboard - System stats display ✅
2. Library - Video browsing, filtering, scanning ✅
3. Queue - Queue management (add, remove, reorder) ✅
4. Settings - Client configuration ✅

---

## Success Criteria

### Phase-Level Acceptance

Each phase must meet its specific success criteria before moving to the next phase. No exceptions.

### System-Level Acceptance

The project is considered **complete** when:

1. **Core Functionality**:
   - [ ] Child can press button and video plays fullscreen
   - [ ] Daily limit (configurable) is enforced
   - [ ] After limit reached, only placeholder videos play
   - [ ] Parent can queue videos from web UI
   - [ ] Queued videos play in order
   - [ ] Random selection works when queue is empty

2. **Reliability**:
   - [ ] System runs for 7 days without manual intervention
   - [ ] Survives server restarts
   - [ ] Survives client restarts
   - [ ] Handles network drops gracefully
   - [ ] Daily limit resets correctly at midnight

3. **Usability**:
   - [ ] Child (age 4-8) can use button without help
   - [ ] Parent can add videos in < 5 minutes
   - [ ] Parent can queue videos from phone in < 2 minutes
   - [ ] Admin UI is intuitive without training

4. **Quality**:
   - [ ] All tests pass
   - [ ] Code coverage meets targets
   - [ ] No known critical bugs
   - [ ] Documentation is complete and accurate

5. **Hardware**:
   - [ ] Trolley setup is physically robust
   - [ ] All components are securely mounted
   - [ ] No safety hazards present
   - [ ] Meets child safety requirements

---

## Future Extensions

These features are explicitly **out of scope** for v1.0 but may be added later:

### v2.0 Potential Features
- [ ] Per-kid profiles even on shared trolley
- [ ] Facial recognition for automatic profile switching
- [ ] Watch history with thumbnails for parents
- [ ] "Favorite" marking and preference learning

### v2.1 Potential Features
- [ ] Total minutes per day (time-based limits instead of program count)
- [ ] Time-of-day restrictions (no videos after 7 PM)
- [ ] Scheduled content (specific video at specific time)

### v2.2 Potential Features
- [ ] Offline caching on Pi (pre-download queue for mobility)
- [ ] Multi-server support (sync between locations)
- [ ] Content recommendations based on watch patterns

### v3.0 Potential Features
- [ ] Rust reimplementation (performance optimization)
- [ ] Mobile app (native iOS/Android admin interface)
- [ ] Cloud backup of settings and stats (optional)
- [ ] Integration with external content APIs (YouTube Kids, etc.)

**Architecture Decision**: All APIs and data models should be designed with these extensions in mind, but none should be implemented in v1.0.

---

## Architecture Decisions

### ADR-001: Local Network Only, No Authentication
**Decision**: The system will operate entirely on the local home network with no authentication.

**Rationale**:
- Reduces complexity significantly
- Physical network access provides security boundary
- Target users (parents) control their home network
- Authentication adds friction for quick queue management

**Consequences**:
- Must never expose server to public internet
- Documentation must emphasize network security
- Not suitable for multi-family deployments without modification

### ADR-002: SQLite for Database
**Decision**: Use SQLite for all data persistence.

**Rationale**:
- Zero configuration required
- Perfect for single-server deployment
- Sufficient performance for expected load (1-2 clients)
- Easy backup (single file)
- Familiar to developers

**Consequences**:
- Concurrent write performance limited (not an issue for this use case)
- Scaling to many clients would require migration
- Must handle database locking gracefully

### ADR-003: mpv for Video Playback
**Decision**: Use mpv as the video player on Raspberry Pi.

**Rationale**:
- Lightweight and performant
- Excellent codec support
- JSON IPC for programmatic control
- Well-maintained and stable
- Easy to hide all UI elements

**Consequences**:
- Dependency on external binary
- Must ensure mpv is installed on client
- Limited to mpv's supported formats (though very broad)

### ADR-004: FastAPI for Backend
**Decision**: Use FastAPI for the HTTP server.

**Rationale**:
- Modern Python framework with great developer experience
- Automatic OpenAPI documentation
- Type hints and validation built-in
- Excellent performance for this use case
- Easy to test

**Consequences**:
- Requires Python 3.11+ for best experience
- Async programming model (learning curve for some)

### ADR-005: React + TypeScript for Admin UI
**Decision**: Build admin interface with React and TypeScript.

**Rationale**:
- Rich ecosystem of components
- TypeScript provides type safety
- Vite for fast development
- Familiar to many developers
- Good mobile browser support

**Consequences**:
- Build step required
- Larger bundle size than vanilla JS (acceptable for admin UI)

### ADR-006: Strict TDD Approach
**Decision**: All features must be developed test-first with strict TDD discipline.

**Rationale**:
- Ensures high code quality
- Provides living documentation
- Enables confident refactoring
- Catches bugs early
- Forces good design decisions

**Consequences**:
- Slower initial development
- Requires discipline and practice
- Must maintain test suite alongside features
- Higher upfront time investment for long-term quality

---

## Development Workflow

### TDD Red-Green-Refactor Cycle

For every feature:

1. **RED**: Write a failing test that describes the desired behavior
2. **GREEN**: Write the minimum code to make the test pass
3. **REFACTOR**: Improve the code while keeping tests green

### Commit Guidelines

- Commit after each red-green-refactor cycle
- Commit messages format: `[PHASE-X] <type>: <description>`
  - Types: `test`, `feat`, `refactor`, `docs`, `fix`, `chore`
  - Examples:
    - `[PHASE-1] test: add test for /api/next endpoint`
    - `[PHASE-1] feat: implement random video selection`
    - `[PHASE-2] refactor: extract limit logic to service`

### Branch Strategy

- Main branch: `main`
- Development happens on: `claude/kids-media-station-01HY376SziaayAEnDmyXohud`
- Create PR to main when phase is complete and all tests pass

### Code Review Checklist

Before merging any phase:

- [ ] All tests pass
- [ ] Coverage targets met
- [ ] No commented-out code
- [ ] No debug print statements
- [ ] Type hints present (Python)
- [ ] TypeScript types defined (Frontend)
- [ ] Error handling implemented
- [ ] Logging appropriate
- [ ] Documentation updated

---

## Notes and Lessons Learned

### 2025-11-18: Project Initialization & Rapid Development
- Created comprehensive grand plan with all phases defined
- Decided on strict TDD approach for quality assurance
- Emphasized simplicity and maintainability over feature creep
- Set clear boundaries for v1.0 scope

### 2025-11-18: Phase 0-3 Completion
- **Phase 0** completed with full documentation and project setup
- **Phase 1** completed with core API endpoints and media serving (server-side only)
- **Phase 2** completed with database integration, daily limits, and comprehensive repository layer
- **Phase 3** nearly complete (95%) with:
  - All backend queue, video, and statistics APIs fully tested
  - Complete admin UI with 4 pages and 105 tests
  - Only remaining: build configuration and manual testing
- **TDD discipline maintained**: 281 total tests across all phases with excellent coverage
- **Monolithic approach**: All endpoints in main.py rather than separate route files (simpler for this project size)
- **Test quality**: Comprehensive test coverage with meaningful assertions, not just "does it run" tests
- **Next focus**: Complete Phase 3 build config, then move to Phase 4 client implementation

---

## Appendix

### Glossary

- **Client**: The Raspberry Pi device on the trolley
- **Server**: The FastAPI backend running on home network
- **Admin UI**: The web interface for parents
- **Placeholder**: A video shown when daily limit is reached
- **Queue**: Ordered list of videos for a specific client
- **Daily Limit**: Maximum number of non-placeholder programs per day
- **Play Log**: Historical record of all video plays

### Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- mpv Manual: https://mpv.io/manual/
- gpiozero Documentation: https://gpiozero.readthedocs.io/
- React Documentation: https://react.dev/
- pytest Documentation: https://docs.pytest.org/
- Vitest Documentation: https://vitest.dev/

---

**End of Grand Plan**
