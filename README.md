# capcut-subtitle (Windows)

**CapCut Windows용 자동 자막 생성 Claude Code 스킬**

영상을 넣으면 AI가 음성을 인식해서 자동으로 자막을 만들어 CapCut 드래프트에 바로 넣어줍니다.  
대본이나 가사가 있으면 더 정확하게 맞춰줍니다.

> 원본 macOS 버전: [eunssaem26/capcut-subtitle](https://github.com/eunssaem26/capcut-subtitle)  
> 이 레포는 Windows에서 동작하도록 포팅한 버전입니다.

---

## 이게 뭔가요?

CapCut에서 영상 작업을 할 때 자막을 일일이 타이핑하고 타이밍 맞추는 게 번거롭죠.  
이 스킬은 그 과정을 자동화합니다.

1. 영상 파일 경로만 알려주면
2. AI(Whisper)가 음성을 듣고 텍스트로 변환하고
3. 타이밍까지 맞춰서
4. CapCut에서 바로 열 수 있는 드래프트로 만들어 줍니다

**Claude Code 안에서 대화로 사용합니다.**  
"이 영상에 자막 넣어줘" 라고 말하면 끝입니다.

---

## 사전 준비 (처음 한 번만)

### 1. Claude Code 설치
[claude.ai/code](https://claude.ai/code) 에서 Windows용 설치

### 2. Python 설치
[python.org/downloads](https://www.python.org/downloads/) 에서 최신 버전 다운로드 후 설치  
⚠️ 설치 화면에서 **"Add Python to PATH"** 반드시 체크!

![Python PATH 체크 예시](https://docs.python.org/3/_images/win_installer.png)

### 3. ffmpeg 설치
Windows 터미널(PowerShell)을 열고 아래 명령어 실행:
```
winget install ffmpeg
```
설치 후 터미널을 껐다가 다시 여세요.

> winget이 없다면 [ffmpeg.org](https://ffmpeg.org/download.html) 에서 Windows 빌드를 직접 다운로드 후 PATH에 추가하세요.

### 4. CapCut 설치 및 최초 실행
[capcut.com](https://www.capcut.com) 에서 Windows용 설치 후 **한 번 실행했다가 종료**하세요.  
(드래프트 폴더가 자동 생성됩니다)

---

## 설치 방법

**처음 설치하는 경우** — Claude Code 안에서 아래 명령어를 실행하세요:

```
/plugin marketplace add hrd2080-afk/capcut-subtitle-windows
/plugin install capcut-subtitle@capcut-subtitle-windows
```

**이미 마켓플레이스를 추가한 적이 있다면**, 새 버전을 받으려면:

```
/plugin marketplace update
/plugin install capcut-subtitle@capcut-subtitle-windows
```

---

## 셋업 (최초 1회)

Claude Code를 열고 아래와 같이 입력하세요:

```
capcut-subtitle 셋업 실행해줘
```

그러면 자동으로:
- Python 가상환경 생성
- 필요한 라이브러리 설치
- AI 음성인식 모델 다운로드 (약 1.5GB, 시간이 좀 걸립니다)

완료 메시지가 뜨면 끝!

---

## 사용법

### 기본 (대본 없이 자동 인식)
Claude Code에서:
```
이 영상에 자막 넣어줘  C:\Users\내계정명\Videos\영상파일.mp4
```

### 대본/가사가 있을 때 (더 정확)
```
이 영상에 자막 넣어줘  C:\Users\내계정명\Videos\영상파일.mp4

[대본 또는 가사를 여기에 붙여넣기]
```

### 완료 후
1. CapCut을 열면 새 드래프트가 목록에 생성되어 있습니다
2. 목록에 안 보이면 CapCut을 완전히 종료 후 재시작하세요
3. 드래프트를 열면 자막이 자동으로 타임라인에 배치되어 있습니다

---

## 옵션

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `--model large-v3` | 더 정확한 모델 (느림, 약 3GB) | `medium` |
| `--lang en` | 영어 영상 | `ko` (한국어) |
| `--name "드래프트이름"` | CapCut에 표시될 이름 | 영상 파일명 |

예시:
```
"이 영상 자막 large-v3 모델로 정확하게 넣어줘  C:\영상.mp4"
```

---

## 자주 묻는 질문

**Q. "CapCut draft folder not found" 오류가 떠요**  
A. CapCut을 한 번도 실행한 적 없는 경우입니다. CapCut을 실행했다가 종료한 후 다시 시도하세요.

**Q. 자막이 CapCut 목록에 안 보여요**  
A. CapCut을 완전히 종료 후 재시작하면 나타납니다.

**Q. 특정 구간 자막이 어긋나요**  
A. 어긋나는 시간대를 알려주거나 더 정확한 모델을 사용하세요:
```
"large-v3 모델로 다시 해줘"
```

**Q. ffmpeg를 찾을 수 없다고 해요**  
A. 터미널을 껐다 켠 후 다시 시도하세요. 그래도 안 되면 ffmpeg 설치를 다시 확인하세요.

**Q. 처음 셋업이 너무 오래 걸려요**  
A. 1.5GB 모델을 다운로드하기 때문입니다. 인터넷 속도에 따라 5~20분 걸릴 수 있습니다. 한 번만 하면 됩니다.

---

## 어떻게 동작하나요?

```
영상 파일
    ↓
ffmpeg로 오디오 추출 (WAV)
    ↓
Whisper AI로 음성 인식 + 단어별 타이밍 추출
    ↓
대본이 있으면 → 대본과 음성 타이밍 정렬
대본이 없으면 → 인식 결과 그대로 사용
    ↓
자막 싱크 품질 검증
    ↓
SRT 파일 생성
    ↓
CapCut 드래프트 폴더에 저장
    ↓
CapCut에서 바로 열림!
```

---

## 라이선스

MIT — 자유롭게 사용, 수정, 배포 가능합니다.
