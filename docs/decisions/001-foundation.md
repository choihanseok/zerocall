# Foundation 기술 결정

2026-09-10 사용자가 Backend·ORM·DB 선택과 최소 Bootstrap 구성을 위임했다.

Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, pytest를 사용한다. 기존 구현은 없으므로 라이브러리 교체 영향도 없다. Framework는 공통 HTTP 기반, ORM은 공통 영속성 경계, Alembic은 명시적 스키마 변경에 사용한다. 실제 설치 버전은 requirements.lock에 고정한다.

LOCAL/DEV/TEST는 명시적인 SQLite 파일을 사용한다. 운영 DB 후보는 PostgreSQL이며 전환 Migration 및 실서버 통합시험 전까지 STAGING/PRODUCTION 실행을 거부한다. 운영 준비 완료를 의미하지 않는다. 개발 서버는 loopback에 바인딩한다. 인증·권한이 없는 Account HTTP API는 만들지 않는다.

참고: [FastAPI SQL databases](https://fastapi.tiangolo.com/tutorial/sql-databases/), [SQLAlchemy dialects](https://www.sqlalchemy.org/features.html), [Alembic](https://alembic.sqlalchemy.org/en/latest/).

배포 클라우드/도메인, 전화번호·이메일 정규화와 유일성, 탈퇴 후 재가입, 상태전이와 관리자 권한은 기술 선택 위임과 별개의 업무정책이다. NEED_REVIEW로 유지한다.
