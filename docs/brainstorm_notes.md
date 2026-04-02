# Brainstorm Notes — Supertone CLI

**Date**: 2026-04-03
**Status**: Direction decided, ready for PRD

---

## Problem Space

### Who
- **주 사용자**: 콘텐츠 크리에이터 (유튜브 나레이션, 숏폼 보이스오버, 오디오북, 게임 에셋 등 다양한 유형)
- **부 사용자**: 자동화 파이프라인을 구축하는 개발자/크리에이터
- 타겟 고객 인터뷰가 아직 진행되지 않은 상태 — 특정 콘텐츠 유형에 좁히지 않고 **범용**으로 설계

### Pain Point
- 매번 Python 코드를 작성해야 TTS를 사용할 수 있음
- 기존 콘텐츠 제작 워크플로(대본 작성 → 번역 → 음성 생성 → 편집)에 Supertone을 끼워 넣기 번거로움
- 대량의 텍스트를 일괄 변환하는 간편한 방법이 없음

### Why It Matters
- 콘텐츠 크리에이터에게 TTS는 반복 작업 — CLI로 자동화하면 시간 절약이 크다
- Supertone SDK는 핵심 기능 위주로 제공 중 — CLI가 SDK의 접근성을 크게 높일 수 있음

---

## Existing Landscape

### Supertone Python SDK (`supertone`)
- **설치**: `uv add supertone` / `pip install supertone`
- **핵심 기능**: Text-to-Speech (4개 모델)
  - SONA Speech 1: en/ko/ja, 전체 음성 설정, 스트리밍 지원
  - Supertonic API 1: 5개 언어, speed만 조정
  - SONA Speech 2: 24개 언어, 대부분 설정 지원
  - SONA Speech 2 Flash: 24개 언어, 제한된 설정 (빠른 처리)
- **인증**: API 키 기반
- **출력 포맷**: WAV 등
- **CLI 기능**: 없음 (SDK만 제공)

### 경쟁/유사 도구
- ElevenLabs CLI, OpenAI TTS API — 각자의 CLI/래퍼 존재
- 범용 TTS CLI는 특정 서비스에 종속적이거나, 파이프라인 친화적이지 않은 경우가 많음

---

## Idea Candidates

### Option A: Unix 철학형 (stdin/stdout 파이프 중심)
```bash
echo "안녕하세요" | supertone tts --voice sona-1 --lang ko > output.wav
cat script.txt | llm translate --to ja | supertone tts --voice sona-1 > narration.wav
find ./scripts -name "*.txt" -exec supertone tts --input {} --outdir ./audio \;
```
- **장점**: 기존 Unix 도구들과 자연스럽게 조합, 학습곡선 낮음
- **단점**: 복잡한 워크플로는 셸 스크립트에 의존

### Option B: 워크플로 내장형 (YAML 파이프라인)
```bash
supertone pipeline run my_workflow.yaml
```
- **장점**: 복잡한 워크플로를 선언적으로 관리 가능
- **단점**: 초기 개발 비용 높음, CLI 복잡도 증가

### Option C: A 먼저, B는 나중에 (점진적 확장)
- Unix 파이프 기반으로 v1 출시 → 사용자 피드백/인터뷰 후 워크플로 기능 검토
- **장점**: 빠른 출시, 실사용 데이터 기반 의사결정
- **단점**: 없음 (점진적 접근의 일반적 이점)

---

## Decisions

| # | 결정 | 근거 |
|---|------|------|
| 1 | **Option C 채택** — Unix 파이프 기반으로 시작, 워크플로는 향후 검토 | 타겟 고객 인터뷰 전이고, SDK도 핵심 기능 위주. 빠르게 출시하고 피드백 수집 |
| 2 | **범용 설계** — 특정 콘텐츠 유형에 좁히지 않음 | 타겟 고객이 아직 확정되지 않은 상태 |
| 3 | **supertone-python SDK 기반** | 공식 SDK 활용으로 유지보수 부담 최소화 |

---

## V1 Scope Ideas (PRD에서 구체화)

### 핵심 명령어
- `supertone tts` — 텍스트를 음성으로 변환 (stdin/파일 입력, 파일/stdout 출력)
- `supertone voices` — 사용 가능한 보이스 목록 조회
- `supertone models` — 모델 목록 및 지원 기능 조회
- `supertone config` — API 키 설정 및 기본값 관리

### 파이프라인 친화 기능
- stdin 입력 지원 (`echo "text" | supertone tts`)
- stdout 출력 지원 (`supertone tts ... > output.wav`)
- 배치 처리 (디렉토리/glob 입력)
- 종료 코드 표준 준수 (0=성공, 1=에러)
- JSON 출력 모드 (`--format json`) — 다른 도구와 연동

### 사용자 편의
- 대화형 설정 (`supertone config init`)
- 프로필/프리셋 저장 (`--profile narrator`)
- 진행률 표시 (stderr, 파이프 시 자동 비활성화)

---

## Next Steps
- `/prd` 로 PRD 작성 (이 브레인스토밍 노트가 컨텍스트로 사용됨)
- 또는 `/bizanalysis` 로 비즈니스 타당성 검증
