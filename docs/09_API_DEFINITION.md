# Foundation API 구현 보충

이번 공개 HTTP 표면은 GET /health 하나다. DB 연결 정상 시 200 `{"status":"UP"}`, 실패 시 503 DATABASE_UNAVAILABLE를 반환한다. 미정의 경로는 404 RESOURCE_NOT_FOUND다. HTTP 에러는 success=false, error.code, error.message, traceId를 포함하며 X-Trace-ID 헤더와 일치한다. 검증 실패는 422 VALIDATION_FAILED, 예기치 않은 오류는 500 INTERNAL_SERVER_ERROR다.

공통 UNAUTHORIZED(401), FORBIDDEN(403), RATE_LIMIT_EXCEEDED(429) 오류 클래스도 준비했다. 실제 인증/권한/요청 제한을 구현한 것은 아니다.

AccountService.create_pending(UUID)와 get(UUID)는 Python 내부 호출용이다. HTTP 가입/조회 API, Swagger, 인증·역할 기능은 없다. 외부 접근 시 Account 경로는 404이며 공개되지 않는다. 이후 API Task에서 인증·권한·소유권을 갖춘 경계를 먼저 구현해야 한다.

ACCOUNT_ALREADY_EXISTS는 내부 PK 중복, ACCOUNT_STORAGE_UNAVAILABLE는 영속성 실패를 뜻한다. 전화번호 중복 오류와 혼동하지 않는다. 존재하지 않거나 삭제 표시된 내부 계정 조회는 RESOURCE_NOT_FOUND다. 기존 설계 API를 삭제한 것이 아니라 아직 구현하지 않은 상태다.

ZC-TASK-20260910-003: PasswordCredentialService.initialize_pending는 내부 호출용이며 새 HTTP 경로는 없다. Credential Repository.get_hash는 SecretStr/None을 반환하며 인증 성공 판정이 아니다. CREDENTIAL_INITIALIZATION_REJECTED(409)는 최초 저장 조건 불충족, CREDENTIAL_STORAGE_UNAVAILABLE(500)는 마스킹된 저장 오류다. 실제 공개 API는 향후 인증·정책·권한·Audit 경계를 갖춰야 한다.
