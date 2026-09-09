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
