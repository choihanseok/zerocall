# ZERO CALL

공통 플랫폼과 서비스별 모듈을 분리하는 생활형 O2O 플랫폼의 초기 Backend입니다.

## 현재 상태

저장소: https://github.com/choihanseok/zerocall

Python 3.12 / FastAPI / SQLAlchemy / Alembic / SQLite(LOCAL·DEV·TEST).
Account Foundation 내부 구현과 로컬 테스트를 완료했습니다. 운영 배포 및 회원가입 서비스는 미완료입니다. Task의 최종 문서 검토 항목은 [작업 보고서](docs/tasks/ZC-TASK-20260909-001_REPORT.md)를 참고하세요.

## 개발 범위

Account Entity, AccountStatus, Repository, Service Base, 필요한 Migration 및 Unit/Integration Test만 구현한다. 전화번호 인증, 로그인, JWT, SNS, Role/Permission, 주문, 결제, 정산, UI는 제외한다.

## 설치 및 실행

Python 3.12를 설치한 뒤 저장소 루트에서 실행합니다. Windows에서는 가상환경 활성화를 `.venv\Scripts\Activate.ps1`로, macOS/Linux에서는 `source .venv/bin/activate`로 수행합니다.

```text
python -m venv .venv
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
```

가상환경을 활성화한 뒤 `.env.example`을 `.env`로 복사합니다. 설정값은 LOCAL 환경과 로컬 DB 파일 경로만 포함합니다. 모든 DB 스키마 변경은 아래 Migration 명령으로 실행합니다.

```text
python -m alembic upgrade head
python -m uvicorn zerocall.app:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

GET http://127.0.0.1:8000/health → `{"status":"UP"}`. Account는 내부 Python Service와 Repository로만 접근하며 HTTP API는 없습니다. 신뢰된 내부 호출에서 `AccountService(SqlAlchemyAccountRepository(make_sessions(engine)))`로 구성하고 `create_pending(uuid4())`를 호출할 수 있습니다. 이후 외부 API를 추가할 때 인증·권한·소유권 검사가 선행되어야 합니다.

## 검증

```text
python -m pytest -q
python -m ruff check .
python -m build --wheel
```

테스트는 임시 SQLite 파일을 사용합니다. wheel은 Python 코드 패키지이며, Migration 실행에는 이 저장소 checkout의 alembic.ini와 migrations 폴더가 필요합니다.

## 문서 및 제한

docs의 DB/API/상태/보안/테스트 파일은 이번 구현의 보충 문서입니다. 원본 정의서를 대체하지 않습니다. 원본 참조자료는 읽기 전용으로 보존하며 공개 저장소에 올리지 않았습니다. 00~17번 전체 원문을 확보해 검토했으며 [기준 문서 확인 기록](docs/REFERENCE_INDEX.md)에 출처를 남겼습니다.

현재 운영 환경은 실행을 거부합니다. PostgreSQL, 인증, 관리자와 운영 배포 검증은 별도 작업입니다. [기술 결정](docs/decisions/001-foundation.md), [Bootstrap 결과](docs/tasks/ZC-TASK-20260910-001_REPORT.md), [Account 보고서](docs/tasks/ZC-TASK-20260909-001_REPORT.md)를 확인하세요.

## 후속 작업

ZC-TASK-20260910-002: 내부 비밀번호 해시 처리 기반. [Task Report](docs/tasks/ZC-TASK-20260910-002_REPORT.md) 및 [기술 결정](docs/decisions/002-password-hashing.md) 참조. Account 저장 및 로그인 API 연결은 후속 범위다.
