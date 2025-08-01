import re
from typing import Dict, Any

import bcrypt

from domain.interfaces.services import PasswordServiceInterface


class BCryptPasswordService(PasswordServiceInterface):
    """
    Конкретная реализация сервиса работы с паролями использующая bcrypt.
    
    Реализует интерфейс из доменного слоя - правильное направление зависимостей.
    """
    
    def hash_password(self, password: str) -> str:
        """Хешировать пароль с помощью bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Проверить пароль против хеша"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_random_password(self, length: int = 12) -> str:
        """Сгенерировать случайный пароль"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Проверить силу пароля.
        
        Правила:
        - Минимум 8 символов
        - Содержит хотя бы одну заглавную букву
        - Содержит хотя бы одну строчную букву
        - Содержит хотя бы одну цифру
        - Содержит хотя бы один специальный символ
        """
        issues = []
        
        if len(password) < 8:
            issues.append("Пароль должен содержать минимум 8 символов")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Пароль должен содержать хотя бы одну заглавную букву")
        
        if not re.search(r'[a-z]', password):
            issues.append("Пароль должен содержать хотя бы одну строчную букву")
        
        if not re.search(r'\d', password):
            issues.append("Пароль должен содержать хотя бы одну цифру")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Пароль должен содержать хотя бы один специальный символ")
        
        return {
            "is_strong": len(issues) == 0,
            "issues": issues
        }