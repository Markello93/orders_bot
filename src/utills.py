import re


def validate_phone(value: str) -> str:
    # Разрешенные символы: цифры, +, -, (, )
    pattern = r"^[\d\+\-\(\)]{1,}$"
    if re.match(pattern, value):
        return value
    raise ValueError(
        "Некорректный номер телефона. Допустимы только цифры и символы +, -, (, )."
    )
