# Credential 저장 기반 결정

Task ZC-TASK-20260910-003. 원본 DB 정의 §7에 맞춰 별도 Credential 테이블 대신 accounts.password_hash를 추가한다. VARCHAR(256), nullable, default 없음. NULL은 비밀번호 미설정을 뜻하며 기존 계정은 그대로 유지한다. Argon2 포맷 검사는 애플리케이션에서 수행하며 DB 직접 쓰기 권한 통제는 운영 배포의 필수 후속 사항이다.

AUTH Repository가 해시 저장과 전용 조회를 담당한다. 일반 Account Entity에는 필드를 추가하지 않는다. ORM은 deferred+raiseload로 일반 Account SELECT에서 해시를 제외하고 우발적 접근 시 예외를 낸다. 이것은 DB 권한통제를 대체하지 않는다. 근거: [SQLAlchemy column loading](https://docs.sqlalchemy.org/en/20/orm/queryguide/columns.html).

Migration은 nullable column 추가만 수행한다. SQLite table 재생성·행 변경·해시 backfill 없음. 근거: [Alembic add_column](https://alembic.sqlalchemy.org/en/latest/ops.html#alembic.operations.Operations.add_column). 기존 row의 다섯 컬럼 보존과 ORM 정합성을 테스트했다. downgrade는 삭제 위험 때문에 거부한다.

initialize_pending은 신뢰할 수 있는 내부 코드 전용이다. UUID/aware 시각/해시 형식을 검증하고 PENDING + deleted_at IS NULL + password_hash IS NULL + updated_at <= 요청 시각을 한 UPDATE 조건으로 검사한다. 한 건 변경 시에만 commit한다. 중복/없는 계정/상태 불일치/삭제 계정/역행 시각은 동일한 초기 저장 거부 오류로 반환한다. 기존 해시 덮어쓰기 연산은 없다.

PENDING 제한은 기존 Foundation의 좁은 생성 범위를 잇는 기술 경계이며 가입·인증 허용 정책을 확정한 것이 아니다. get_hash는 삭제 계정을 제외하고 SecretStr 또는 None을 반환한다. 계정 상태/권한 검증이나 로그인 성공을 의미하지 않는다. 원문 가입 flow의 전화번호 확인·약관·권한과 인증 flow의 계정 상태·실패 제한·토큰 검증은 향후 반드시 갖춰야 한다.

Service는 기존 PasswordHashAdapter로 해시 후 Repository에 전달한다. 평문은 DB에 전달하지 않는다. 성공 로그는 commit 이후 이벤트/계정 UUID만 포함하며 해시/평문을 기록하지 않는다. SQL parameter hiding을 유지하고 저장 실패의 원본 exception을 일반 traceback에 전파하지 않는다. 임시 Python 메모리의 즉시 소거는 보장하지 않는다. 영구 Audit 및 실제 Actor 연결은 공개 API를 만들기 전 후속 Task다.

이번 작업은 인증정보의 최초 저장 기반이며 비밀번호 변경·재설정·자동 재해시 저장·로그인 API를 포함하지 않는다. 가입 정책 및 운영 준비는 NEED_REVIEW 유지.
