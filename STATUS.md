# STATUS — Supertone CLI

**Last updated**: 2026-04-03
**Current milestone**: Phase 1 — SDK 래퍼 CLI

---

## Issue Summary

| 구분 | 수량 |
|------|------|
| **Total** | 15 |
| P0 (Must) | 5 |
| P1 (Should) | 8 |
| P2 (Could) | 2 |

### By Track

| Track | Issues | Est. |
|-------|--------|------|
| Foundation | ISSUE-001, 002 | 1.5d |
| Config | ISSUE-003 | 1.5d |
| Client | ISSUE-004 | 1d |
| TTS | ISSUE-005, 006, 007, 010, 013 | 5.5d |
| Voices | ISSUE-008, 009, 011 | 2d |
| Usage | ISSUE-012 | 0.5d |
| Platform | ISSUE-014, 015 | 1d |

**Total estimate**: ~13d

---

## Key Risks

| Risk | Severity | Status |
|------|----------|--------|
| SDK API surface changes | High | Mitigated by client.py wrapper |
| Streaming needs audio lib (sounddevice) | Medium | Resolved — optional extra `[stream]` |
| API beta instability | Medium | Integration tests separated |
| Test coverage for interactive/streaming | Medium | Dependency injection for mocking |

---

## Next Issues to Implement

1. **ISSUE-001** (P0) — Scaffold project with uv, pyproject.toml, and package structure
2. **ISSUE-002** (P0) — Implement error hierarchy and output formatting module
3. **ISSUE-003** (P0) — Implement config module and config commands

---

## Warnings

**Issue Validation** (76 violations, non-blocking):
- **AC format**: 65 acceptance criteria are not in strict Given/When/Then format. Content is clear and testable; format is a style preference.
- **Dependency depth**: 11 issues have chain depth > 3. This is expected — the foundation chain (scaffold → errors → config → client → commands) is 4-6 deep by design.

These are informational only and do not block implementation.

---

## Documents

| Document | Status |
|----------|--------|
| PRD | v1.1 Complete |
| Requirements | v1.0 Complete |
| UX Spec | v1.0 Complete |
| Architecture | v1.0 Complete |
| Data Model | v1.0 Complete |
| Test Plan | v1.0 Complete |
| Issues | 15 issues created |
