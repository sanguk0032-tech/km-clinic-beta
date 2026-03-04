# Django + Next.js 로그인/네트워크/MVP 체크리스트 (설명서 버전)

아래 순서대로 한 단계씩만 확인하세요.

## 0) 실행 위치 고정
- **PowerShell 위치**: 프로젝트 루트 (`manage.py` 있는 폴더)

```powershell
cd C:\path\to\km-clinic-beta
```

---

## 1) 백엔드 서버 살아있는지 먼저 확인

### 1-1. 서버 실행
```powershell
python manage.py runserver 0.0.0.0:8000
```

### 1-2. 같은 PC에서 헬스체크
(새 PowerShell 창)
```powershell
Invoke-RestMethod -Method GET http://127.0.0.1:8000/healthz/
```
정상 예시:
```json
{"status":"ok","now":"..."}
```

### 1-3. 폰/다른 기기에서 헬스체크
- PC의 로컬 IP 확인:
```powershell
ipconfig
```
- `IPv4`가 예: `192.168.0.23`이면 폰 브라우저에서:

`http://192.168.0.23:8000/healthz/`

안 되면:
- PC 방화벽 인바운드 허용(8000)
- 폰/PC 같은 와이파이인지 확인

---

## 2) ALLOWED_HOSTS 점검 (DisallowedHost 방지)

이 프로젝트는 기본적으로 아래 호스트를 허용하도록 설정되어 있습니다.
- `127.0.0.1`
- `localhost`
- `0.0.0.0`

추가 IP/도메인이 필요하면 실행 전에 환경변수로 지정:

```powershell
$env:DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,0.0.0.0,192.168.0.23"
python manage.py runserver 0.0.0.0:8000
```

---

## 3) JWT 로그인 실패 원인 분리 진단

핵심은 **프론트 문제인지, 백엔드 인증 문제인지 분리**하는 것입니다.

### 3-1. 백엔드 JWT 엔드포인트 직접 호출
(엔드포인트 예시는 프로젝트 실제 경로에 맞게 바꿔서 테스트)

```powershell
$body = @{ username = "patient1"; password = "비밀번호" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/auth/login/" -ContentType "application/json" -Body $body
```

- 여기서 토큰(access/refresh)이 나오면: **백엔드는 정상**, 프론트 호출 URL/요청 형식 문제일 확률 큼
- 401/400이면: 계정/비번/serializer 필드명 확인 필요 (`username` vs `email`)

### 3-2. 프론트 API baseURL 점검
- Next.js 코드에서 API 주소가 `127.0.0.1`로 하드코딩이면, 폰에서는 실패합니다.
- 폰에서 접속 시에는 반드시 **PC의 LAN IP**를 써야 합니다.

권장 패턴:
- `.env.local`
```env
NEXT_PUBLIC_API_BASE_URL=http://192.168.0.23:8000
```
- 코드에서는 `process.env.NEXT_PUBLIC_API_BASE_URL`만 참조

---

## 4) 127.0.0.1 하드코딩 찾기

```powershell
rg "127\.0\.0\.1|localhost:8000|NEXT_PUBLIC_API_BASE_URL|api/auth" frontend
```

- 하드코딩 발견 시 env 변수 기반으로 교체

---

## 5) CORS/쿠키 여부 빠른 판단

- JWT를 **Authorization Bearer**로 보내면, 일반적으로 쿠키 이슈보다 CORS/헤더 노출 이슈가 핵심
- 브라우저 콘솔 Network 탭에서 확인:
  - preflight(OPTIONS) 실패
  - `Access-Control-Allow-Origin` 누락

(현재 저장소에는 DRF/CORS 설정이 안 보이므로, 실제 백엔드 코드 기준으로 `django-cors-headers` 적용 여부를 추가 점검하세요.)

---

## 6) MVP 흐름(환자 등록 → 한의원 조회) 최소 구현 순서

1. **환자가 Clinic code 입력**
2. 백엔드에서 code로 Clinic 조회
3. Enrollment(user, clinic, is_active=True) 생성 (중복이면 기존 활성화)
4. 한의원 계정에서 `Enrollment`로 환자 목록 조회
5. 목록에서 환자 클릭 시 trend/최근 체크인 조회

권장 API (예시):
- `POST /api/enroll/` : `{ "clinic_code": "ABC123" }`
- `GET /api/clinic/my-patients/`
- `GET /api/patients/{id}/trends/`

---

## 7) 오늘 바로 실행할 “한 번에 하나씩” 체크리스트

- [ ] `python manage.py runserver 0.0.0.0:8000`
- [ ] `Invoke-RestMethod http://127.0.0.1:8000/healthz/`
- [ ] 폰에서 `http://내PCIP:8000/healthz/`
- [ ] JWT 로그인 API를 PowerShell로 직접 호출
- [ ] 프론트 `.env.local`의 API 주소를 `내PCIP`로 변경
- [ ] `rg`로 127.0.0.1 하드코딩 제거
- [ ] 브라우저 Network 탭에서 CORS/401 여부 확인
- [ ] Enrollment API 최소 1개부터 붙이기
