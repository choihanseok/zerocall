# 배포 준비 및 0원 예산 경계

Task ZC-TASK-20260910-004. 사용자가 신규 계정/서버를 요청했고 월 예산을 0원으로 지정했다. 유료 자원·결제수단·유료 플랜을 생성하지 않는다. 현재 서버/클라우드 DB는 생성되지 않았다. Docker 패키지와 PostgreSQL CI 검증은 인프라 프로비저닝 완료를 의미하지 않는다.

## 현재 가능한 구성

- 기존 LOCAL/DEV/TEST SQLite 유지.
- loopback PostgreSQL 전용 시험 DB에서 기존 Migration과 저장 로직을 검증한다.
- STAGING/PRODUCTION 설정은 PostgreSQL+psycopg와 TLS verify-full/sslrootcert가 있어야 통과한다. 구성 유효성은 운영 준비 승인이 아니다.
- Docker는 비관리자 UID 10001로 실행하고 소스/의존성/Migration만 포함한다. Secret과 원문자료는 build context에서 제외한다.
- 시작 시 Migration을 실행하지 않는다. 별도 migration 계정으로 먼저 실행하고 runtime에는 DDL 권한을 주지 않는다.
- 앱 포트8000은 HTTPS를 종료하는 플랫폼/reverse proxy 뒤에서만 노출한다. TLS 인증서·방화벽·서비스 접근제한은 실제 플랫폼에서 구성해야 한다.

## 환경별 분리 요구

스테이징: 별도 app/DB/runtime user/migration user/Secret, 합성 데이터만 사용, 접근제한.
운영: 별도 app/DB/runtime user/migration user/Secret, 최소권한, 비공개 DB 네트워크, HTTPS, 백업 및 복구 시험, 모니터링/알림.
동일 DB 연결 문자열을 두 환경에 재사용하지 않는다. staging으로 운영 데이터를 복사하지 않는다.

실제 플랫폼 Secret 설정(아래 값은 설명용이며 실제 credential 아님):

```text
ZC_ENVIRONMENT=STAGING 또는 PRODUCTION
ZC_DATABASE_URL=postgresql+psycopg://<runtime-user>:<encoded-password>@<db-host>/<database>?sslmode=verify-full&sslrootcert=system
```

플랫폼에서 사설 CA를 쓰면 sslrootcert에 읽기 전용으로 마운트한 CA 파일 경로를 사용한다. 검증을 끄는 sslmode=require/disable로 우회하지 않는다. [PostgreSQL TLS 문서](https://www.postgresql.org/docs/current/libpq-ssl.html) 참조.

## 배포 절차

1. 무료 계정 연결과 명시적인 free 플랜·결제수단 없음·과금 차단 상태 확인.
2. 별도 DB 및 사용자/접근권한을 만들고 TLS 연결 검증.
3. 신규 빈 DB임을 확인하거나 기존 DB 백업/복구 계획을 확인.
4. 동일 release의 Docker image로 별도 migration 작업: python -m alembic upgrade head.
5. runtime Secret으로 앱 실행, HTTPS health 확인, 인증/업무 API가 의도치 않게 노출되지 않는지 확인.
6. 재시작 후 영속성, 백업 복구, 오류 알림, 환경 간 격리 검증.
7. 배포 commit/image digest와 실제 검증 결과를 기록한 뒤 readiness 판정.

## 무료 서비스 제한 확인

[Render 무료 서비스 공식 문서](https://render.com/docs/free)는 무료 웹 서버의 유휴 중단과 무료 PostgreSQL의 30일 만료·백업 미제공을 명시한다. 이 DB를 운영 DB로 사용하거나 두 환경의 영구 저장소로 간주하지 않는다. 실제 무료 hosting/DB 계정 연결이 없는 현재는 외부 URL을 발급하지 않았다. 무료 시험 환경 구성 이후에도 운영 요건 충족 여부를 별도로 판단한다.

## 아직 미완료

클라우드 가입/본인확인, 서버·DB 생성, TLS 실제 연결, runtime/migration 권한 분리 실증, HTTPS/네트워크 제한, 백업·복구, 운영 RPO/RTO·보존기간 확정. READY_FOR_STAGING_DEPLOYMENT=NO, READY_FOR_PRODUCTION=NO.
