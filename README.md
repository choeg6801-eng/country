# ATLAS HUB · 글로벌 아틀라스 — 배포용 정적 사이트

빌드 과정 없이 바로 올릴 수 있는 **정적 웹사이트**예요. 서버·데이터베이스 없이 HTML·JS·이미지만으로 돌아가요.

## 폴더 구성

| 파일 | 내용 |
|---|---|
| `index.html` | 홈 (지구본 · 9개 정보 분야 · 이번 달 축제 · 인기 국가 · 대륙) |
| `countries.html` | 국가 백과 98개국 (대륙 필터 · 검색 · 비교 담기) |
| `country.html` | 국가 상세 (개요 · 여행 가이드 · 문화 · 음식 · 경제 · 꿀팁 · 뉴스, PDF 저장) |
| `compare.html` | 두 나라 비교 (PDF 저장) |
| `continent.html` | 대륙 허브 |
| `community.html` | 로컬 꿀팁 게시판 (새 글은 쓰는 사람 브라우저에만 저장) |
| `credits.html` | 사진·데이터 출처 페이지 (모든 페이지 하단에서 연결) |
| `js/data.js` | 98개국 데이터 전체 (`window.ATLAS_DB`) — 내용 수정은 여기서 |
| `js/runtime.js` | 화면을 그리고 클릭·입력을 처리하는 작은 런타임 (외부 라이브러리 없음) |
| `assets/` | 국기 SVG, 국가 사진, 지도·지구본 이미지, 공유용 이미지(`og-image.jpg`) |
| `CREDITS.md` | 사진·폰트 출처와 라이선스 |
| `DATA_CHECK_2026-10.md` | 2026년 10월 데이터 검증 보고서 (바뀐 항목과 근거 링크) |
| `scripts/`, `.github/workflows/` | 외교부 데이터 자동 업데이트 (매일 06시) — `AUTO_UPDATE_GUIDE.md` 참고 |
| `robots.txt`, `sitemap.xml` | 검색엔진용 — `YOUR-DOMAIN`을 실제 주소로 바꿔야 해요 |
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

배포 후 `robots.txt`, `sitemap.xml`의 `YOUR-DOMAIN`을 실제 주소로 바꿔 다시 올려 주세요.

## 데이터 고치는 법
- 나라 정보는 전부 `js/data.js` 한 파일에 있어요. 예: `"VN":{ ... "visa":"..." }` 부분을 찾아 고치면 모든 페이지에 반영돼요.
- 사진을 바꾸려면 `assets/`에 새 이미지를 넣고 `data.js`에서 해당 나라의 `"photo"` 경로를 바꾸세요.
- 파일은 UTF-8로 저장해야 한글이 깨지지 않아요.

## 알아둘 제한 사항
- **여행경보·비자**: 2026년 10월 19일에 검증한 값이 들어 있어요. 자동 업데이트를 켜면 외교부 데이터(`data/live.json`)가 매일 덮어써요.
- **항공권 가격·환율·날씨·뉴스**: 예시 또는 근사치예요.
- **커뮤니티 글**: 쓴 사람 브라우저에만 저장돼요. 모두가 보는 게시판은 Supabase 같은 DB 연결이 필요해요.
- **영어 버전**: 아직 없어서 KR/EN 버튼은 숨겼어요.
- **자동 업데이트는 GitHub 저장소와 연결된 배포(Netlify·Vercel·GitHub Pages)에서만** 동작해요. 폴더를 끌어다 놓는 Netlify Drop 방식은 자동 갱신이 안 돼요.
- **PDF 저장**: 브라우저에서 바로 PDF 파일을 만들어 내려받아요(글자가 이미지로 들어가서 선택·복사는 안 돼요).
