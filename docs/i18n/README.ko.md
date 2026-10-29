# Lanshu OpenAI Media API

**에이전트를 위한 OpenAI 이미지 생성 및 음성 전사 도구. 사용량을 함께 기록합니다.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Runtime](https://img.shields.io/badge/runtime-standard_library-475569?style=flat-square)](../../README.md#requirements)
[![Documentation](https://img.shields.io/badge/docs-7_languages-0F766E?style=flat-square)](../../README.md#documentation)
[![License](https://img.shields.io/badge/license-MIT-16A34A?style=flat-square)](../../LICENSE)

[English](../../README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Français](README.fr.md) · [العربية](README.ar.md) · [Türkçe](README.tr.md)

OpenAI 이미지 생성, 파일 전사, 비용 조회 API를 호출하는 작은 Python CLI와 독립 배포용 스킬입니다. 성공한 호출의 출력 파일, 요청 ID, 사용량을 함께 저장합니다. 영어 README가 기본 문서입니다.

## 기능

- Sunburst와 Flare로 이미지를 생성하고 크기, 품질, 수량, 형식을 지정합니다.
- GPT-Transcribe로 오디오·비디오 파일을 전사하며 여러 언어 힌트와 전문 용어를 전달합니다.
- 관리자 키로 프로젝트, API 키, 모델별 비용 기록을 조회합니다.
- API 실행 결과를 JSON으로 출력하여 다른 에이전트나 스크립트와 연결합니다.

## 선별 모델

| 작업 | 모델 | 선택 |
| --- | --- | --- |
| 이미지 품질 우선 | `gpt-image-2.5-sunburst` | 이미지 기본값 |
| 이미지 생성 속도 우선 | `gpt-image-2.5-flare` | 빠른 초안 |
| 오디오·비디오 파일 전사 | `gpt-transcribe` | ASR 기본값 |

모델 정보 확인일: 2026-10-29. 명시적으로 지정한 모델을 유지하며 다른 모델로 자동 전환하지 않습니다.

## 실행 요구 사항

Python 3.9 이상이 필요하며 런타임 Python 패키지는 표준 라이브러리만 사용합니다. curl, ffprobe, zsh는 선택 사항입니다. curl은 HTTP 전송에, ffprobe는 추가 오디오 형식의 길이 확인에, zsh는 기존 ~/.zshrc 내보내기 변수를 읽는 데 사용됩니다.

## 빠른 시작

프로젝트 디렉터리에서 실행합니다. 유료 API 호출 전에는 기존 로컬 환경에 일반 API 키를 설정하세요.

### 이미지 생성

```bash
python3 scripts/openai_media.py image \
  --prompt "햇살이 드는 창가에 앉은 주황색 고양이, 자연스러운 사진, 글자 없음" \
  --out output/cat.png
```

기본값은 1024×1024, medium 품질의 PNG 한 장입니다. 빠른 초안에는 --model gpt-image-2.5-flare --quality low, 세밀한 이미지에는 --quality high를 사용하세요. --prompt-file, --size, --n, --output-format도 지원합니다. --dry-run은 요청만 미리 표시합니다. 기존 출력이나 metadata가 있으면 유료 요청 전에 중단합니다.

### 음성을 텍스트로 변환

```bash
python3 scripts/openai_media.py transcribe \
  --input /absolute/path/recording.wav \
  --languages ko \
  --keyword OpenAI \
  --out output/transcript.txt
```

--languages를 반복하면 여러 예상 언어를 전달합니다. --prompt는 녹음의 배경 설명, --keyword는 관련 용어 힌트입니다. empty_transcript: true는 빈 응답을 뜻합니다. 현재 CLI는 파일 전사용이며 실시간 마이크 입력, 화자 분리, 단어별 타임스탬프는 제공하지 않습니다.

### 비용 조회

```bash
python3 scripts/openai_media.py costs \
  --date 2026-10-29 --timezone UTC \
  --project-id YOUR_PROJECT_ID \
  --key-name YOUR_KEY_NAME \
  --model gpt-image-2.5-sunburst \
  --out output/costs.json
```

날짜와 식별자를 실제 값으로 바꾸세요. 키 이름이 중복되면 --api-key-id를 사용합니다. 비용 조회에는 관리자 키가 필요합니다.

### 명령줄 도구 설치

소스 스크립트는 설치 없이 실행됩니다. 별도 명령이 필요하면 가상 환경에 설치하세요.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
lanshu-openai-media-api models
```

## 인증 정보

| 변수 | 용도 |
| --- | --- |
| `OPENAI_API_KEY` | 이미지 생성 및 전사 |
| `OPENAI_ADMIN_KEY` | 비용 조회 및 키 이름 확인 |
| `OPENAI_ADMIN_API_KEY` | 관리자 키의 호환 별칭 |

명시적인 --env-file이 해당 환경 변수보다 우선합니다. 지정하지 않으면 프로세스 환경을 읽고, 필요할 때 ~/.zshrc에서 내보낸 값을 읽습니다. --no-shell-env로 이 기능을 끌 수 있습니다. 인증 파일은 리터럴 대입만 해석하며 실행하지 않습니다. 셸 시작 출력은 버리고 키는 전용 메모리 파이프로 전달합니다.

키는 기존 로컬 환경이나 인증 파일에 보관하며 저장소, 로그, 배포 패키지에 포함하지 않습니다. 관리자 키는 비용 조회에 사용합니다.

## 다른 에이전트에서 사용

루트에는 SKILL.md, 에이전트 메타데이터, 호출 스크립트가 있습니다. 아래 명령은 독립 스킬 폴더, ZIP, 체크섬 목록을 만듭니다. 생성한 폴더를 에이전트의 skills 디렉터리에 넣으세요. Codex의 일반적인 경로는 ~/.codex/skills/입니다. 호출 이름은 $lanshu-openai-media-api이며 기존 빌드를 대체하려면 --force를 사용합니다.

```bash
python3 tools/build_skill.py --output-dir dist
```

## 출력 및 과금 범위

이미지·전사 파일과 같은 이름의 .metadata.json을 저장합니다. 요청 인수, HTTP 상태, request ID, usage, 소요 시간, 출력 경로, 응답 메타데이터를 보관하며 키와 이미지 base64는 제외합니다.

usage는 사용량입니다. Costs API의 amount는 UTC 기준 일별 합계입니다. 프로젝트, 키, 모델로 필터링해도 개별 request ID의 영수증은 아닙니다. UTC 외 시간대의 날짜는 여러 UTC 버킷과 겹칠 수 있으므로 returned_daily_buckets와 date_window_exact를 확인하세요. 기록이 없다는 이유로 무료라고 판단하지 않습니다.

POST는 자동 재시도나 모델 변경을 하지 않습니다. GET 네트워크 오류는 최대 한 번 재시도합니다. 연결이 끊기면 먼저 기존 파일과 metadata를 확인하세요.

## 개발 및 검사

프로토콜 테스트는 로컬 HTTP 서버와 합성 데이터를 사용하며 실제 키가 필요하지 않습니다. CI 대상은 Python 3.9, 3.11, 3.13입니다. Sunburst 이미지 생성과 30초 중국어 전사를 실제 API로 확인했으며, 모든 문서 언어의 인식 정확도를 검증했다는 뜻은 아닙니다.

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
python3 -B tools/check_docs.py
python3 -B tools/build_skill.py --output-dir dist
```

인수, 확인 날짜가 명시된 가격, 공식 자료는 [API 설명](../../references/api-notes.md)을 참고하세요. 동작 변경 시 영어 문서, 번역, 스킬을 함께 갱신합니다.

## 라이선스

[MIT](../../LICENSE) · Copyright © 2026 Lanshu.
