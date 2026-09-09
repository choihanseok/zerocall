# Account Foundation DB 구현 보충

기존 DB 정의서 §7~9의 accounts 중 이번 단계에 필요한 부분만 구현했다. 원본의 나머지 컬럼을 삭제한 것이 아니며 향후 별도 Migration으로 추가한다.

| 컬럼 | SQLAlchemy 유형 | NULL | 제약 |
| --- | --- | --- | --- |
| account_id | UUID (SQLite CHAR(32)) | NO | PK |
| account_status | VARCHAR(9) | NO | PENDING/ACTIVE/SUSPENDED/WITHDRAWN/BLOCKED CHECK |
| created_at | DateTime(timezone=True) | NO | 애플리케이션에서 aware UTC 변환 |
| updated_at | DateTime(timezone=True) | NO | created_at 이상 |
| deleted_at | DateTime(timezone=True) | YES | NULL 또는 created_at 이상 |
| password_hash | VARCHAR(256) | YES | AUTH 전용, 형식/비용 상한은 애플리케이션 검증 |

SQLite는 오프셋을 보존하지 않으므로 UTC로 정규화한 시각을 저장하고 조회 시 UTC timezone을 복원한다. UUID는 내부 호출자가 uuid4() 등으로 생성해 전달한다. 잘못된 UUID 및 nil UUID는 Service/Domain에서 거부한다. status index는 ix_accounts_account_status다.

Migration `20260910_001`은 추적 기반만, `20260910_002`는 accounts와 index만 생성한다. 자동 schema sync/create_all을 사용하지 않는다. 기존 동명 테이블이 있으면 덮어쓰지 않고 오류로 중단한다. NULL/default/backfill 대상 기존 계정 데이터가 없는 초기 Migration이다. 기존 다른 테이블과 데이터의 보존 및 재실행을 테스트한다.

downgrade는 데이터를 지우지 않고 명시적으로 거부한다. 문제가 생기면 쓰기를 중단하고 백업 후 검토된 forward migration을 적용한다. 이번 코드에는 hard delete, 상태 변경, 탈퇴 API가 없다.

phone/email/phone_verified_at/email_verified_at/last_login_at, AccountProfile/Agreement/Role/StatusHistory는 NOT_IMPLEMENTED. 전화번호·이메일 unique 정책은 원본에서도 후보이며 확정 전 구현하지 않는다. 기존 soft-deleted 레코드는 내부 일반조회에서 숨기되 원본과 PK는 보존한다.

후속 ZC-TASK-20260910-003에서 Migration 20260910_003으로 password_hash를 추가했다. 기존 데이터는 NULL 유지하며 backfill/삭제 없음. PENDING 계정의 비어 있는 해시를 내부에서 최초 저장할 수 있다. 일반 Account Entity에는 노출하지 않으며 ORM 컬럼은 deferred+raiseload다. [저장 계약](decisions/003-credential-storage.md) 참조.
