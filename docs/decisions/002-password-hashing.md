# Password Hashing Foundation 기술 결정

- Task: ZC-TASK-20260910-002
- 사용자 위임 범위의 기술 결정. 업무 비밀번호 정책을 확정하지 않는다.
- Argon2id, argon2-cffi 25.1 계열. RFC_9106_LOW_MEMORY 프로파일을 명시적으로 선택한다: memory 65536 KiB, iterations 3, parallelism 4, salt 16 bytes, hash 32 bytes. 무작위 salt는 라이브러리가 생성한다.
- 근거: [argon2-cffi 공식 API](https://argon2-cffi.readthedocs.io/en/stable/api.html), [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html). 독자적인 암호 알고리즘은 작성하지 않는다.

## 내부 계약

PasswordHashAdapter의 hash는 인코딩된 해시를 반환한다. verify는 일치 시 True, 불일치 시 False를 반환한다. needs_rehash는 선택한 프로파일과 다른지 확인한다. 재해시는 향후 정상 인증 후 별도 저장 작업이 수행해야 하며 현재 자동 저장은 없다.

입력은 비어 있지 않은 UTF-8 문자열이며 기술적 자원 상한 4096 bytes를 적용한다. trim, Unicode 정규화, 대소문자 변환, 잘라내기를 하지 않는다. 길이/복잡도/유출 비밀번호 목록 등 가입 정책은 NEED_REVIEW다.

저장 해시는 내부의 신뢰할 수 있는 저장소에서만 받아야 한다. 방어적으로 256문자 이하의 canonical Argon2id v19 형식과 Base64, salt 8~64 bytes, hash 16~64 bytes를 검사한다. 검증 자원은 memory 최대64 MiB, iterations 최대3, parallelism 최대4로 제한한다. 상한 밖의 기존 해시는 자동 처리하지 않는다. 지원 범위 안의 낮은 비용 해시는 검증 후 재해시 필요를 표시할 수 있으며 신규 생성은 항상 지정 프로파일을 사용한다.

입력 오류는 ValidationFailed, 잘못되거나 지원하지 않는 저장 해시는 InvalidStoredPasswordHash, 라이브러리 연산 실패는 PasswordHashUnavailable로 구분한다. 공개 오류 메시지와 일반 traceback에는 원본 라이브러리 오류를 연결하지 않는다. 이 모듈은 로그·파일·DB를 쓰지 않는다. Python 메모리의 안전한 즉시 소거를 보장하지 않으며 debugger/locals 수집도 비밀값에서 제외해야 한다.

동기 CPU·메모리 작업이다. 향후 async API 연결 시 이벤트 루프 밖에서 실행하고 동시 실행 제한·rate limit 및 배포 자원 검증을 먼저 추가해야 한다. 요청당 상한은 전체 서버 동시 처리 상한을 대체하지 않는다.

## 제외

Account 스키마/비밀번호 저장/로그인 API/JWT/OTP/SNS/Role/Permission/비밀번호 변경·재설정은 구현하지 않는다. 이 모듈만으로 인증 또는 운영 보안 준비가 완료되지 않는다.
