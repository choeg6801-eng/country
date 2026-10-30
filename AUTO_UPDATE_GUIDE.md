# 여행 정보 자동 업데이트 설정 가이드

매일 아침 6시(한국 시간)에 GitHub가 외교부 공공데이터를 자동으로 받아 `data/live.json` 파일을 새로 만들고, 사이트가 그 값을 보여 주도록 설정하는 방법입니다. 개발 지식이 없어도 순서대로 따라 하면 됩니다. 약 20~30분 걸립니다.

---

## 0. 준비물

- 사이트 코드가 올라가 있는 **GitHub 저장소** (Netlify / Vercel / GitHub Pages 중 하나에 연결되어 있어야 함)
- 이 폴더의 파일들을 저장소에 **같은 위치 그대로** 올립니다.

```
(저장소 최상위)
├─ .github/workflows/update-live.yml   ← 매일 자동 실행 설정
├─ scripts/update_live.py              ← 데이터를 받아 정리하는 프로그램
├─ scripts/samples/*.json              ← 테스트용 예시 응답 (지우지 마세요)
└─ data/                               ← live.json이 여기에 자동으로 생깁니다
```

> `.github` 폴더는 이름이 점(.)으로 시작해서 컴퓨터에서 숨김 폴더로 보일 수 있습니다. GitHub 웹에서 올릴 때는 **Add file → Create new file**을 누르고 파일 이름 칸에 `.github/workflows/update-live.yml`을 그대로 입력한 뒤 내용을 붙여넣으면 폴더가 함께 만들어집니다.

> `data/live.sample.json`은 테스트용 가짜 데이터입니다. 저장소에 올리지 않아도 됩니다.

---

## 1. 공공데이터포털 회원가입

1. <https://www.data.go.kr> 에 접속합니다.
2. 오른쪽 위 **회원가입**을 누르고 안내에 따라 가입합니다(간편인증 또는 휴대폰 인증).
3. 로그인합니다.

---

## 2. API 활용신청 (①·② 두 개면 충분)

검색창에 아래 **데이터명**을 하나씩 검색해서 신청합니다. 검색 결과에서 **오픈 API** 탭에 있는 항목을 고르세요(같은 이름의 "파일데이터"가 아닙니다).

| # | 정확한 데이터명 | 바로가기 | 승인 |
|---|---|---|---|
| ① | **외교부_국가∙지역별 여행경보** | <https://www.data.go.kr/data/15076237/openapi.do> | 자동승인 |
| ② | **외교부_국가·지역별 입국허가요건** | <https://www.data.go.kr/data/15075345/openapi.do> | 개발계정 자동승인 |
| ③ | **외교부_국가∙지역별 특별여행주의보** | <https://www.data.go.kr/data/15076244/openapi.do> | 자동승인 |

각 페이지에서:

1. 파란색 **활용신청** 버튼을 누릅니다.
2. **활용목적**: "웹 사이트 개발" 선택, 내용에 예) `해외여행자를 위한 국가별 여행정보 사이트에 여행경보·입국요건 표시` 정도로 적습니다.
3. **라이선스 표시** 동의에 체크 → **활용신청**.

> ③ 특별여행주의보는 **신청하지 않아도 됩니다.** 2026-10-20에 확인해 보니 기존 요청 주소가 "서비스 없음(폐기)"으로 응답해서 기본 설정에서는 꺼 두었어요. 여행경보(①)와 입국허가요건(②)만으로 사이트는 정상 동작합니다.

---

## 3. 인증키(Decoding) 복사

1. 오른쪽 위 **마이페이지 → 데이터활용 → Open API → 활용신청 현황**으로 갑니다.
2. 신청한 API 하나를 누르면 **일반 인증키(Encoding)**와 **일반 인증키(Decoding)** 두 개가 보입니다.
3. **Decoding** 키를 복사합니다. (세 API 모두 **같은 키**입니다. 한 번만 복사하면 됩니다.)

> Encoding 키(중간에 `%2B`, `%3D` 같은 글자가 섞인 것)를 넣어도 프로그램이 알아서 처리하지만, **Decoding 키를 권장**합니다.
> 키 앞뒤에 공백이 들어가지 않게 주의하세요.

---

## 4. GitHub에 인증키 등록 (Secret)

