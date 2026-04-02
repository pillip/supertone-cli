# Supertone CLI

Supertone Python SDK를 래핑하는 Unix 파이프 친화적 CLI 도구. 터미널에서 한 줄 명령으로 TTS를 생성하고, 기존 도구들과 자연스럽게 조합할 수 있습니다.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (패키지 관리)
- Supertone API 키 ([발급](https://www.supertone.ai/en/api))

## Setup

```bash
# 저장소 클론
git clone https://github.com/your-org/supertone-cli.git
cd supertone-cli

# 의존성 설치
uv sync

# (선택) 스트리밍 지원
uv sync --extra stream

# API 키 설정
uv run supertone config init
# 또는
export SUPERTONE_API_KEY="your-api-key"
```

## Usage

```bash
# 기본 TTS
uv run supertone tts "안녕하세요" --voice <voice-id> --output hello.wav

# 파이프라인
echo "Hello world" | uv run supertone tts --voice <voice-id> > output.wav

# 배치 처리
uv run supertone tts --input ./scripts/ --outdir ./audio/ --voice <voice-id>

# 보이스 목록
uv run supertone voices list

# 보이스 검색
uv run supertone voices search --lang ko --gender female

# 사용량 조회
uv run supertone usage
```

## Testing

```bash
# 단위 테스트 (API 호출 mock)
uv run pytest -q

# 커버리지 리포트
uv run pytest --cov=src --cov-report=term-missing

# 통합 테스트 (실제 API 호출, SUPERTONE_API_KEY 필요)
uv run pytest -m integration
```

## Project Structure

```
supertone-cli/
├── src/supertone_cli/
│   ├── cli.py            # Typer 앱 엔트리포인트
│   ├── commands/
│   │   ├── tts.py        # tts, tts predict
│   │   ├── voices.py     # voices list, search, clone
│   │   ├── usage.py      # usage
│   │   └── config_cmd.py # config init/set/get/list
│   ├── config.py         # TOML 설정 관리
│   ├── client.py         # SDK 래핑 레이어
│   ├── output.py         # 출력 포맷팅 (테이블/JSON/진행률)
│   └── errors.py         # 에러 계층 (exit codes)
├── tests/
├── pyproject.toml
└── docs/
```

## Documentation

- [PRD](../PRD.md) — 제품 요구사항
- [Requirements](requirements.md) — 상세 요구사항
- [Architecture](architecture.md) — 아키텍처 설계
- [UX Spec](ux_spec.md) — CLI UX 명세
- [Data Model](data_model.md) — 데이터 모델
- [Test Plan](test_plan.md) — 테스트 전략
