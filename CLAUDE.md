# Kids Single-Button Media Station - Development Guide

## Welcome, Claude!

This is the main entry point for developing the Kids Single-Button Media Station project. This file will guide you through the project structure, development workflow, and point you to the right resources.

**Current Phase**: Phase 0 - Project Setup
**Last Updated**: 2025-11-18

---

## Quick Navigation

- **[Grand Plan](docs/grand_plan.md)** ⭐ - The complete project vision, all phases, and progress tracking
- **[TDD Guide](docs/tdd_guide.md)** - Test-driven development principles and workflow
- **[Server Development](server/CLAUDE.md)** - Backend development guide
- **[Client Development](client/CLAUDE.md)** - Raspberry Pi client guide
- **[Admin UI Development](admin/CLAUDE.md)** - Frontend development guide

---

## Project Overview

This is a custom media player system for young children with three main goals:

1. **Single-button interaction** - No menus, no choices, just one button
2. **Daily program limits** - Enforced screen time limits (e.g., 3 programs/day)
3. **Centralized parent control** - Web UI for queue management and settings

### System Components

```
┌─────────────────────────────────────────┐
│         Home LAN Network                │
│                                         │
│  ┌──────────┐      ┌──────────┐       │
│  │  Server  │◄─────┤  Admin   │       │
│  │ (FastAPI)│      │ (Browser)│       │
│  └────┬─────┘      └──────────┘       │
│       │                                │
│  ┌────▼─────┐                          │
│  │  Client  │                          │
│  │  (Pi)    │──► Button + Screen      │
│  └──────────┘                          │
└─────────────────────────────────────────┘
```

---

## Getting Started

### First Time Setup

1. **Read the Grand Plan**:
   ```
   Open and read: docs/grand_plan.md
   ```
   This contains the full vision, requirements, and all development phases.

2. **Understand TDD Workflow**:
   ```
   Open and read: docs/tdd_guide.md
   ```
   All development follows strict test-driven development.

3. **Set Up Your Environment**:
   - Python 3.11+ installed
   - Node.js 18+ and npm installed
   - Git configured

4. **Check Current Phase**:
   - Open `docs/grand_plan.md` and find the "Progress Tracking" section
   - See which phase is currently active
   - Review the tasks for that phase

### Current Phase: Phase 0 - Project Setup

**What to do right now**:

- [ ] Set up Python environment for server (see [server/CLAUDE.md](server/CLAUDE.md))
- [ ] Set up Python environment for client (see [client/CLAUDE.md](client/CLAUDE.md))
- [ ] Set up Node/npm environment for admin (see [admin/CLAUDE.md](admin/CLAUDE.md))
- [ ] Configure test frameworks for all components
- [ ] Create .gitignore
- [ ] Create README.md

**Expected outcome**: All tooling is in place and you can run empty test suites successfully.

---

## Development Workflow

### TDD Red-Green-Refactor Cycle

**For every feature, follow this cycle religiously**:

1. **🔴 RED**: Write a failing test
   - Think about the behavior you want
   - Write a test that describes it
   - Run the test and watch it fail
   - Commit: `[PHASE-X] test: add test for <feature>`

2. **🟢 GREEN**: Make it pass
   - Write the minimum code to pass the test
   - Don't worry about elegance yet
   - Run the test and watch it pass
   - Commit: `[PHASE-X] feat: implement <feature>`

3. **♻️ REFACTOR**: Clean up
   - Improve the code structure
   - Keep tests green
   - Commit: `[PHASE-X] refactor: improve <component>`

4. **Repeat** for the next small piece of functionality

### Working on a Task

1. **Identify the task** from the current phase in `docs/grand_plan.md`
2. **Navigate to the component's CLAUDE.md**:
   - Server tasks → `server/CLAUDE.md`
   - Client tasks → `client/CLAUDE.md`
   - Admin tasks → `admin/CLAUDE.md`
