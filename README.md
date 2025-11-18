# Kids Single-Button Media Station

A custom media player system for young children featuring single-button interaction, enforced daily screen time limits, and centralized parent control.

## Overview

This system allows children to watch videos with one button press while parents maintain complete control over content and viewing limits through a web interface.

### Key Features

- 🎯 **Single-button interaction** - No menus, no choices, just one button
- ⏱️ **Daily program limits** - Configurable viewing limits per device
- 🎬 **Parent-controlled queue** - Parents select content from web UI
- 🏠 **Local network only** - No internet dependency, complete privacy
- 🔒 **Safe by design** - Fails gracefully, child-appropriate error handling

## System Architecture

```
┌─────────────────────────────────────────────────┐
│              Home LAN Network                   │
│                                                 │
│  ┌──────────────┐      ┌──────────────┐       │
│  │ Media Server │◄─────┤  Admin Web   │       │
│  │  (FastAPI)   │      │  (Browser)   │       │
│  └──────┬───────┘      └──────────────┘       │
│         │                                       │
│         │ HTTP                                  │
│         │                                       │
│  ┌──────▼────────┐                             │
│  │ Client (Pi)   │                             │
│  │ - Button      │──► GPIO Pin 17              │
│  │ - mpv Player  │──► HDMI to Screen           │
│  └───────────────┘                             │
└─────────────────────────────────────────────────┘
```

## Components

- **Server**: FastAPI backend serving media and API
- **Client**: Raspberry Pi with button and screen
- **Admin UI**: React web interface for parents

## Quick Start

### Prerequisites

**Choose one deployment method:**

#### Option A: Docker (Recommended for Production)
- [Docker](https://www.docker.com/) - Container runtime
- [Docker Compose](https://docs.docker.com/compose/) - Multi-container orchestration

#### Option B: Native Python (Development)
- Python 3.11+
- [UV](https://astral.sh/uv) - Fast Python package manager (for server & client)
- [Bun](https://bun.sh) - Fast JavaScript runtime (for admin UI)
- Raspberry Pi OS (for client hardware)

---

### Server Setup (Docker) - RECOMMENDED

The containerized setup includes all dependencies (Python, FastAPI, mpv, ffmpeg) with zero configuration:

```bash
# Clone repository
git clone <repo-url>
cd bobavision

# Start server with docker-compose
docker-compose up -d

# Server is now running at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

**Data persistence**: The container automatically creates:
- `./data/` - SQLite database
- `./media/` - Video library directory

To add videos:
```bash
# Copy videos to media directory
cp /path/to/videos/*.mp4 ./media/library/

# Trigger library scan
curl -X POST http://localhost:8000/api/videos/scan
```

**Container commands**:
```bash
# View logs
docker-compose logs -f server

# Stop server
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Access container shell
docker-compose exec server sh
```

---

### Server Setup (Native Python) - DEVELOPMENT

For active development with hot-reload:

```bash
cd server

# Install dependencies with UV
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run tests
pytest

# Start server with auto-reload
uvicorn src.main:app --reload --port 8000
```

### Client Setup (Raspberry Pi)

```bash
cd client

# Install dependencies with UV
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run tests
pytest

# Start client
python src/main.py
```

### Admin UI Setup

```bash
cd admin

# Install dependencies with Bun
bun install

# Run tests
bun test

# Start development server
bun run dev
```

## Development

This project follows strict **Test-Driven Development (TDD)** principles.

### TDD Workflow

1. **🔴 RED**: Write a failing test
2. **🟢 GREEN**: Write minimal code to pass
3. **♻️ REFACTOR**: Improve code while keeping tests green

See [docs/tdd_guide.md](docs/tdd_guide.md) for detailed TDD practices.

### Project Structure

```
bobavision/
├── CLAUDE.md              # Development guide (start here!)
├── README.md              # This file
├── docs/
│   ├── grand_plan.md      # Complete project plan
│   └── tdd_guide.md       # TDD principles
├── server/                # FastAPI backend
├── client/                # Raspberry Pi client
├── admin/                 # React admin UI
└── media/                 # Video files
```

### Running Tests

```bash
# Server tests
cd server && pytest --cov=src

# Client tests
cd client && pytest --cov=src

# Admin tests
cd admin && bun test
```

### Commit Convention

```
[PHASE-X] <type>: <description>

Types: test, feat, refactor, fix, docs, chore
```

## Current Status

**Phase**: 4 - Client Application & Kid-Friendly UI (Complete - 75%)
**Current**: Phase 5 - Server Containerization (In Progress)
**Next**: Phase 5 - Hardware Integration & Polish

### Recent Updates (2025-11-18)
- ✅ Phase 0-4 Complete: Full server, admin UI, and client implementation
- 🐳 **NEW**: Docker containerization with mpv (ADR-007)
- 📦 Server now deployable as a single container with all dependencies
- 🎯 305 unit tests + 24 E2E tests passing
- 📊 Server coverage: 98.29% | Client: 85% | Admin: 89.04%

See [docs/grand_plan.md](docs/grand_plan.md) for complete roadmap.

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Main development guide
- **[docs/grand_plan.md](docs/grand_plan.md)** - Complete project vision and phases
- **[docs/tdd_guide.md](docs/tdd_guide.md)** - TDD principles and examples
- **[server/CLAUDE.md](server/CLAUDE.md)** - Backend development guide
- **[client/CLAUDE.md](client/CLAUDE.md)** - Raspberry Pi client guide
- **[admin/CLAUDE.md](admin/CLAUDE.md)** - Frontend development guide

## Hardware Requirements

### Raspberry Pi Client

- Raspberry Pi 4 (2-4GB RAM)
- 7-10" HDMI display
- Large momentary push button
- Speaker/soundbar
- Power supply or USB-C PD powerbank

See [docs/hardware_setup.md](docs/hardware_setup.md) (Phase 4) for detailed assembly.

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Client**: Python, gpiozero, mpv
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Testing**: pytest, Vitest, React Testing Library
- **Package Management**: UV (Python), Bun (JavaScript)
- **Deployment**: Docker, Docker Compose (containerized with mpv)

## License

Private project - All rights reserved

## Development

For development instructions, see [CLAUDE.md](CLAUDE.md).

To get started:
1. Read [docs/grand_plan.md](docs/grand_plan.md)
2. Follow the current phase tasks
3. Use strict TDD for all features
4. Update progress in grand_plan.md

---

**Built with ❤️ for kids who need healthy screen time boundaries**
