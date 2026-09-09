from zerocall.common.errors import ApplicationError


class AccountAlreadyExists(ApplicationError):
    code = "ACCOUNT_ALREADY_EXISTS"
    message = "이미 존재하는 계정 식별자입니다."
    status_code = 409


class AccountStorageUnavailable(ApplicationError):
    code = "ACCOUNT_STORAGE_UNAVAILABLE"
    message = "계정 정보를 처리하지 못했습니다."
    status_code = 503
