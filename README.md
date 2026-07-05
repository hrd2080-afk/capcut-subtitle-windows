# capcut-subtitle (Windows)

CapCut Windows용 자동 자막 생성 Claude Code 스킬

영상 음성을 인식하거나 대본을 음성에 맞춰 정렬해 타이밍·스타일이 잡힌 자막을 네이티브 CapCut 드래프트로 생성합니다.

원본 macOS 버전: [eunssaem26/capcut-subtitle](https://github.com/eunssaem26/capcut-subtitle)

---

## 준비물

- Python 3.8+
- ffmpeg (`winget install ffmpeg`)
- CapCut (Windows) — 최초 1회 실행해 드래프트 폴더 생성 필요

## 설치

Claude Code에서:

```
/plugin local add <이 레포 경로>
```

또는 `plugins/capcut-subtitle` 폴더를 `~/.claude/skills/capcut-subtitle`에 복사

## 셋업 (최초 1회)

```
capcut-subtitle 셋업 실행해줘
```

약 1.5GB 모델 다운로드 포함

## 사용법

```
이 영상에 자막 넣어줘  C:\Users\나\Videos\영상.mp4
```

대본/가사가 있으면 함께 제공하면 정확도가 올라갑니다.

## macOS → Windows 변경 사항

| 항목 | macOS | Windows |
|---|---|---|
| CapCut 드래프트 경로 | `~/Movies/CapCut/...` | `%LOCALAPPDATA%\CapCut\...` |
| 설치 스크립트 | `setup.sh` | `setup.ps1` |
| 폰트 경로 | AppleSDGothicNeo | 빈값 (CapCut 기본 폰트) |
| platform 필드 | `"os": "mac"` | `"os": "windows"` |

## 라이선스

MIT
