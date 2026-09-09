# ZERO CALL TASK REPORT

- Task ID: ZC-TASK-20260909-001
- Task: Account Foundation
- Module: ACCOUNT / Service: COMMON / Risk: HIGH
- 구현 결과: 완료, 로컬 검증 PASS
- Task Status: COMPLETED (요청된 내부 Foundation 범위)
- 마지막 검증일: 2026-09-10

## Before / Impact

현재 저장소는 사용자 지정 choihanseok/zerocall이다. 최초 원격은 빈 저장소였으며 README 초기 커밋 후 공통 기반을 구성했다. 기존 Account, API, Table, Framework는 없었다. 사용자 위임으로 기술 선택과 Bootstrap을 먼저 검증했다. 영향범위는 공통 기반과 내부 Account 영속성에 한정되며 금융·권한·외부 시스템에 영향 없음.

ZR-COM-ACCOUNT-003의 기반 부분에 연결한다. 원본 회원 항목에는 개별 ID가 없으며 정규화 ID는 첨부 개발문서의 것을 보존한다. 회원가입 전체 요구사항은 완료 처리하지 않는다.

## Implemented

불변 Account Entity, 정의된 다섯 AccountStatus, Repository Protocol/SQLAlchemy 구현, 내부 Service Base, PENDING 생성 및 조회, UUID/시각 검증, PK 중복 방지, transaction rollback, 삭제 표시 레코드 조회 제외, UTC 저장·복원.

전화번호/이메일/비밀번호 필드와 인증·로그인·JWT·SNS·Role/Permission·상태전이·탈퇴·주문·결제·정산·UI 및 Account 공개 API는 구현하지 않았다. Account 생성은 회원가입 완료가 아니다.

## Changed Files

- Modified: README.md (원격 초기본 기준).
- Created foundation: .gitignore, .env.example, AGENTS.md, BOOTSTRAP_STATUS.md, pyproject.toml, requirements.lock, alembic.ini, .github/workflows/ci.yml.
- Created common: src/zerocall/__init__.py, app.py, common/__init__.py, config.py, database.py, errors.py, logging.py.
- Created account: src/zerocall/account/__init__.py, domain.py, errors.py, repository.py, service.py, persistence.py.
- Created migrations: migrations/env.py, versions/20260910_001_bootstrap.py, versions/20260910_002_accounts.py.
- Created tests: tests/conftest.py, test_bootstrap.py, test_account_unit.py, test_account_integration.py.
- Created docs: docs/REFERENCE_INDEX.md, docs/02_REQUIREMENTS_MASTER.md, 08_DATABASE_DEFINITION.md, 09_API_DEFINITION.md, 10_STATUS_CODE_DEFINITION.md, 14_SECURITY_OPERATION.md, 15_TEST_ACCEPTANCE.md, decisions/001-foundation.md, tasks/ZC-TASK-20260910-001_PLAN.md, tasks/ZC-TASK-20260910-001_REPORT.md, tasks/ZC-TASK-20260909-001_PLAN.md, tasks/ZC-TASK-20260909-001_REPORT.md.
- Deleted: NONE. 원본 참조자료 변경 없음.
- Local only: .venv, dist/build, zerocall-local.db (Git 제외). 상위 docs/reference/development-documents.txt는 원문 읽기용 추출자료로 원격에 포함하지 않음.

## Migration

20260910_001 초기 tracking → 20260910_002 accounts 생성 및 status index. PK/status/시각 순서 제약 포함. 초기 개발 DB에 적용했고 head=20260910_002 확인. 기존 다른 테이블과 데이터 보존 및 반복 실행 검증. 데이터 삭제/변환 없음. 파괴적 downgrade는 명시적으로 거부한다.

## Tests

- Unit: 18 PASS / 0 FAIL.
- Integration: 15 PASS / 0 FAIL.
- Bootstrap Regression: 14 PASS / 0 FAIL (전체 원문 대조 후 공통 오류 검증 3건 추가).
- 전체: 47 PASS / 0 FAIL.
- Lint: PASS. 최초 줄 길이 오류 1건 수정 후 PASS.
- Build: Account를 포함한 wheel 생성 PASS.
- 실제 loopback 서버 시작 및 /health 응답: PASS, 검증 후 해당 서버 종료.
- DB: 로컬 Migration head 적용 및 조회 PASS.
- 원격 CI: PASS. 커밋 02fbfecd3c1957c44de7fe46100682558b1b4023의 GitHub Actions 실행 34390770096에서 설치·pytest·ruff·wheel build 모두 성공. [실행 결과](https://github.com/choihanseok/zerocall/actions/runs/34390770096).
- 서드파티 TestClient deprecation warning 2건 존재. 실패를 숨기거나 테스트를 삭제하지 않음.

## Docs Sync

DB/API/Status/Security/Test 및 Requirement 추적 보충 문서와 기술 결정, Bootstrap/Task 보고서를 작성했다. 원본 정의서를 덮어쓰지 않았다. 후속 첨부에서 00~17번 전체를 확보하고 17번 §168 및 종료 선언까지 읽었다. 출처는 docs/REFERENCE_INDEX.md에 기록했다. 이전 문서 차단은 해소했다. 공통 401/403/429 오류 클래스 및 로그 message 필드를 기준과 일치시켰다.

## Known Issues / NEED_REVIEW

1. 17_PROJECT_BOOTSTRAP_CHECKLIST 전체 원문 검토 완료. 사본 18개는 local-reference에 보관하며 원격에는 공개하지 않는다. 새 작업 환경에서는 원문 확보가 필요하다.
2. SQLite 기반 로컬 검증이며 PostgreSQL 실서버 및 운영 배포는 미검증. STAGING/PRODUCTION 실행은 차단한다.
3. 전화번호/이메일 유일성·정규화, Account 상태전이·탈퇴·재가입 및 Actor/Scope/Audit 정책은 원본의 NEED_REVIEW 유지.
4. 관리자 검수 화면은 사용자 요청 범위 밖이며 미구현. 현 상태를 운영 기능 완료로 해석하지 않는다.
5. 공개 저장소 게시가 최초 자동 검토에서 거절되었으나, 사용자가 공개 승인 관련 문구를 선택하여 명시적으로 승인했다. 공개 범위를 유지하고 코드·테스트·CI·보충 문서 40개 게시를 완료했다. 비밀값·원본 참조자료·DB 파일은 포함하지 않았다.

## GitHub 게시

- Branch: codex/account-foundation
- [PR #1](https://github.com/choihanseok/zerocall/pull/1)
- main 병합 및 운영 배포 없음. Draft PR에 현재 범위 검증 결과를 반영한다.
- 게시 승인은 이번 준비 결과물의 공개에 적용하며 향후 모든 동작의 자동 승인 설정을 변경한 것은 아니다.

## READY/NEXT TASK

READY_FOR_LOCAL_FOUNDATION: YES. READY_FOR_PRODUCTION: NO. 정식 COMPLETED: YES (현재 범위).
사용자의 후속 자동 진행 요청에 따라 별도 Task ZC-TASK-20260910-002 Password Hashing Foundation을 다음 작업으로 수행한다. Account Task의 범위를 확장하지 않는다.
