# AccountStatus 구현 보충

Account 상태코드는 원본 08_DATABASE_DEFINITION §8의 PENDING, ACTIVE, SUSPENDED, WITHDRAWN, BLOCKED를 그대로 사용한다. 원본 10번 문서에는 Account 전이표가 없으므로 전이정책은 NEED_REVIEW다.

Foundation의 create_pending은 내부 PENDING 레코드만 생성한다. 가입 완료·실명확인·전화번호 인증 또는 로그인 가능 상태를 의미하지 않는다. Repository도 ACTIVE 등으로 직접 생성하는 호출을 거부한다. 기존 레코드를 읽을 때는 정의된 다섯 상태를 표현할 수 있다.

상태변경, 활성화, 정지, 탈퇴, 복구 메서드는 구현하지 않았다. 향후 Actor/Scope/Reason/History/Audit 규칙 확정 후 별도 Task에서 구현한다. 새 상태코드 추가 없음.
