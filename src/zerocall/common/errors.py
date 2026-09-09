class ApplicationError(Exception):
    code = "INTERNAL_SERVER_ERROR"
    message = "요청을 처리하지 못했습니다."
    status_code = 500


class ResourceNotFound(ApplicationError):
    code = "RESOURCE_NOT_FOUND"
    message = "요청한 정보를 찾을 수 없습니다."
    status_code = 404


class ValidationFailed(ApplicationError):
    code = "VALIDATION_FAILED"
    message = "입력값을 확인해 주세요."
    status_code = 422


class Unauthorized(ApplicationError):
    code = "UNAUTHORIZED"
    message = "인증이 필요합니다."
    status_code = 401


class Forbidden(ApplicationError):
    code = "FORBIDDEN"
    message = "접근 권한이 없습니다."
    status_code = 403


class RateLimitExceeded(ApplicationError):
    code = "RATE_LIMIT_EXCEEDED"
    message = "요청이 많습니다. 잠시 후 다시 시도해 주세요."
    status_code = 429