3. **Follow the TDD cycle** as described in that component's guide
4. **Update progress** in `docs/grand_plan.md` by checking off completed tasks

### Commit Message Format

```
[PHASE-X] <type>: <description>

<optional body>
```

**Types**:
- `test` - Adding or modifying tests
- `feat` - Adding or modifying features
- `refactor` - Refactoring existing code
- `fix` - Bug fixes
- `docs` - Documentation updates
- `chore` - Build, dependencies, tooling

**Examples**:
```
[PHASE-1] test: add test for /api/next endpoint
[PHASE-1] feat: implement random video selection
[PHASE-2] refactor: extract limit logic to service layer
[PHASE-3] docs: update API endpoint documentation
```

---

## Repository Structure

```
bobavision/
├── CLAUDE.md                 ← You are here
├── README.md                 ← User-facing documentation
├── .gitignore
│
├── docs/
│   ├── grand_plan.md         ← Master plan and progress tracking
│   ├── tdd_guide.md          ← TDD principles and workflow
│   ├── api_reference.md      ← API documentation (created in Phase 3)
│   ├── architecture.md       ← Architecture decisions (created in Phase 5)
│   └── hardware_setup.md     ← Hardware assembly guide (created in Phase 4)
│
├── server/                   ← FastAPI backend
│   ├── CLAUDE.md             ← Server development guide
│   ├── pyproject.toml        ← Python dependencies
│   ├── pytest.ini            ← Test configuration
│   ├── src/
│   │   ├── main.py           ← FastAPI app entry point
│   │   ├── api/              ← API routes
│   │   ├── db/               ← Database models and repositories
│   │   ├── services/         ← Business logic
│   │   └── media/            ← Media scanning and serving
│   └── tests/
│       ├── conftest.py       ← Shared fixtures
│       └── test_*.py         ← Test files
│
├── client/                   ← Raspberry Pi client
│   ├── CLAUDE.md             ← Client development guide
│   ├── requirements.txt      ← Python dependencies
│   ├── pytest.ini            ← Test configuration
│   ├── src/
│   │   ├── main.py           ← Client entry point
│   │   ├── button.py         ← Button handler
│   │   ├── player.py         ← mpv wrapper
│   │   └── http_client.py    ← API client
│   ├── tests/
│   │   └── test_*.py         ← Test files
│   └── bobavision.service    ← systemd service (Phase 4)
│
├── admin/                    ← React admin UI
│   ├── CLAUDE.md             ← Frontend development guide
│   ├── package.json          ← Node dependencies
│   ├── vite.config.ts        ← Vite configuration
│   ├── tsconfig.json         ← TypeScript configuration
│   ├── src/
│   │   ├── main.tsx          ← App entry point
│   │   ├── pages/            ← Page components
│   │   ├── components/       ← Reusable components
│   │   └── services/         ← API client
│   └── tests/
│       └── *.test.tsx        ← Component tests
│
└── media/                    ← Media files (not in git)
    ├── library/              ← Video files
    └── placeholders/         ← Placeholder videos
```

---

## Key Principles

### 1. TDD First, Always

Never write production code without a failing test first. See `docs/tdd_guide.md` for details.

### 2. Single Responsibility

Each module, class, and function should have one clear purpose.

### 3. Simple Over Clever

Readable code beats clever code. You should understand this in 6 months with no docs.

### 4. Fail Safe

When things go wrong, the system should fail in a way that's safe for kids:
- Server down? Show "can't connect" message, not random content
- No placeholder video? Log error and show nothing, not crash
- Invalid request? Return error response, not 500

### 5. No Surprises for Parents

The system should do exactly what parents expect:
- Limit of 3 means 3, not "approximately 3"
- Queue order is sacred - never shuffle or auto-remove
- Stats should be accurate to the second

### 6. No UI for Kids