1. GitHub에서 사이트 저장소로 갑니다.
2. 위쪽 메뉴 **Settings**(톱니바퀴)를 누릅니다.
3. 왼쪽 메뉴 **Secrets and variables → Actions**를 누릅니다.
4. 초록색 **New repository secret**을 누릅니다.
5. 입력합니다.
   - **Name**: `DATA_GO_KR_KEY` (대문자, 철자 그대로)
   - **Secret**: 3단계에서 복사한 Decoding 키
6. **Add secret**을 누릅니다.

> Secret은 등록 후 다시 볼 수 없습니다. 바꾸려면 연필 아이콘(Update)을 눌러 새로 붙여넣으세요.

### (확인) Actions가 저장소에 쓸 수 있는지

**Settings → Actions → General** 맨 아래 **Workflow permissions**에서 **Read and write permissions**를 선택하고 **Save**를 누릅니다. (설정 파일에도 쓰기 권한을 적어 두었지만, 조직 저장소는 여기서 막혀 있을 수 있습니다.)

---

## 5. 수동으로 한 번 실행해 보기

1. 저장소 위쪽 **Actions** 탭을 누릅니다.
   - "Workflows aren't being run on this repository" 같은 안내가 보이면 **I understand my workflows, go ahead and enable them**을 누릅니다.
2. 왼쪽 목록에서 **Update live travel data**를 누릅니다.
3. 오른쪽 **Run workflow** → 초록 **Run workflow** 버튼을 누릅니다.
4. 몇 초 뒤 목록에 실행 기록이 생깁니다. 1~2분 후 **초록 체크(✓)**가 되면 성공입니다.
5. 실행 기록 → **update** → **Fetch MOFA open APIs → data/live.json** 단계를 펼치면 이런 줄이 보입니다.
   ```
   [alarm] ok: 300 records → 190 countries
   [visa] ok: 190 records → 185 countries
   [special] ok: 20 records → 18 countries
   wrote .../data/live.json: 195 countries (3/3 APIs ok)
   ```
   `FAILED`가 보이면 아래 **문제 해결**을 확인하세요.

이후에는 **매일 06:00(KST)**에 자동으로 실행됩니다. 따로 할 일은 없습니다.

---

## 6. live.json 생성 확인

1. 저장소 **Code** 탭 → `data` 폴더 → `live.json`을 엽니다.
2. 맨 위 `"updated"` 시간이 방금 실행한 시간인지 확인합니다.
3. `"countries"` 안에 `"VN": { "alertLevel": 1, "alert": "1단계 여행유의 (일부 지역)", "visa": "무비자 45일", ... }` 같은 내용이 있으면 정상입니다.
4. `"status"` 항목에서 API별 성공 여부(`"ok": true/false`)와 오류 메시지를 볼 수 있습니다.

> 데이터가 전날과 똑같으면 파일이 바뀌지 않으므로 커밋이 생기지 않습니다. 정상입니다.

---

## 7. 호스팅 자동 재배포

`live.json`이 커밋되면 호스팅이 알아서 다시 배포합니다.

- **Netlify / Vercel**: 저장소가 연결되어 있으면 커밋마다 자동 배포됩니다. 대시보드의 Deploys 목록에 `chore: update live travel data ...` 배포가 생겼는지 확인하세요.
- **GitHub Pages**: Settings → Pages에서 배포 브랜치(예: `main`)가 지정되어 있으면 자동입니다. Actions 탭에 `pages build and deployment`가 함께 실행됩니다.

배포 후 사이트에서 `https://내사이트주소/data/live.json`을 브라우저로 열어 새 내용이 보이면 끝입니다.

---

## 문제 해결

로그(5단계의 실행 기록)나 `live.json`의 `"status" → "error"`에 나오는 메시지로 원인을 찾습니다.

