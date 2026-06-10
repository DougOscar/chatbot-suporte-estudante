"""Base declarativa do SQLAlchemy.

Mantida em módulo separado para que ``migrations/env.py`` possa importar
``Base`` sem puxar a engine (que tem efeitos colaterais de configuração).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