The child's interface is one button. Period. No hidden menus, no on-screen controls, no "clever" workarounds.

---

## Common Development Tasks

### Running Tests

```bash
# Server tests
cd server
pytest

# Client tests
cd client
pytest

# Admin tests
cd admin
npm test
```

### Running Development Servers

```bash
# Server (Phase 1+)
cd server
uvicorn src.main:app --reload --port 8000

# Admin UI (Phase 3+)
cd admin
npm run dev
```

### Adding a New Video to Library

```bash
# Copy video to library
cp /path/to/video.mp4 media/library/

# Trigger rescan (Phase 2+)
curl -X POST http://localhost:8000/api/videos/scan
```

### Checking Code Coverage

```bash
# Server
cd server
pytest --cov=src --cov-report=html

# Client
cd client
pytest --cov=src --cov-report=html

# Admin
cd admin
npm run test:coverage
```

---

## Phase Transition Checklist

Before moving from one phase to the next:

- [ ] All phase tasks are checked off in `docs/grand_plan.md`
- [ ] All tests pass
- [ ] Code coverage meets targets (server: >85%, client: >85%, admin: >70%)
- [ ] All success criteria for the phase are met
- [ ] Code is committed and pushed
- [ ] You can demonstrate the phase's functionality manually

**Do not proceed to the next phase until all checklist items are complete.**

---

## Getting Help

### Understanding the System

1. **Read the Grand Plan** - `docs/grand_plan.md` has everything
2. **Check the component's CLAUDE.md** - Specific guidance for each part
3. **Look at the tests** - Tests document expected behavior
4. **Review ADRs** - Architecture Decision Records explain why things are the way they are

### Debugging

1. **Run the tests** - They'll tell you what's broken
2. **Check the logs** - Server and client should log meaningful errors
3. **Isolate the problem** - Can you reproduce it in a test?
4. **Read the error message carefully** - Python and TypeScript errors are usually helpful

### When Stuck

1. **Re-read the requirement** - Are you solving the right problem?
2. **Simplify** - Can you make a smaller test pass first?
3. **Take a break** - Sometimes the answer comes when you're not looking
4. **Document the block** - Write down what you've tried and why it didn't work

---

## Important Files to Keep in Sync

When you make changes, remember to update:

1. **docs/grand_plan.md** - Check off completed tasks, update progress percentages
2. **Component CLAUDE.md files** - Add lessons learned, update guidance
3. **Tests** - Keep tests updated as functionality changes
4. **This file (CLAUDE.md)** - Update if you change workflow or structure

---

## Testing Philosophy

From `docs/tdd_guide.md`:

> Tests are not just verification - they are documentation, specification, and design feedback.

Write tests that:
- **Describe behavior clearly** - Test names should read like sentences
- **Test one thing** - Each test has one reason to fail
- **Are independent** - Tests don't depend on each other
- **Are fast** - You'll run them hundreds of times
- **Are reliable** - No flaky tests allowed

---

## Next Steps

1. **Open docs/grand_plan.md** and find the current phase
2. **Review the tasks** for that phase
3. **Navigate to the relevant component's CLAUDE.md**:
   - Server: `server/CLAUDE.md`
   - Client: `client/CLAUDE.md`
   - Admin: `admin/CLAUDE.md`
4. **Start with the first uncompleted task**
5. **Follow the TDD cycle religiously**

---

## Branch Information

**Development Branch**: `claude/kids-media-station-01HY376SziaayAEnDmyXohud`

All commits should go to this branch. When a phase is complete, we'll create a PR to merge to main.

---

## Success Criteria Reminder

The project is done when:

- A child can press one button and watch videos
- After N videos (configurable), only placeholder plays
- Parents can queue videos from their phone's browser
- The system runs for a week without intervention
- All tests pass
- Documentation is complete

We're building something simple, robust, and delightful. Let's do this right!

---

**Ready to start? Open the Grand Plan and let's build!**
