# 일상 건강상태 트래킹 MVP (Django + Next.js)

자가 기록 기반으로 매일 지표를 입력하고, 기간별 추세를 보는 모바일 웹앱입니다.  
**고정 안내 문구:** `자가 기록 기반의 추세이며 의학적 판단이 아닙니다.`

## 1) 프로젝트 구조

```text
km-clinic-beta/
├─ backend/
│  ├─ manage.py
│  ├─ requirements.txt
│  ├─ config/
│  │  ├─ settings.py
│  │  ├─ urls.py
│  │  ├─ asgi.py
│  │  └─ wsgi.py
│  └─ apps/
│     └─ tracker/
│        ├─ models.py
│        ├─ views.py
│        ├─ serializers.py
│        ├─ admin.py
│        ├─ urls.py
│        └─ migrations/
│           ├─ 0001_initial.py
│           └─ 0002_seed_default_metrics.py
└─ frontend/
   ├─ package.json
   ├─ app/
   │  ├─ page.tsx
   │  ├─ login/page.tsx
   │  ├─ trend/page.tsx
   │  ├─ layout.tsx
   │  └─ globals.css
   ├─ components/Disclaimer.tsx
   └─ lib/api.ts
```

## 2) 기능 요약

- 인증: JWT 로그인 (`/api/auth/token/`)
- 데일리 체크인: 사용자별 날짜 1회 저장(업서트)
- 지표 5개 기본 제공:
  - sleep_quality (0-10)
  - fatigue (0-10)
  - stress (0-10)
  - digestion (0-10)
  - bowel (text)
- 추세 조회: 7/30/90일 + 지표 선택
- 관리자: Django Admin에서 `MetricDefinition` CRUD

## 3) Windows 실행 방법 (복붙용)

### 3-1. 백엔드 실행 (127.0.0.1:8000)

```powershell
cd C:\path\to\km-clinic-beta\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

### 3-2. 프론트 실행 (localhost:3000)

새 PowerShell 창:

```powershell
cd C:\path\to\km-clinic-beta\frontend
npm install
npm run dev
```

브라우저:
- 로그인: `http://localhost:3000/login`
- 오늘 입력: `http://localhost:3000/`
- 추세: `http://localhost:3000/trend`
- 관리자: `http://127.0.0.1:8000/admin/`

## 4) API 명세

- `POST /api/auth/token/`  
  body: `{ "username": "...", "password": "..." }`
- `GET /api/metrics/`
- `GET /api/entries/today/`
- `POST /api/entries/upsert/`  
  body 예시:
  ```json
  {
    "date": "2026-01-18",
    "note": "오늘 컨디션 메모",
    "values": [
      {"metric_key": "sleep_quality", "value_int": 7},
      {"metric_key": "fatigue", "value_int": 4},
      {"metric_key": "stress", "value_int": 6},
      {"metric_key": "digestion", "value_int": 8},
      {"metric_key": "bowel", "value_text": "정상"}
    ]
  }
  ```
- `GET /api/entries/trend/?days=30&metric_key=sleep_quality`

## 5) 개발 참고

- DB는 기본 SQLite이며, Django ORM 기반으로 PostgreSQL 전환이 쉽도록 구성했습니다.
- CORS는 개발 단계에서 `http://localhost:3000` 허용입니다.
- 배포 전에는 `CORS_ALLOWED_ORIGINS`, `DEBUG`, `ALLOWED_HOSTS`를 환경별로 반드시 제한하세요.
