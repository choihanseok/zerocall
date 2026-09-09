# ZERO CALL TASK REPORT

- Task ID: ZC-TASK-20260910-002
- Task: Password Hashing Foundation / Module: AUTH COMMON / Risk: HIGH
- Status: COMPLETED (내부 Password Hashing Foundation 범위)

## Requirement / Impact

14_SECURITY_OPERATION §5/6/43와 ZR-COM-ACCOUNT-003/004의 보안 기반 부분을 구현했다. 기존 구현에 비밀번호 처리 모듈은 없었으며 Account Foundation의 완료 후 별도 Task로 진행했다. 가입·로그인 전체 요구사항은 NOT_IMPLEMENTED 유지. 기존 Framework/ORM/API/Table/Data 삭제 또는 교체 없음.

## Changed Files

- Added: src/zerocall/auth/__init__.py, src/zerocall/auth/passwords.py, tests/test_passwords.py.
- Added docs: docs/decisions/002-password-hashing.md, docs/tasks/ZC-TASK-20260910-002_PLAN.md, docs/tasks/ZC-TASK-20260910-002_REPORT.md.
- Modified: pyproject.toml, requirements.lock, README.md, docs/02_REQUIREMENTS_MASTER.md, docs/14_SECURITY_OPERATION.md, docs/15_TEST_ACCEPTANCE.md.
- Deleted: NONE. 원문 참조자료·실제 비밀번호·DB 파일은 포함하지 않음.

## Migration

NONE. Account 컬럼과 기존 Migration head 20260910_002를 유지한다. DB 접근·저장·삭제 없음.

## Tests

- 신규 26 PASS: 실제 Argon2 생성·검증, 무작위 salt, Unicode·공백 보존, 잘못된 입력·해시, 계산 비용 상한, 재해시 필요 판단, 오류 마스킹.
- 기존 47 PASS. 전체 73 PASS / 0 FAIL. Ruff PASS.
- Build: auth 모듈이 포함된 wheel 생성 PASS.
- 원격 CI: 코드 커밋 4dab85b8f2edee4ca0bca1a8cfaad89357e4a07c의 [실행 34392762064](https://github.com/choihanseok/zerocall/actions/runs/34392762064) PASS. 설치·Lint·73개 Test·wheel Build 성공.
- 기존 서드파티 deprecation warning 2건 유지. 테스트 실패 없음.

## Docs Sync

계획서·기술 결정·요구사항 추적·보안·테스트·README를 동기화했다. 원본 요구사항 ID와 업무 정책을 변경하지 않았다.

## Known Issues / NEED_REVIEW

- 가입 비밀번호 길이/복잡도·유출 목록·변경/재설정 정책은 미확정이다. 4096 bytes는 내부 기술 자원 상한이다.
- 운영 동시성/메모리 검증 및 API 연결 시 thread offload·rate limit은 후속 작업이다.
- 저장소 연결, 실제 인증 API, 관리자 검수, 운영 DB/배포는 미구현. 운영 준비 NO.
- 지정 검증 자원 상한을 넘는 기존 해시 및 다른 알고리즘의 이관 정책은 별도 검토가 필요하다.

## READY/NEXT TASK

READY_FOR_INTERNAL_FOUNDATION: YES. READY_FOR_PRODUCTION: NO. 현재 Task 완료.
[Draft PR #2](https://github.com/choihanseok/zerocall/pull/2), base=codex/account-foundation. main 병합·운영 배포 없음. 다음 후보는 Credential 저장 설계 검토이며 아직 착수하지 않았다. 이번 Task 보고 후 종료한다.
