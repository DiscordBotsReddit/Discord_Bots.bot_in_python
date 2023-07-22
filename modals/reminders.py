from sqlalchemy import BigInteger, Identity, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    original_channel_id: Mapped[int] = mapped_column(BigInteger)
    timestamp_to_remind_at: Mapped[int] = mapped_column(Integer)
    timestamp_reminding_from: Mapped[int] = mapped_column(Integer)
    reminder: Mapped[str] = mapped_column(String(255))
