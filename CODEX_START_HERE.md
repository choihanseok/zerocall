# ZERO CALL — Codex 개발 시작 안내

최종 점검: 2026-09-10 / ZC-TASK-20260910-005.
READY_FOR_DEVELOPMENT=YES (현재 로컬 환경). 운영/스테이징 실배포는 미완료이며 개발 시작의 선행 차단사항이 아니다.

## 작업 위치와 기준

- 프로젝트 폴더 안의 실제 Git 저장소인 `zero-call`에서 작업한다.
- 현재 누적 개발 브랜치: `codex/deployment-foundation`. main에는 아직 병합되지 않았다.
- 기능 기준 검증 커밋: 42e943afd06c2334e7241ced125a83651e739539. 그 뒤 개발 시작 문서 정리만 추가했다.
- 시작 전에 git status를 확인한다. 미커밋 변경을 초기화하거나 다른 사람의 변경을 원복하지 않는다.

## 먼저 읽기

1. AGENTS.md.
2. local-reference/00_MASTER_RULE.md.
3. local-reference/16_CODEX_TASK_RULE.md.
4. local-reference/17_PROJECT_BOOTSTRAP_CHECKLIST.md.
5. BOOTSTRAP_STATUS.md, docs/tasks/ZC-TASK-20260910-005_REPORT.md.
6. 해당 기능의 원문 정의서와 docs의 구현 보충 문서.

local-reference의 00~17 원문 사본은 읽기 전용으로 취급하고 공개하지 않는다. 새 clone/worktree에는 Git 제외 자료와 .venv/.env/DB가 자동 복사되지 않는다. 해당 환경에서는 원문 사본을 먼저 확보하고 의존성·환경설정·Migration 점검을 다시 한다. 현재 환경의 PASS를 다른 환경으로 자동 승계하지 않는다.

## 현재 Windows 환경의 실행 명령

저장소 루트의 PowerShell에서 가상환경 활성화 없이 실행할 수 있다.

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m build --wheel
.\.venv\Scripts\python.exe -m uvicorn zerocall.app:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

현재 .env는 LOCAL/개발용 SQLite 설정이며 Git 제외다. 기존 .env를 임의로 덮어쓰지 않는다. 새 환경 설치 명령은 README 참조. 스키마 갱신이 필요할 때만 개발 DB 대상을 확인하고 `python -m alembic upgrade head`를 실행한다. 현재 head는 20260910_003이다. 운영 DB에 개발 테스트를 실행하지 않는다.

서버 실행 후 /health가 UP이어야 한다. 이번 점검용 서버는 종료했으므로 개발 시 위 실행 명령으로 시작한다.

## 테스트 해석

- 로컬108 PASS, PostgreSQL 전용3 SKIP: 로컬 PostgreSQL 서버가 없어 의도적으로 건너뜀.
- 동일 코드의 GitHub CI에서 실제 PostgreSQL3개 테스트와 Docker build/start/health PASS.
- 의존성2개 deprecation warning은 남아 있으나 실패는 없다.
- 클라우드 운영 TLS·영구DB·백업/복구·실제 배포는 미검증이다.

## 다음 개발 작업

다음 작업번호 후보는 ZC-TASK-20260910-006이다. 사용자가 요청한 한 가지 목표를 정하고 관련 Requirement ID/현재 코드/영향분석/계획을 먼저 기록한 뒤 최소 범위 구현→Migration 필요 여부→테스트→보고서→문서 동기화를 수행한다. 가입·인증 정책의 NEED_REVIEW를 임의 확정하지 않는다.

004 인프라 Task는 무료 계정 연결 대기이며 배포를 완료했다고 보고하지 않는다. 해당 Task를 이어가는 경우 기존 번호004를 사용한다. 이번005는 개발 준비 점검만 완료했으며 새로운 업무 기능을 만들지 않았다.
