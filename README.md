# capcut-subtitle (Windows)

**CapCut Windows용 자동 자막 생성 Claude Code 스킬**

영상을 넣으면 AI가 음성을 인식해서 자동으로 자막을 만들어 CapCut 드래프트에 바로 넣어줍니다.  
대본이나 가사가 있으면 더 정확하게 맞춰줍니다.

> 원본 macOS 버전: [eunssaem26/capcut-subtitle](https://github.com/eunssaem26/capcut-subtitle)  
> 이 레포는 Windows에서 동작하도록 포팅한 버전입니다.

---

## 이게 뭔가요?

CapCut에서 자막을 일일이 타이핑하고 타이밍 맞추는 게 번거롭죠.  
이 스킬은 그 과정을 자동화합니다.

1. 영상 파일 경로만 알려주면
2. AI(Whisper)가 음성을 듣고 텍스트로 변환하고
3. 타이밍까지 맞춰서
4. CapCut에서 바로 열 수 있는 드래프트로 만들어 줍니다

**Claude Code 안에서 대화로 사용합니다.**  
"이 영상에 자막 넣어줘" 라고 말하면 끝입니다.

---

## 전체 흐름 요약

```
사전 준비: Claude Code + CapCut + Python + ffmpeg 설치
       ↓
Claude Code에서 플러그인 설치 (1회)
       ↓
"capcut-subtitle 셋업 실행해줘" (1회, 모델 다운로드 포함)
       ↓
"이 영상에 자막 넣어줘 C:\경로\영상.mp4"
       ↓
CapCut 열면 자막 완성된 드래프트가 생겨 있음
```

---

## STEP 1 — 사전 준비 (처음 한 번만)

아래 4가지가 없으면 작동하지 않습니다. 순서대로 설치하세요.

### 1. Claude Code 설치

[claude.ai/code](https://claude.ai/code) 에서 Windows용 앱을 받아 설치하세요.

### 2. CapCut (Windows) 설치

[capcut.com](https://www.capcut.com) 에서 Windows 버전 설치 후 **한 번 실행했다가 종료**하세요.  
(한 번 실행해야 드래프트 폴더가 자동으로 생성됩니다.)

### 3. Python 3 설치

[python.org/downloads](https://www.python.org/downloads/) 에서 최신 버전을 받아 설치하세요.

> ⚠️ **중요:** 설치 화면 맨 아래 **"Add Python to PATH"** 체크박스를 반드시 체크하세요.

![Python PATH 체크 예시](https://docs.python.org/3/_images/win_installer.png)

설치 확인 — Windows 터미널(PowerShell)에서:
```
python --version
```
`Python 3.x.x` 라고 나오면 OK.

### 4. ffmpeg 설치

Windows 터미널(PowerShell)에서 아래 명령어 한 줄 실행:
```
winget install ffmpeg
```
설치 후 **터미널을 껐다가 다시 여세요.**

> winget이 없다면 [ffmpeg.org](https://ffmpeg.org/download.html) 에서 Windows 빌드를 직접 다운로드 후 PATH에 추가하세요.

설치 확인:
```
ffmpeg -version
```
버전 정보가 나오면 OK.

---

## STEP 2 — 플러그인 설치

### 방법 1: ZIP 다운로드 (권장 — git 없어도 됨)

1. 이 페이지 상단 초록색 **`Code`** 버튼 클릭 → **`Download ZIP`** 클릭
2. 다운로드된 ZIP 파일 압축 해제
3. 압축 해제된 폴더 안에서 아래 경로의 폴더를 찾으세요:
   ```
   capcut-subtitle-windows-main\plugins\capcut-subtitle\skills\capcut-subtitle
   ```
4. 위 `capcut-subtitle` 폴더를 아래 위치에 복사하세요:
   ```
   C:\Users\내계정명\.claude\skills\capcut-subtitle
   ```
   > `내계정명` 은 본인 Windows 사용자 이름으로 바꾸세요.  
   > 예: `C:\Users\홍길동\.claude\skills\capcut-subtitle`

5. `.claude\skills` 폴더가 없으면 직접 만드세요.

### 방법 2: git clone (git이 설치된 경우)

Windows 터미널에서:
```
git clone https://github.com/hrd2080-afk/capcut-subtitle-windows.git
```
클론 후 아래 폴더를 복사:
- **원본:** `capcut-subtitle-windows\plugins\capcut-subtitle\skills\capcut-subtitle`
- **붙여넣을 곳:** `C:\Users\내계정명\.claude\skills\capcut-subtitle`

### 방법 3: Claude Code 마켓플레이스 (SSH 설정이 된 경우)

SSH 오류가 뜨면 먼저 터미널에서 아래를 실행해 GitHub를 신뢰 목록에 추가하세요:
```
git config --global url."https://github.com/".insteadOf "git@github.com:"
```
그 다음 Claude Code에서:
```
/plugin marketplace add hrd2080-afk/capcut-subtitle-windows
/plugin install capcut-subtitle@capcut-subtitle-windows
```

---

## STEP 3 — 셋업 (최초 1회)

Claude Code를 열고 아래처럼 입력하세요:

```
capcut-subtitle 셋업 실행해줘
```

그러면 자동으로:
- Python 가상환경 생성
- 필요한 라이브러리 설치
- AI 음성인식 모델 다운로드 **(약 1.5GB — 인터넷 속도에 따라 5~20분 소요)**

완료 메시지가 뜨면 끝! 다음부터는 안 해도 됩니다.

---

## STEP 4 — 사용법

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

### 완료 후 CapCut에서 확인하는 법
1. CapCut을 열면 새 드래프트가 목록에 생성되어 있습니다
2. 목록에 안 보이면 → CapCut을 완전히 종료 후 재시작하세요
3. 드래프트를 열면 자막이 자동으로 타임라인에 배치되어 있습니다

---

## 고급 옵션

| 원하는 것 | Claude Code에 이렇게 말하기 |
|---|---|
| 더 정확한 자막 (느림, 약 3GB) | `"large-v3 모델로 자막 넣어줘 C:\영상.mp4"` |
| 영어 영상 처리 | `"영어 영상이야 자막 넣어줘 C:\영상.mp4"` |
| CapCut 드래프트 이름 지정 | `"드래프트 이름 '내영상'으로 자막 넣어줘 C:\영상.mp4"` |

---

## 오류 해결

| 오류 / 증상 | 해결법 |
|---|---|
| `CapCut draft folder not found` | CapCut을 한 번 실행 후 종료하고 다시 시도 |
| `ffmpeg를 찾을 수 없음` | 터미널 껐다 켜기. 그래도 안 되면 ffmpeg 재설치 |
| 자막이 CapCut 목록에 안 보임 | CapCut 완전 종료 후 재시작 |
| 특정 구간 자막이 어긋남 | `"large-v3 모델로 다시 해줘"` 라고 입력 |
| 셋업이 너무 오래 걸림 | 정상입니다 — 1.5GB 다운로드 중. 한 번만 하면 됩니다 |
| `python --version` 이 안 먹힘 | Python 재설치 시 "Add Python to PATH" 체크 확인 |

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
