---
description: "Task list for AI Slide Generator implementation"
status: "Phase 3 Complete - 75% Done"
last_updated: "2026-02-01"
---

# Tasks: AI Slide Generator

**Input**: Design documents from `/specs/001-ai-slide-generator/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are OPTIONAL but recommended for critical logic.

**Organization**: Tasks are grouped by phase, with explicit parallel tracks for Frontend (FE) and Backend (BE).

---

## 📊 Progress Summary

| Phase | Status | Completion | Tasks |
|-------|--------|------------|-------|
| Phase 1: Setup & Foundation | ✅ Complete | 100% (7/7) | T001-T007 |
| Phase 2: Style Initialization | ✅ Complete | 100% (5/5) | T008-T012 |
| Phase 3: Slide Management | ✅ Complete | 100% (7/7) | T013-T019 |
| Phase 4: Fullscreen Playback | ⏳ Pending | 0% (0/4) | T020-T023 |
| Phase 5: Polish & Edge Cases | 🎯 Mostly Done | 80% (4/5) | T024-T028 |
| **Total** | **75% Complete** | **23/28** | **All Tasks** |

**Current Status**: 
- ✅ Core functionality complete (Phases 1-3)
- ✅ UI/UX polished (Tailwind CSS, Toast notifications, loading states)
- ✅ Error handling and data integrity implemented
- ⏳ Carousel component remaining (Phase 4)

**Next Steps**: Implement Phase 4 Carousel component for fullscreen presentation mode.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `Week7/backend/`
- **Frontend**: `Week7/frontend/`

---

## Phase 1: Setup & Foundation (Setup + Core)

**Purpose**: Initialize projects, configure environments, and establish the shared data contract (`outline.yml`).

**⚠️ CRITICAL**: Both FE and BE foundations must be ready before parallel story work.

- [X] T001 Create project directories `Week7/backend` and `Week7/frontend`
- [X] T002 [P] Initialize **Backend** (FastAPI) in `Week7/backend`: uv venv, requirements.txt, basic app structure
- [X] T003 [P] Initialize **Frontend** (Vite+React+TS) in `Week7/frontend`: tailwind, axios, dnd-kit
- [X] T004 [P] Create `Week7/outline.yml` handling logic in `Week7/backend/app/data/yaml_store.py` (CRUD operations)
- [X] T005 [P] Create shared type definitions (ProjectState, Slide) in `Week7/frontend/src/types/index.ts` matching Pydantic models
- [X] T006 [P] Implement `google.genai` wrapper in `Week7/backend/app/core/generator.py` (Stubbed or real)
- [X] T007 [P] Configure CORS and Env vars (`GEMINI_API_KEY`) in `Week7/backend/app/core/config.py` and `Week7/backend/app/main.py`

**Checkpoint**: Backend running at localhost:8000/docs, Frontend running at localhost:5173. `outline.yml` read/write works.

---

## Phase 2: Style Initialization (User Story 1 - P1)

**Goal**: Establish visual style (First-run experience).

**Independent Test**: Clear `outline.yml`, open app -> Popup -> Generate 2 images -> Select one -> Saved to file.

### Backend Track (BE)
- [X] T008 [P] [US1] Implement POST `/style/init` endpoint in `Week7/backend/app/api/endpoints.py` (Generate candidates)
- [X] T009 [P] [US1] Implement POST `/style/select` endpoint in `Week7/backend/app/api/endpoints.py` (Save style to outline.yml)

### Frontend Track (FE)
- [X] T010 [P] [US1] Create `StyleInitializer` component in `Week7/frontend/src/components/StyleInitializer.tsx` (Modal UI)
- [X] T011 [P] [US1] Integrate API calls in `Week7/frontend/src/api/client.ts` for style endpoints
- [X] T012 [P] [US1] Wire up `App.tsx` to check `ProjectState.style_reference` and show Modal if missing

**Checkpoint**: User can launch app, enter prompt, see 2 images, select one, and it persists in `outline.yml`.

---

## Phase 3: Slide Management & Editor (User Story 2 & 3 - P2)

**Goal**: Create, Reorder, and Edit slides (Core Content Loop).

**Independent Test**: Add 3 slides, drag to reorder, edit text, regenerate image.

### Backend Track (BE)
- [X] T013 [P] [US2] Implement POST `/slides` (Create) and DELETE `/slides/{id}` endpoints in `Week7/backend/app/api/endpoints.py`
- [X] T014 [P] [US2] Implement PUT `/slides/reorder` endpoint in `Week7/backend/app/api/endpoints.py`
- [X] T015 [P] [US3] Implement PUT `/slides/{id}` (Update text) and POST `/slides/{id}/generate` (Regen image)

### Frontend Track (FE)
- [X] T016 [P] [US2] Create `Sidebar` component in `Week7/frontend/src/components/Sidebar.tsx` with `@dnd-kit`
- [X] T017 [P] [US3] Create `SlideEditor` component in `Week7/frontend/src/components/SlideEditor.tsx` (Text area + Image preview)
- [X] T018 [P] [US3] Implement logic to show "Regenerate" button when content hash differs in `SlideEditor.tsx`
- [X] T019 [P] [US2] Integrate slide CRUD and reorder APIs in `Week7/frontend/src/api/client.ts`

**Checkpoint**: Full CRUD on slides. Drag-and-drop works. Text changes trigger "Regenerate" option.

---

## Phase 4: Fullscreen Playback (User Story 4 - P1)

**Goal**: Consumption experience (Marquee).

**Independent Test**: Click Play, verification full screen, auto-advance, Esc to exit.

### Backend Track (BE)
- [ ] T020 [P] [US4] Ensure `GET /project` returns slides in correct order (already covered by T004/T014, verify only)

### Frontend Track (FE)
- [ ] T021 [P] [US4] Create `Carousel` component in `Week7/frontend/src/components/Carousel.tsx` (Fullscreen overlay)
- [ ] T022 [P] [US4] Implement auto-advance timer and Esc key listener in `Carousel.tsx`
- [ ] T023 [P] [US4] Add "Play" button to `Sidebar` or `App` header to trigger Carousel

**Checkpoint**: Presentation mode works smoothly.

---

## Phase 5: Polish & Edge Cases

**Purpose**: Error handling, UI refinement, and robustness.

- [X] T024 [P] [FE] Add Toast notifications for API errors (using `sonner` or similar) in `Week7/frontend/src/App.tsx`
- [X] T025 [P] [BE] Add error handling in `generator.py` for Gemini API quotas/timeouts
- [X] T026 [P] [FE] Add loading skeletons/spinners for image generation states
- [X] T027 [P] [BE] Verify atomic writes for `outline.yml` to prevent corruption
- [ ] T028 Run full end-to-end test flow (Init -> Add -> Edit -> Reorder -> Play)

---

## Parallel Execution Strategy

1.  **Phase 1**: Developer A sets up Backend (T002, T004, T006, T007). Developer B sets up Frontend (T003, T005).
2.  **Phase 2**: Developer A builds Backend Endpoints (T008, T009). Developer B builds Frontend UI (T010, T011, T012).
3.  **Phase 3**: Developer A builds Slide APIs (T013, T014, T015). Developer B builds Sidebar/Editor (T016, T017, T018, T019).
4.  **Phase 4**: Frontend-heavy phase. Developer B builds Carousel (T021, T022, T023). Developer A supports or moves to Phase 5 tasks.

## Dependencies

- **Phase 2 (Style)** depends on **Phase 1 (Setup)**.
- **Phase 3 (Slides)** depends on **Phase 1 (Setup)** (independent of Phase 2 logic, but needs project structure).
- **Phase 4 (Carousel)** depends on **Phase 3 (Slides)** (needs slides to display).
