# ATLAS HUB · 글로벌 아틀라스 — 배포용 정적 사이트

빌드 과정 없이 바로 올릴 수 있는 **정적 웹사이트**예요. 화면은 HTML·JS·이미지만으로 돌아가고, 로컬 꿀팁 게시판만 Supabase(무료 DB)에 연결돼 있어요.

## 폴더 구성

| 파일 | 내용 |
|---|---|
| `index.html` | 홈 (지구본 · 9개 정보 분야 · 이번 달 축제 · 인기 국가 · 대륙) |
| `countries.html` | 국가 백과 98개국 (대륙 필터 · 검색 · 비교 담기) |
| `country.html` | 국가 상세 (개요 · 여행 가이드 · 문화 · 음식 · 경제 · 출장·비즈니스 · 꿀팁 · 뉴스, PDF 저장) |
| `country/xx.html` | 나라별 개별 페이지 98개 (예: `country/vn.html`) — 검색 노출·공유용 주소 |
| `compare.html` | 두 나라 비교 (PDF 저장) |
| `continent.html` | 대륙 허브 |
| `community.html` | 로컬 꿀팁 게시판 — 모두에게 공개되는 공유 게시판 (Supabase, 신고 3회 시 자동 숨김) |
| `credits.html` | 사진·데이터 출처 페이지 (모든 페이지 하단에서 연결) |
| `js/data.js` | 98개국 데이터 전체 (`window.ATLAS_DB`) — 내용 수정은 여기서 |
| `js/runtime.js` | 화면을 그리고 클릭·입력을 처리하는 작은 런타임 (외부 라이브러리 없음) |
| `js/community.js` | 공유 게시판 연결 (글 읽기·쓰기·신고) |
| `photos/` | 국가 대표 사진 98장 — 전부 Wikimedia Commons 실사진 (작가·라이선스는 `CREDITS.md`) |
| `flags/` | 국기 98개 (SVG) |
| `etc/` | 지도 이미지, 공유용 이미지(`og-image.jpg`) |
| `data/live.json` | 외교부 자동 업데이트 결과 (인증키를 넣기 전엔 빈 값) |
| `data/fx.json` | 환율 — 매일 자동 갱신 (키 필요 없음) |
| `CREDITS.md` | 사진·폰트 출처와 라이선스 |
| `DATA_CHECK_2026-10.md` | 2026년 10월 데이터 검증 보고서 (바뀐 항목과 근거 링크) |
| `scripts/`, `.github/workflows/` | 매일 06시 자동 업데이트 — 환율(바로 동작), 외교부 여행경보·입국정보(인증키 등록 후 동작). `AUTO_UPDATE_GUIDE.md` 참고 |
| `robots.txt`, `sitemap.xml` | 검색엔진용 — 주소는 `country-three-zeta.vercel.app`로 채워 뒀어요 (도메인을 바꾸면 `gen`에서 다시 만들기) |
| `404.html` | 없는 주소로 들어왔을 때 보이는 페이지 |

## 내 컴퓨터에서 미리 보기

`index.html`을 더블클릭해도 대부분 보이지만, 정확하게 확인하려면 폴더에서 간단한 서버를 띄우세요.

```
cd atlas-hub-site
python3 -m http.server 8000
```
브라우저에서 `http://localhost:8000` 접속.

## 배포 방법 (셋 중 하나)

### A. Netlify Drop — 가장 쉬움 (회원가입 후 1분)
1. https://app.netlify.com/drop 접속 → 로그인
2. 압축을 푼 `atlas-hub-site` **폴더 통째로** 화면에 끌어다 놓기
3. 몇 초 뒤 `https://무작위이름.netlify.app` 주소가 생겨요 → Site settings에서 이름 변경 가능

### B. Vercel
1. GitHub에 이 폴더를 새 저장소로 올리기
2. https://vercel.com → Add New → Project → 저장소 선택
3. Framework Preset은 **Other**, Build Command 비우기, Output Directory는 `./` → Deploy

### C. GitHub Pages
1. GitHub에 저장소 만들고 이 폴더 내용을 루트에 올리기
2. 저장소 Settings → Pages → Branch를 `main` / `(root)`로 지정 → Save
3. `https://아이디.github.io/저장소이름/` 으로 열려요


## GitHub 웹사이트에서 올릴 때 (파일 수 제한)
GitHub 웹 업로드는 **한 번에 100개 파일**까지만 돼요. 폴더별로 나눠 올리면 돼요.
1. **Add file → Upload files** → `photos`, `flags`, `etc`, `.github`를 뺀 나머지 전부(html·md 파일, `js`, `data`, `scripts` 폴더 등)를 끌어다 놓고 Commit
2. 다시 **Upload files** → `photos` 폴더 → Commit (98개)
3. 같은 방법으로 `flags` 폴더(98개), `etc` 폴더(3개)
4. 숨김 폴더 `.github`는 **Add file → Create new file** → 이름 칸에 `.github/workflows/update-live.yml` → 내용 붙여넣기 → Commit
- `photos`, `flags`, `etc`는 저장소 **맨 위(루트)**에 있어야 해요.

`country` 폴더(98개)는 따로 한 번 더 올리면 돼요. 한 번에 100개까지라 폴더 하나는 한 번에 올라가요.

## 데이터 고치는 법
- 나라 정보는 전부 `js/data.js` 한 파일에 있어요. 예: `"VN":{ ... "visa":"..." }` 부분을 찾아 고치면 모든 페이지에 반영돼요.
- 사진을 바꾸려면 `photos/`에 새 이미지를 넣고 `data.js`에서 해당 나라의 `"photo"` 경로와 `"credit"`(작가·라이선스)을 바꾸세요.
- 파일은 UTF-8로 저장해야 한글이 깨지지 않아요.

## 알아둘 제한 사항
- **여행경보·비자**: 2026년 10월 19일에 검증한 값이 들어 있어요. 자동 업데이트를 켜면 외교부 데이터(`data/live.json`)가 매일 덮어써요.
- **환율**: GitHub Actions가 매일 `data/fx.json`을 갱신해요(Rates By Exchange Rate API). 화면에 기준일이 함께 보여요. **1인당 GDP**: World Bank(대만은 IMF) 2026-10 조회값이에요.
- **항공권 가격**: 근사치예요. **수도 기온**은 Open-Meteo 과거 기상 자료(2016~2025년) 월 평균, **현지 시각**은 나라별 시간대로 서머타임까지 자동 계산해요. **뉴스**는 구글 뉴스 검색으로 연결돼서 항상 최신 기사가 떠요.
- **커뮤니티 글**: Supabase에 저장돼 모두에게 공개돼요. 링크·연락처·욕설은 등록이 막히고, 같은 사람은 10분에 5개까지, 신고 3회면 자동으로 숨겨져요. DB 연결이 안 되면 글은 그 브라우저에만 임시 저장돼요.
- **영어 버전**: 아직 없어서 KR/EN 버튼은 숨겼어요.
- **자동 업데이트는 GitHub 저장소와 연결된 배포(Netlify·Vercel·GitHub Pages)에서만** 동작해요. 폴더를 끌어다 놓는 Netlify Drop 방식은 자동 갱신이 안 돼요.
- **PDF 저장**: 브라우저에서 바로 PDF 파일을 만들어 내려받아요(글자가 이미지로 들어가서 선택·복사는 안 돼요).
