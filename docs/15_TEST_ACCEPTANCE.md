# Account Foundation 테스트 검수 보충

| 구분 | 파일 | 범위 |
| --- | --- | --- |
| Unit | tests/test_account_unit.py | 생성·조회, PK 검증, 불변성, 상태 집합, 시각 검증, 중복, 저장 실패 |
| Integration | tests/test_account_integration.py | 실제 SQLite 저장과 재연결, UTC, 중복 및 동시성, rollback, 누락 스키마, soft delete 조회 제외, DB 제약, Migration 보존·재실행·ORM 정합성 |
| Bootstrap/Regression | tests/test_bootstrap.py | 서버/Health/DB/Config/공통 오류/Trace/마스킹 |

최초 전체 검증 44 PASS / 0 FAIL. 전체 원문 대조 후 공통 401/403/429 오류 검증을 추가하여 현재 47 PASS / 0 FAIL. 실행 명령은 README에 기록한다. CI는 동일한 테스트를 실행하도록 구성한다. 원격 CI 결과는 Task Report에서 별도 기록한다.

권한 없음은 계정 HTTP 경로가 404로 비공개임을 확인하는 범위만 검증한다. 정식 Role/Scope 검증은 구현하지 않았으므로 PASS로 표시하지 않는다. 취소/탈퇴/외부 API/결제/네트워크 API 실패는 기능 자체가 범위 밖이다. DB 연결·transaction 실패는 포함한다.

TC-ACC-001(회원가입), TC-ACC-002(전화번호 중복), TC-ACC-003(미인증 가입 차단), TC-ACC-004(탈퇴 전체 flow)는 이번 Foundation 테스트로 완료 처리하지 않는다.
