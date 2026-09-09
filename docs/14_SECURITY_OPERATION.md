# Foundation 보안 운영 보충

- Config는 환경변수 또는 로컬 .env에서만 읽는다. .env와 DB 파일은 Git 제외.
- LOCAL/DEV/TEST만 실행 가능하며 STAGING/PRODUCTION은 실패 처리한다. 서비스 배포 미완료.
- SQL parameter와 원본 exception, request body/query/header를 로그로 출력하지 않는다.
- Trace ID는 서버가 UUID로 새로 발급한다. 클라이언트 임의 문자열을 로그에 반영하지 않는다.
- Account 로그는 commit 후 생성 이벤트와 내부 UUID만 남긴다. 개인정보·인증정보 없음.
- UI/Account API가 없으며 권한검사를 생략한 외부 계정 접근을 만들지 않는다.
- 서버는 README 명령의 127.0.0.1 주소로만 실행한다. CORS allow-all 없음.
- 테스트는 임시 디렉터리 DB만 사용한다. 실제 고객 데이터·운영 DB 연결 없음.
- 정식 Audit 저장소, 인증, 관리자, 운영 백업/복구, HTTPS 배포, PostgreSQL 실서버 검증은 미구현이다.

로컬 개발 준비와 운영 준비를 구분한다. 저장소는 사용자가 지정한 공개 저장소로 확인되었으며 비밀값과 원본 참조자료는 포함하지 않는다.
