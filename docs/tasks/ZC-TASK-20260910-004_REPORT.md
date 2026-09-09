# ZERO CALL TASK REPORT

- Task ID: ZC-TASK-20260910-004 / Deployment Foundation
- Status: IN_PROGRESS — 코드 준비 후 실제 계정 연결 대기
- 사용자 확정: 기존 서버 없음, 새 구성 요청, 월 예산 0원. 유료 자원 생성 금지.

## Changed Files

Dockerfile, .dockerignore, deploy/README.md, common/config.py, common/database.py, account/persistence.py, pyproject.toml, requirements.lock, .github/workflows/ci.yml, tests/test_deployment_config.py, tests/test_postgresql.py, README 및 Bootstrap/보안/DB/테스트 보충 문서, 004 계획/보고서.
삭제 없음. 기존 Framework/SQLite 데이터/계정 API 유지. 실제 Secret 포함 없음.

## Migration

새 Migration 없음. 기존 head 20260910_003을 PostgreSQL에서도 검증한다. 운영/스테이징 실DB는 아직 생성하거나 접근하지 않았다.

## Tests

로컬105 PASS, PostgreSQL 전용3 SKIP(로컬 서버 없음). 기존92개 회귀 포함. 원격 PostgreSQL service job에서3개 테스트, Docker build/start/health를 실행하도록 구성했다. 실제 원격 결과는 확인 후 기록한다. TLS 설정 거부/수용은 구성 검증이며 실제 클라우드 TLS 성공을 의미하지 않는다.

## Docs Sync

인프라 요구 INFRA-004 및 14_SECURITY_OPERATION 환경분리·TLS·최소권한·백업/복구/배포 기준을 추적한다. deploy/README에 구성과 미완료 사항을 명시했다. 기존 ID 보존.

## Known Issues / NEED_REVIEW

무료 Render 로그인 화면을 열었으나 계정은 연결되지 않았다. 현재 호출 가능한 클라우드 계정 생성 연결도 없다. 카드/유료 자원 없이 가입 후 무료 플랜 조건을 확인해야 한다. 무료 Render DB는 만료/백업 제한 때문에 운영 DB로 채택하지 않았다.
서버/DB/권한분리/실제 TLS/HTTPS/백업/복구/알림은 아직 미구축. 월0원 범위에서 가능한 시험 환경만 진행한다. 원문 RPO/RTO/보존기간은 NEED_REVIEW 유지.

## READY/NEXT TASK

READY_FOR_LOCAL_DEVELOPMENT=YES. READY_FOR_STAGING_DEPLOYMENT=NO. READY_FOR_PRODUCTION=NO.
현재 인프라 Task는 계정 연결 이후 이어가야 하며, 운영 구축 완료로 표시하지 않는다.
