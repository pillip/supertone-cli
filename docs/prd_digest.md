# PRD Digest — Supertone CLI (Phase 1)

## Goals
1. 코드 없이 터미널에서 TTS 생성 — Supertone SDK 래핑 CLI
2. Unix 파이프 친화 (stdin/stdout, 배치, JSON) — 자동화 파이프라인 통합
3. SDK 전체 기능 노출 — TTS, 보이스 관리, 클로닝, 사용량 조회

## Target User
콘텐츠 크리에이터 (나레이션/보이스오버/오디오북 등) + 자동화 파이프라인 구축 개발자

## Must-have Features
1. `supertone tts` — 텍스트→음성 변환 (인라인/파일/stdin → 파일/stdout)
2. `supertone tts predict` — 음성 길이 예측 (크레딧 무료)
3. `supertone tts` 배치 처리 — 디렉토리/glob 입력, 진행률 표시
4. `supertone voices list` — 보이스 목록 조회 (preset/custom 분리)
5. `supertone voices search` — 언어/성별/나이/용도/키워드 필터 검색
6. `supertone voices clone` — 음성 샘플로 커스텀 보이스 등록
7. `supertone usage` — API 사용량 조회
8. `supertone config` — API 키 설정, 기본값 관리 (init/set/get/list)
9. 스트리밍 TTS — `--stream`으로 실시간 오디오 재생 (sona_speech_1)
10. 전체 음성 설정 노출 — speed, pitch, pitch-variance, similarity, text-guidance, style

## Key NFRs
1. `pip install supertone-cli`로 설치, Python 3.11+
2. CLI 시작 시간 < 500ms
3. API 키 파일 퍼미션 600, 환경변수 `SUPERTONE_API_KEY` 지원
4. pytest 기반 테스트, 커버리지 > 80%

## Scope Boundaries
**In**: TTS 생성/스트리밍, 보이스 조회/검색/클로닝, 길이 예측, 사용량 조회, 설정 관리, 파이프라인 친화 출력
**Out**: 감정 스타일 시스템, 비언어 태그, 보이스 가이딩, 대본 포맷 파서, YAML 워크플로, 프로필/프리셋, GUI/TUI
