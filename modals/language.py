from sqlalchemy import BigInteger, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Language(Base):
    __tablename__ = "languages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(Text)
    role_id: Mapped[int] = mapped_column(BigInteger)

    def __repr__(self) -> str:
        return super().__repr__()
