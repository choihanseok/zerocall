# ZERO CALL 개발 준비 상태

- 최종 점검: 2026-09-10 / ZC-TASK-20260910-005
- READY_FOR_DEVELOPMENT: YES (현재 로컬 환경)
- BLOCKING_DEVELOPMENT_SETUP_ISSUES: NONE
- READY_FOR_STAGING_DEPLOYMENT: NO
- READY_FOR_PRODUCTION: NO

## 시작 위치

실제 저장소는 zero-call, 현재 누적 개발 브랜치는 codex/deployment-foundation이다. main은 아직 병합하지 않았다. [Codex 시작 안내](CODEX_START_HERE.md)를 먼저 읽는다.

## 완료한 개발 준비

00~17 원문18개 확인, Framework/의존성/Git/로컬 환경/DB/Migration 확인, 실제 서버와 Health 확인, 공통 Error/Logging/Trace 회귀 검증 완료. 로컬108 tests PASS 및 PostgreSQL3 tests는 CI에서 PASS. Lint/wheel build/PostgreSQL/Docker build/start/health 모두 검증했다. .env·DB·원문자료는 Git 제외다.

현재 기술: Python3.12/FastAPI/SQLAlchemy/Alembic. LOCAL은 SQLite, PostgreSQL은 전용 CI에서 검증했다. Migration head=20260910_003. 기능 기준 commit=42e943afd06c2334e7241ced125a83651e739539.

## 개발 결과와 별도 남은 항목

Account Foundation, Password Hashing, Credential Storage 기반 구현 완료.004의 PostgreSQL/Docker 배포 준비 코드는 검증됐지만 클라우드 실제 자원 생성은 계정 연결 대기다. 예산0원으로 유료 자원은 생성하지 않았다. 운영/스테이징 서버·영구DB·HTTPS/권한분리/백업복구 실증은 미완료이며 현재 로컬 개발 시작을 막지 않는다.

원문 기준 사본은 local-reference에 있다. 새 clone/worktree에서 자동으로 복사되지 않으므로 해당 환경의 문서·의존성·환경·DB 점검은 다시 수행한다. 기존 자료와 사용자 변경은 보존한다.

[최종005 보고서](docs/tasks/ZC-TASK-20260910-005_REPORT.md) / [004 인프라 진행 보고서](docs/tasks/ZC-TASK-20260910-004_REPORT.md)
