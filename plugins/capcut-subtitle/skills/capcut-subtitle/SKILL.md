---
name: capcut-subtitle
description: "Automatically generate timed, styled subtitles for a video and inject them into a native CapCut (Windows) draft."
triggers:
  - "자막 넣어줘"
  - "자막 만들어줘"
  - "capcut-subtitle"
  - "캡컷 자막"
---

# CapCut Auto-Subtitle (Windows)

영상 음성을 인식하거나 대본을 음성에 맞춰 정렬해 타이밍·스타일이 잡힌 자막을 네이티브 CapCut(Windows) 드래프트로 생성합니다.

두 가지 시나리오를 처리합니다:
- **대본/가사 제공 시**: Whisper 단어 타이밍과 Needleman-Wunsch 알고리즘으로 텍스트를 오디오에 정렬
- **대본 없을 시**: Whisper 전사 결과를 자막으로 바로 사용

## 준비물

1. **Python 3.8+** — [python.org](https://www.python.org) 에서 설치 (설치 시 "Add Python to PATH" 체크)
2. **ffmpeg** — [ffmpeg.org](https://ffmpeg.org/download.html) 에서 Windows 빌드 다운로드 후 PATH에 추가
   - 또는 winget: `winget install ffmpeg`
   - 또는 Chocolatey: `choco install ffmpeg`
3. **CapCut (Windows)** — 반드시 한 번 실행해 드래프트 폴더를 생성해둬야 함

## 최초 1회 셋업

Claude Code 에서:
```
capcut-subtitle 셋업 실행해줘
```

또는 터미널에서 직접:
```powershell
powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\.claude\plugins\cache\capcut-subtitle\skills\capcut-subtitle\setup.ps1"
```

약 1.5GB 모델 다운로드가 포함됩니다.

## 사용법

```
이 영상에 자막 넣어줘  C:\Users\나\Videos\내영상.mp4
```

대본이나 가사가 있으면 함께 제공하면 정확도가 올라갑니다:
```
이 영상에 자막 넣어줘  C:\Users\나\Videos\노래.mp4
(대본 붙여넣기)
```

## Claude가 실행하는 명령

### 셋업
```powershell
powershell -ExecutionPolicy Bypass -File "<skill_dir>\setup.ps1"
```

### 자막 생성
```powershell
<venv>\Scripts\python.exe "<skill_dir>\engine\subtitle.py" `
    --video "C:\절대경로\영상.mp4" `
    [--script "C:\절대경로\대본.txt"] `
    [--name "드래프트이름"]
```

venv 경로: `%USERPROFILE%\.capcut-subtitle\venv`

## 파이프라인

1. ffmpeg로 오디오 추출 (16kHz mono WAV)
2. faster-whisper로 단어 단위 타임스탬프 전사
3. 대본 정렬 또는 전사 세그먼트를 큐로 변환
4. 싱크 검증
5. SRT 생성
6. CapCut 드래프트 생성

## CapCut 드래프트 폴더 (Windows)

기본 경로:
```
%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft
```

폴더가 없으면 CapCut을 먼저 한 번 실행하세요.
경로가 다르면 `--root "C:\사용자경로"` 옵션으로 지정할 수 있습니다.

## 자주 막히는 곳

| 증상 | 해결 |
|---|---|
| "CapCut draft folder not found" | CapCut을 한 번 실행해 폴더를 만든 뒤 다시 시도 |
| 자막이 안 보임 / 드래프트가 목록에 없음 | CapCut 완전히 종료 후 재시작 |
| 특정 자막이 어긋남 | 그 시각을 알려주거나 더 정확한 모델 사용: `"large-v3 모델로 다시"` |
| ffmpeg not found | ffmpeg를 설치하고 PATH에 추가했는지 확인 |
| python not found | Python 설치 시 "Add to PATH" 체크 여부 확인 |
| 작업 충돌 방지 | 작업할 드래프트는 CapCut에서 닫아두세요 |

## 참고

- 원본 macOS 버전: https://github.com/eunssaem26/capcut-subtitle
- 완료 후 CapCut을 열어 새로 생긴 드래프트를 확인하세요 (목록에 없으면 CapCut 재시작)
