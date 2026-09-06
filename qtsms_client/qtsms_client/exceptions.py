"""
Custom exceptions for QTSMS Client.
"""

from typing import Optional, Dict, Any


class QTSMSException(Exception):
    """Base exception for QTSMS client."""

    pass


class QTSMSValidationError(QTSMSException):
    """Raised when action parameters fail validation."""

    pass


class QTSMSRequestError(QTSMSException):
    """Raised when a request to the SMS gateway fails."""

    def __init__(self, message: str, status_code: int = None, response: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class QTSMSAuthError(QTSMSException):
    """Raised when authentication fails."""

    pass


class QTMSErrorCode:
    """
    Error codes from Beeline A2P SMS Gateway API.
    
    Based on official documentation: https://a2p-sms.beeline.ru/support/manuals/https
    """
    
    # Authentication errors
    AUTH_ERROR = 20107
    AUTH_ERROR_MESSAGE = "Ошибка авторизации (или 'В доступе отказано')"
    
    # Phone number errors
    INVALID_PHONE = 20117
    INVALID_PHONE_MESSAGE = "Неправильный номер телефона: {phone}"
    
    # Service/product errors
    SERVICE_UNAVAILABLE = 20148
    SERVICE_UNAVAILABLE_MESSAGE = "Невозможно предоставить услуги для продукта '{product_id}:{phone}:1'"
    
    # Transport/Database errors
    TRANSPORT_ERROR = 20154
    TRANSPORT_ERROR_MESSAGE = "Ошибка транспорта: '{sqlcode}:{ord_id}:{sqlerrm}'"
    
    # Blacklist errors
    BLACKLISTED = 20158
    BLACKLISTED_MESSAGE = "Отправка невозможна, так как номер '{phone}' занесён в чёрный список"
    
    # Duplicate message errors
    DUPLICATE_MESSAGE = 20167
    DUPLICATE_MESSAGE_MESSAGE = "Запрещено посылать сообщение с тем же текстом тому же адресату ({phone}) в течение {minutes} минут"
    
    # Message length errors
    MESSAGE_TOO_LONG = 20170
    MESSAGE_TOO_LONG_MESSAGE = "Слишком длинное сообщение"
    
    # Censorship errors
    CENSORSHIP_FAILED = 20171
    CENSORSHIP_FAILED_MESSAGE = "Сообщение не прошло проверку цензуры '{message}'; Имя отправителя: '{sender}'"
    
    # Request errors
    INVALID_REQUEST = 20200
    INVALID_REQUEST_MESSAGE = "invalid request (Неправильный запрос)"
    
    # Inbox errors
    INBOX_NOT_FOUND = 20202
    INBOX_NOT_FOUND_MESSAGE = "No inbox found (Не найден почтовый ящик для входящих сообщений)"
    
    # Target/Group errors
    TARGET_OR_GROUP_REQUIRED = 20203
    TARGET_OR_GROUP_REQUIRED_MESSAGE = "target or phl_codename should be specified (Нет номера телефона или идентификатора группы в запросе)"
    
    GROUP_NO_PHONES = 20204
    GROUP_NO_PHONES_MESSAGE = "No phone numbers for group (Не найдены телефоны для группы)"
    
    # Date errors
    DATE_FORMAT_INVALID = 20207
    DATE_FORMAT_INVALID_MESSAGE = "Date_to format is invalid. Should be (Неправильный формат даты)"
    
    DATE_RANGE_WRONG = 20208
    DATE_RANGE_WRONG_MESSAGE = "Wrong date range - date_to < date_from (Дата начала позже даты конца)"
    
    # Empty params
    EMPTY_PARAMS = 20209
    EMPTY_PARAMS_MESSAGE = "Request params is empty (Параметры запроса пустые)"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = 20211
    RATE_LIMIT_EXCEEDED_MESSAGE = "Too high messages rate for user (Превышено количество сообщений для пользователя)"
    
    DATE_RANGE_TOO_BIG = 20212
    DATE_RANGE_TOO_BIG_MESSAGE = "Too big dates range (Превышен интервал в выбранных датах)"
    
    INVALID_PHONES = 20213
    INVALID_PHONES_MESSAGE = "Invalid phone numbers in your request (Невалидные номера в списке)"
    
    MULTIPLE_TARGETS_FORBIDDEN = 20218
    MULTIPLE_TARGETS_FORBIDDEN_MESSAGE = "Multiple targets are not allowed (Запрещено отправлять на несколько адресов)"
    
    # Sender approval errors
    SENDER_NOT_APPROVED = 20230
    SENDER_NOT_APPROVED_MESSAGE = "Отправитель {sender} не одобрен на стороне оператора {operator}. Абонент: {phone}"
    
    # Limit errors
    DAILY_LIMIT_REACHED = 20280
    DAILY_LIMIT_REACHED_MESSAGE = "Достигнут суточный лимит на отправку SMS с платформы A2P"
    
    MONTHLY_LIMIT_REACHED = 20281
    MONTHLY_LIMIT_REACHED_MESSAGE = "Достигнут месячный лимит на отправку SMS с платформы A2P"
    
    @classmethod
    def get_error_message(cls, code: int, **kwargs) -> str:
        """
        Get human-readable error message for an error code.
        
        Args:
            code: Error code from API
            **kwargs: Parameters for formatting the message
            
        Returns:
            Formatted error message
        """
        error_map = {
            cls.AUTH_ERROR: cls.AUTH_ERROR_MESSAGE,
            cls.INVALID_PHONE: cls.INVALID_PHONE_MESSAGE,
            cls.SERVICE_UNAVAILABLE: cls.SERVICE_UNAVAILABLE_MESSAGE,
            cls.TRANSPORT_ERROR: cls.TRANSPORT_ERROR_MESSAGE,
            cls.BLACKLISTED: cls.BLACKLISTED_MESSAGE,
            cls.DUPLICATE_MESSAGE: cls.DUPLICATE_MESSAGE_MESSAGE,
            cls.MESSAGE_TOO_LONG: cls.MESSAGE_TOO_LONG_MESSAGE,
            cls.CENSORSHIP_FAILED: cls.CENSORSHIP_FAILED_MESSAGE,
            cls.INVALID_REQUEST: cls.INVALID_REQUEST_MESSAGE,
            cls.INBOX_NOT_FOUND: cls.INBOX_NOT_FOUND_MESSAGE,
            cls.TARGET_OR_GROUP_REQUIRED: cls.TARGET_OR_GROUP_REQUIRED_MESSAGE,
            cls.GROUP_NO_PHONES: cls.GROUP_NO_PHONES_MESSAGE,
            cls.DATE_FORMAT_INVALID: cls.DATE_FORMAT_INVALID_MESSAGE,
            cls.DATE_RANGE_WRONG: cls.DATE_RANGE_WRONG_MESSAGE,
            cls.EMPTY_PARAMS: cls.EMPTY_PARAMS_MESSAGE,
            cls.RATE_LIMIT_EXCEEDED: cls.RATE_LIMIT_EXCEEDED_MESSAGE,
            cls.DATE_RANGE_TOO_BIG: cls.DATE_RANGE_TOO_BIG_MESSAGE,
            cls.INVALID_PHONES: cls.INVALID_PHONES_MESSAGE,
            cls.MULTIPLE_TARGETS_FORBIDDEN: cls.MULTIPLE_TARGETS_FORBIDDEN_MESSAGE,
            cls.SENDER_NOT_APPROVED: cls.SENDER_NOT_APPROVED_MESSAGE,
            cls.DAILY_LIMIT_REACHED: cls.DAILY_LIMIT_REACHED_MESSAGE,
            cls.MONTHLY_LIMIT_REACHED: cls.MONTHLY_LIMIT_REACHED_MESSAGE,
        }
        
        message = error_map.get(code, f"Unknown error code: {code}")
        
        # Format message with provided kwargs
        try:
            return message.format(**kwargs)
        except (KeyError, ValueError):
            return message
    
    @classmethod
    def get_all_errors(cls) -> Dict[int, str]:
        """Get all error codes with their descriptions."""
        return {
            cls.AUTH_ERROR: cls.AUTH_ERROR_MESSAGE,
            cls.INVALID_PHONE: cls.INVALID_PHONE_MESSAGE,
            cls.SERVICE_UNAVAILABLE: cls.SERVICE_UNAVAILABLE_MESSAGE,
            cls.TRANSPORT_ERROR: cls.TRANSPORT_ERROR_MESSAGE,
            cls.BLACKLISTED: cls.BLACKLISTED_MESSAGE,
            cls.DUPLICATE_MESSAGE: cls.DUPLICATE_MESSAGE_MESSAGE,
            cls.MESSAGE_TOO_LONG: cls.MESSAGE_TOO_LONG_MESSAGE,
            cls.CENSORSHIP_FAILED: cls.CENSORSHIP_FAILED_MESSAGE,
            cls.INVALID_REQUEST: cls.INVALID_REQUEST_MESSAGE,
            cls.INBOX_NOT_FOUND: cls.INBOX_NOT_FOUND_MESSAGE,
            cls.TARGET_OR_GROUP_REQUIRED: cls.TARGET_OR_GROUP_REQUIRED_MESSAGE,
            cls.GROUP_NO_PHONES: cls.GROUP_NO_PHONES_MESSAGE,
            cls.DATE_FORMAT_INVALID: cls.DATE_FORMAT_INVALID_MESSAGE,
            cls.DATE_RANGE_WRONG: cls.DATE_RANGE_WRONG_MESSAGE,
            cls.EMPTY_PARAMS: cls.EMPTY_PARAMS_MESSAGE,
            cls.RATE_LIMIT_EXCEEDED: cls.RATE_LIMIT_EXCEEDED_MESSAGE,
            cls.DATE_RANGE_TOO_BIG: cls.DATE_RANGE_TOO_BIG_MESSAGE,
            cls.INVALID_PHONES: cls.INVALID_PHONES_MESSAGE,
            cls.MULTIPLE_TARGETS_FORBIDDEN: cls.MULTIPLE_TARGETS_FORBIDDEN_MESSAGE,
            cls.SENDER_NOT_APPROVED: cls.SENDER_NOT_APPROVED_MESSAGE,
            cls.DAILY_LIMIT_REACHED: cls.DAILY_LIMIT_REACHED_MESSAGE,
            cls.MONTHLY_LIMIT_REACHED: cls.MONTHLY_LIMIT_REACHED_MESSAGE,
        }


class QTMSParseResponseError(QTSMSException):
    """Raised when parsing API response fails."""
    
    def __init__(self, message: str, raw_response: str = None):
        super().__init__(message)
        self.raw_response = raw_response
