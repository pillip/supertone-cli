# Business Analysis — Supertone CLI

**Date**: 2026-04-03
**Status**: Analyzed

---

## Executive Summary

콘텐츠 크리에이터를 위한 Supertone TTS CLI 도구. Supertone Python SDK를 기반으로 Unix 파이프 친화적인 인터페이스를 제공하고, Phase 2에서 감정 연출 자동화 기능으로 "AI 성우 연출 도구"로 확장. **Go** — 단, Phase 1은 SDK 래퍼로 빠르게 출시하고, Phase 2 특화 기능은 API 자체 구현이 필요하므로 개발 투자 대비 차별화 가치를 검증한 후 진행.

---

## Market Analysis

### TTS 시장 규모
- **2025**: $38.7억 → **2031**: $79.2억 (CAGR 12.66%)
- Neural/AI 기반 음성: 시장의 67%, CAGR 15.08%로 가장 빠른 성장
- 아시아태평양: CAGR 14.86%로 가장 빠르게 성장하는 지역
- 출처: [Mordor Intelligence](https://www.mordorintelligence.com/industry-reports/text-to-speech-market)

### TAM / SAM / SOM (추정)

| 구분 | 범위 | 추정 규모 |
|------|------|-----------|
| **TAM** | 글로벌 TTS 시장 전체 | $38.7억 (2025) |
| **SAM** | 콘텐츠 크리에이터/미디어 엔터테인먼트 TTS 수요 | ~$3-5억 (시장의 ~10%) |
| **SOM** | Supertone을 사용하는 한/영/일 콘텐츠 크리에이터 중 CLI를 채택하는 비율 | 초기 수천 명 규모 (rough estimate) |

> SOM은 Supertone의 기존 사용자 기반과 CLI 채택률에 크게 의존. 정확한 수치는 Supertone 사용자 데이터 확인 필요.

### 주요 트렌드
- 콘텐츠 크리에이터의 AI 도구 채택 가속화
- "코드로서의 콘텐츠" — 자동화 파이프라인 구축 수요 증가
- K-콘텐츠 글로벌 확산으로 다국어 음성 수요 증가

---

## Competitive Landscape

### 직접 경쟁자: TTS CLI 도구

| 항목 | ElevenLabs 커뮤니티 CLI | Supertone CLI (계획) |
|------|------------------------|---------------------|
| **보이스** | 5,000+ | 200+ (Phase 1), 확장 예정 |
| **언어** | 70+ | 23 (SONA Speech 2) |
| **기능 범위** | TTS, STT, 더빙, SFX, 음성복제, MCP 서버 | Phase 1: TTS 핵심 / Phase 2: 감정 연출 |
| **파이프라인 친화** | `--json` 출력, 파이프 호환 | stdin/stdout, 배치 처리 |
| **감정 제어** | 제한적 | Phase 2에서 핵심 차별점 |
| **한국어 품질** | 범용 | 특화 (HYBE 백업) |
| **성숙도** | 높음 | 신규 |

출처: [ElevenLabs CLI](https://github.com/hongkongkiwi/elevenlabs-cli), [ElevenLabs 공식 CLI](https://elevenlabs.io/docs/eleven-agents/operate/cli)

### 간접 경쟁자
- **OpenAI TTS API** — 고품질이나 공식 CLI 없음
- **macOS `say` 명령** — 무료지만 품질 제한
- **Coqui TTS 등 오픈소스** — 커스터마이징 가능하나 품질/편의성 트레이드오프

### 차별화 전략

ElevenLabs CLI와 **기능 수로 경쟁하지 않는다.** 대신:

1. **Phase 1**: Supertone 사용자에게 최고의 CLI 경험 제공 (이건 경쟁이 아니라 자사 생태계 강화)
2. **Phase 2**: "AI 성우 연출 도구"로 포지셔닝 — 감정 스타일, 비언어 태그, 보이스 가이딩, 대본 기반 배치 처리. 이 영역에서는 ElevenLabs CLI도 제공하지 않는 워크플로

---

## Business Model

### Phase 1 — SDK 래퍼 (수익 모델 불필요)
- CLI 자체는 **오픈소스 무료 도구**
- 수익은 Supertone API 사용료를 통해 간접 발생
- 목적: Supertone 생태계 확장, 사용자 락인, 개발자 경험 향상

### Phase 2 — 특화 기능 추가 시 옵션
- **Option A**: 계속 오픈소스 + API 사용료 모델 유지
- **Option B**: CLI Pro (감정 프리셋 라이브러리, 고급 배치 기능 등) 유료화
- **Option C**: Supertone 공식 도구로 편입

> Phase 1 사용자 데이터를 보고 결정. 현 단계에서 수익 모델 확정은 시기상조.

### 가격 참고
- Supertone API: $0.10/분 (베타) — [Supertone API](https://www.supertone.ai/en/api)
- ElevenLabs: 월 $5~ (Starter) — [ElevenLabs Pricing](https://elevenlabs.io/pricing)

---

## Risks & Mitigations

| # | 리스크 | 심각도 | 완화 전략 |
|---|--------|--------|-----------|
| 1 | **SDK 기능 제한** — 현재 SDK는 TTS 핵심만 제공. 감정 스타일, 보이스 가이딩 등은 SDK에 없음 | 높음 | Phase 2 특화 기능은 API를 직접 구현하여 해결. SDK 의존도를 낮추고 자체 API 레이어 구축 |
| 2 | **Supertone API 변경/중단** | 중간 | SDK 버전 핀닝, API 변경 모니터링, 추상화 레이어로 격리 |
| 3 | **사용자 기반 부족** — Supertone 사용자 자체가 ElevenLabs 대비 작음 | 중간 | Phase 1을 빠르게 출시하여 "Supertone을 쓰는 이유"를 CLI가 강화. K-콘텐츠/한국어 특화로 틈새 확보 |
| 4 | **ElevenLabs CLI가 감정 연출 기능 추가** | 낮음 | 선점 효과 + Supertone 음성 품질 차별화. CLI는 결국 뒤의 모델 품질에 의존 |
| 5 | **Phase 2 개발 비용** — 감정 스타일 등 API 자체 구현은 상당한 투자 필요 | 중간 | Phase 1 사용자 피드백으로 수요 검증 후 투자. MVP → 검증 → 확장 사이클 유지 |

---

## SWOT Analysis

### Strengths
- Supertone의 한/영/일 음성 품질 (특히 한국어)
- HYBE 에코시스템과의 연결 (K-콘텐츠 산업)
- SONA Speech 2의 23개 언어 + 크로스링구얼 음성 일관성
- API 직접 구현 가능 — SDK 제한에 묶이지 않음

### Weaknesses
- 현재 SDK 기능이 제한적 (감정 스타일 등 미노출)
- ElevenLabs 대비 보이스/언어 수 열세
- CLI 생태계 제로에서 시작
- Phase 2 특화 기능은 자체 개발 필요 (시간/비용)

### Opportunities
- K-콘텐츠 글로벌 확산 → 한국어 TTS 수요 증가
- "AI 성우 연출 도구"는 아직 경쟁자가 없는 포지션
- 콘텐츠 제작 자동화 트렌드
- Supertone이 감정 스타일 API를 공식 오픈하면 Phase 2 개발 비용 크게 감소

### Threats
- ElevenLabs의 압도적 시장 점유 및 기능 확장 속도
- Supertone API 베타 단계의 불안정성
- 대형 플랫폼(Google, AWS, OpenAI)의 TTS 품질 빠른 개선

---

## Go / Pivot / No-Go

### **Go** (조건부)

**근거:**
1. Phase 1은 저비용/저위험 — SDK 래퍼이므로 빠르게 출시 가능
2. Phase 2 "AI 성우 연출 도구"는 시장에 없는 포지션이며, API 직접 구현으로 실현 가능
3. K-콘텐츠/한국어 특화 틈새는 ElevenLabs가 쉽게 공략하기 어려운 영역

**조건:**
- Phase 1 출시 후 **실사용 데이터**로 Phase 2 투자 여부 결정
- Phase 2 진입 전 타겟 고객 인터뷰 완료 필요
- Supertone API의 안정성/지속성 확인

---

## Next Steps
- `/prd` 로 PRD 작성 (brainstorm_notes + business_analysis가 컨텍스트로 사용됨)