| 메시지 | 뜻 | 해결 |
|---|---|---|
| `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` | 등록되지 않은 키 | ① **발급 직후에는 1~2시간(길면 하루)** 지나야 키가 동작합니다. 기다렸다가 다시 실행하세요. ② 키를 잘못 복사했거나 앞뒤 공백이 있는지 확인하고 Secret을 다시 등록하세요. ③ 해당 API를 활용신청했는지 확인하세요. |
| `SERVICE_ACCESS_DENIED_ERROR` | 이 API에 대한 사용 권한 없음 | 그 API를 **활용신청하지 않았거나 승인 대기/중지** 상태입니다. 마이페이지 → 활용신청 현황에서 상태가 "승인"인지 확인하세요. |
| `SERVICE_KEY_IS_NULL` / `DATA_GO_KR_KEY is not set` | 키가 전달되지 않음 | Secret 이름이 정확히 `DATA_GO_KR_KEY`인지 확인하세요(오타·소문자 주의). |
| `DEADLINE_HAS_EXPIRED_ERROR` | 활용 기간 만료 | 마이페이지에서 **연장 신청**을 하세요(보통 2년). |
| `LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR` | 하루 호출량 초과 | 개발계정은 하루 10,000회입니다. 이 프로그램은 하루 몇 회만 쓰므로, 같은 키를 다른 곳에서 많이 쓰고 있지 않은지 확인하세요. 다음 날 자동으로 풀립니다. |
| `NO_OPENAPI_SERVICE_ERROR` | 주소가 없음/폐기됨 | 외교부가 API 버전을 바꾼 경우입니다. 해당 데이터 페이지의 **요청주소**를 확인해 저장소 **Settings → Secrets and variables → Actions → Variables** 탭에 `MOFA_SPECIAL_URL` 등으로 새 주소를 넣으세요(아래 참고). |
| `SERVICETIMEOUT_ERROR`, `network error`, `HTTP_ERROR` | 외교부 서버 일시 장애 | 기다리면 됩니다. 실패한 API는 **이전 값을 그대로 유지**하므로 사이트는 영향이 없습니다. 다음 날 자동으로 다시 시도합니다. |
| `XML/error response: ...` | JSON 대신 오류 문서가 옴 | 뒤에 붙은 메시지를 위 표에서 찾으세요. |
| Actions 단계에서 `Permission denied` / `403` (push 실패) | Actions에 쓰기 권한 없음 | 4단계의 **Workflow permissions → Read and write**를 켜세요. 브랜치 보호 규칙이 있으면 github-actions 푸시를 허용해야 합니다. |
| 예약 시간에 실행이 안 됨 | GitHub 정책 | 예약 실행은 몇 분~수십 분 늦을 수 있습니다. **저장소에 60일간 활동이 없으면 예약 실행이 자동으로 꺼집니다.** Actions 탭에서 다시 Enable 하세요. |

### 승인 대기 시간 정리
- 여행경보·특별여행주의보: **자동승인** — 신청 즉시 승인. 단, 키가 실제로 동작하기까지 **1~2시간 정도** 걸릴 수 있습니다.
- 입국허가요건: 개발계정 **자동승인**(운영계정은 심의승인이지만 이 사이트에는 개발계정으로 충분합니다).

### API 주소 바꾸기 (고급, 필요할 때만)
저장소 **Settings → Secrets and variables → Actions → Variables** 탭 → **New repository variable**:
- `MOFA_SPECIAL_URL` — 특별여행주의보 요청 주소. 기본값은 `off`(사용 안 함)예요. 새 주소를 찾았을 때만 넣으세요.

(여행경보·입국허가요건 주소를 바꿔야 할 때는 `.github/workflows/update-live.yml`의 `env:` 아래에 `MOFA_ALARM_URL: ${{ vars.MOFA_ALARM_URL }}`, `MOFA_VISA_URL: ${{ vars.MOFA_VISA_URL }}` 줄을 추가하고 같은 방법으로 변수를 만드세요.)

### 내 컴퓨터에서 테스트 (선택)
Python 3이 설치되어 있다면 인터넷이나 키 없이 예시 데이터로 동작을 확인할 수 있습니다.
```
python3 scripts/update_live.py --sample
```
→ `data/live.sample.json`이 만들어집니다(가짜 데이터라서 사이트용 `live.json`은 건드리지 않습니다).

---

## live.json 형식 (참고)

```json
{
  "updated": "2026-10-19T06:00:12+09:00",
  "source": "외교부 해외안전여행 · 공공데이터포털",
  "status": { "alarm": {"ok": true, "count": 190}, "visa": {"ok": true}, "special": {"ok": true} },
  "countries": {
    "VN": {
      "alertLevel": 1,
      "alert": "1단계 여행유의 (일부 지역)",
      "alertRegions": "1단계 일부: ...",
      "alertDate": "2025-03-02",
      "visa": "무비자 45일",
      "visaRaw": "45일 / 근거: ...",
      "special": "특별여행주의보 ..."
    }
  }
}
```
- 국가 키는 ISO 2자리 대문자 코드(`VN`, `JP`, `US` …)입니다.
- 값이 없는 항목은 아예 빠집니다. 사이트는 빠진 항목만 기존 내장 값을 그대로 씁니다.
- 출처 표기: 사이트 하단에 "자료: 외교부 해외안전여행 · 공공데이터포털"을 표시해 주세요(공공누리/이용허락 조건).
