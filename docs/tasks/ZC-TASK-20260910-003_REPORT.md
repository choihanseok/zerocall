# ZERO CALL TASK REPORT

- Task ID: ZC-TASK-20260910-003
- Task: Password Credential Storage Foundation / Module: AUTH COMMON
- Risk: CRITICAL / Status: COMPLETED (내부 저장 기반 범위)

## Requirement / Impact

ZR-COM-ACCOUNT-003/004의 기반 부분. DB 원문 §7/99와 보안 원문 §5/6/43에 근거한다. Account/Hash Foundation 뒤에 별도 작업으로 수행했다. 기존 Framework/ORM을 유지했으며 현재 Account Entity/API/상태전이/권한 변경 없음. 가입·로그인 전체는 NOT_IMPLEMENTED다.

## Changed Files

- Added: migrations/versions/20260910_003_password_hash.py, src/zerocall/auth/credentials.py, src/zerocall/auth/credential_persistence.py, tests/test_credentials.py.
- Added docs: docs/decisions/003-credential-storage.md, docs/tasks/ZC-TASK-20260910-003_PLAN.md, docs/tasks/ZC-TASK-20260910-003_REPORT.md.
- Modified: src/zerocall/account/persistence.py, src/zerocall/auth/passwords.py, tests/test_account_integration.py, README.md, BOOTSTRAP_STATUS.md, docs/02_REQUIREMENTS_MASTER.md, docs/08_DATABASE_DEFINITION.md, docs/09_API_DEFINITION.md, docs/14_SECURITY_OPERATION.md, docs/15_TEST_ACCEPTANCE.md.
- Deleted: NONE. 개인 비밀번호·원본 문서·DB 파일 공개 없음.

## Migration

20260910_003: accounts.password_hash VARCHAR(256) NULL 추가. 기존 행 NULL 유지, backfill/default/데이터 삭제 없음. 일반 Account 조회는 해시를 불러오지 않는다. Migration 반복 실행과 기존 행·기존 해시 보존 검증 PASS. downgrade는 파괴적 작업을 거부한다.

## Tests

- 신규 19 + 기존 73 = 전체 92 PASS / 0 FAIL. Ruff PASS. wheel build PASS.
- 실제 Argon2→DB→새 연결에서 검증, 동시 최초 저장 한 건 성공, 중복 덮어쓰기 금지, 비정상 상태·삭제·없는 계정·역행 시각 거부, commit 실패 rollback 및 성공 로그 없음, 해시/평문 미출력, ORM 일반 조회 제외, Migration 보존/정합성 검증.
- 기존 DB 제약 테스트는 컬럼 추가에 맞춰 INSERT 컬럼명을 명시하고 최신 Migration head 기대값만 갱신했다. 기존 검증 삭제 없음.
- 최초 실패: 테스트용 미래 UTC 시각과 현재 시각 비교 오류 1건을 고정 시각으로 수정. 줄 길이 오류 수정. 최종 모두 PASS.
- 기존 서드파티 deprecation warning 2건 유지.
- 원격 CI: 코드 커밋 8e167dd828181f9b72437786bf83d3aacdb5e3ec의 [실행 34394155684](https://github.com/choihanseok/zerocall/actions/runs/34394155684) PASS. 설치·Lint·92개 Test·wheel Build 성공.

## Docs Sync

요구사항·DB/API·보안·테스트·기술 결정·Bootstrap 상태·README 및 계획/보고서 갱신. 원문 기준과 원본 ID 유지.

## Known Issues / NEED_REVIEW

- 공개 가입/로그인, 전화번호 인증, JWT, Role/Permission, 비밀번호 변경·재설정은 미구현.
- 비밀번호 업무 정책·인증 실패 제한·Actor/영구 Audit 및 운영 자원/동시성 검증은 후속 과제다.
- get_hash는 내부 secret 접근이며 인증 성공을 의미하지 않는다. 공개 API로 직접 연결하면 안 된다.
- SQLite LOCAL/DEV/TEST만 검증. 운영 DB/배포 준비 NO.

## READY/NEXT TASK

READY_FOR_INTERNAL_FOUNDATION: YES. READY_FOR_PRODUCTION: NO.
[Draft PR #3](https://github.com/choihanseok/zerocall/pull/3), base=codex/password-hashing-foundation. main 병합·운영 배포 없음.
다음 후보는 인증 정책과 경계 설계 검토다. 현재 Task 보고 후 종료하며 다음 기능은 아직 구현하지 않았다.

로컬 Migration 실행: 환경 미설정 첫 시도는 안전하게 거부되었고, 명시적 LOCAL·개발용 SQLite 환경으로 적용 후 head=20260910_003 확인. 운영 DB 접근 없음.
