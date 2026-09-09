# Account Foundation 요구사항 추적 보충

이 파일은 기존 요구사항 Master의 대체본이 아니라 이번 구현 범위만 기록하는 보충 문서다. 원본 문서와 Original ID를 삭제하거나 변경하지 않는다.

| 원본 | 정규화 ID | 이번 구현 | 판정 |
| --- | --- | --- | --- |
| 회원 항목 25, 개별 ID 없음 | ZR-COM-ACCOUNT-003 | 내부 계정 생성·조회·저장 기반 | Foundation 구현, 회원가입 전체 NOT_IMPLEMENTED |
| 동일 | ZR-COM-ACCOUNT-004 | 로그인 | 범위 밖 |
| 동일 | ZR-COM-ACCOUNT-001/002 | SNS | 범위 밖, NEED_REVIEW 유지 |
| 동일 | ZR-COM-ACCOUNT-005 | 실명인증 | 범위 밖, NEED_REVIEW 유지 |
| 동일 | ZR-COM-ACCOUNT-006 | 권한설정 | 범위 밖 |

Task ZC-TASK-20260909-001 → AccountService → AccountRepository → accounts → AccountStatus → tests/test_account_*.py. Foundation용 테스트는 TC-ACC-001 회원가입 전체 검수를 대체하지 않는다.

Task ZC-TASK-20260910-002 → ZR-COM-ACCOUNT-003/004 관련 보안 기반(14_SECURITY_OPERATION §5/6/43) → PasswordHashAdapter / Argon2PasswordHashAdapter → tests/test_passwords.py. 비밀번호 해시 생성·검증만 구현. 가입/로그인 전체 NOT_IMPLEMENTED 유지.
