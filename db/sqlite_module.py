import csv
from datetime import datetime, timedelta

# SQLAlchemy импорты для моделей, запросов, асинхронной работы
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, select, delete, desc, update
from sqlalchemy.sql import func

# ===============================
# Настройка подключения к SQLite
# ===============================

# Путь к SQLite-файлу
DATABASE_URL = "sqlite+aiosqlite:///./db.sqlite3"

# Асинхронный движок базы данных
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика асинхронных сессий
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Базовый класс для ORM-моделей
Base = declarative_base()

# ===============================
# Модели таблиц
# ===============================

# Таблица с последними ценами
class PriceEntry(Base):
    __tablename__ = "price_entries"

    id = Column(Integer, primary_key=True)
    exchange = Column(String, index=True)        # Название биржи
    symbol = Column(String, index=True)          # Символ (валютная пара)
    last_price = Column(Float)                   # Последняя цена
    volume = Column(Float)                       # Объём
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # Дата обновления

# Таблица с логами алертов
class StrategyAlert(Base):
    __tablename__ = "strategy_alerts"

    id = Column(Integer, primary_key=True)
    strategy = Column(String)                    # Название стратегии
    exchange = Column(String)                    # Биржа
    symbol = Column(String)                      # Валютная пара
    old_price = Column(Float)                    # Предыдущая цена
    new_price = Column(Float)                    # Новая цена
    volume = Column(Float)                       # Объём на момент алерта
    created_at = Column(DateTime, server_default=func.now())  # Время создания алерта

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    strategy = Column(String)              # Название стратегии (если применимо)
    exchange = Column(String)              # Биржа
    symbol = Column(String)                # Валютная пара
    order_type = Column(String)            # Тип ордера: market/limit
    side = Column(String)                  # buy/sell
    amount = Column(Float)                 # Количество
    price = Column(Float, nullable=True)   # Цена (для лимитных ордеров)
    status = Column(String)                # Статус: open/closed/canceled
    order_id = Column(String)              # ID ордера на бирже
    created_at = Column(DateTime, server_default=func.now())  # Время создания

# ===============================
# Слой доступа к данным (DAL)
# ===============================

class DBManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    # Получить последнюю сохранённую цену по паре и бирже
    async def get_last_price(self, exchange: str, symbol: str) -> float | None:
        stmt = select(PriceEntry).where(
            PriceEntry.exchange == exchange,
            PriceEntry.symbol == symbol
        )
        result = await self.session.execute(stmt)
        entry = result.scalars().first()
        return entry.last_price if entry else None

    # Сохранить (или обновить) текущую цену и объём
    async def save_price(self, exchange: str, symbol: str, price: float, volume: float):
        stmt = select(PriceEntry).where(
            PriceEntry.exchange == exchange,
            PriceEntry.symbol == symbol
        )
        result = await self.session.execute(stmt)
        entry = result.scalars().first()

        if entry:
            # Обновляем запись
            entry.last_price = price
            entry.volume = volume
        else:
            # Добавляем новую
            entry = PriceEntry(exchange=exchange, symbol=symbol, last_price=price, volume=volume)
            self.session.add(entry)

        await self.session.commit()

    # Записать алерт стратегии в лог
    async def log_alert(self, strategy: str, exchange: str, symbol: str, old: float, new: float, volume: float):
        alert = StrategyAlert(
            strategy=strategy,
            exchange=exchange,
            symbol=symbol,
            old_price=old,
            new_price=new,
            volume=volume,
        )
        self.session.add(alert)
        await self.session.commit()

    # Удалить алерты старше N дней
    async def delete_old_alerts(self, days: int = 7) -> int:
        """Удаляет алерты старше N дней. Возвращает количество удалённых записей."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            delete(StrategyAlert).where(StrategyAlert.created_at < cutoff_date)
        )
        await self.session.commit()
        return result.rowcount

    # Получить алерты постранично, начиная с самых новых
    async def get_alerts_paginated(self, page: int = 1, page_size: int = 20) -> list[StrategyAlert]:
        """Возвращает алерты постранично (от новых к старым)."""
        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(StrategyAlert)
            .order_by(desc(StrategyAlert.created_at))
            .offset(offset)
            .limit(page_size)
        )
        return result.scalars().all()

    # Экспорт всех алертов в CSV-файл
    async def export_alerts_to_csv(self, filename: str = "alerts_export.csv") -> None:
        """Экспортирует все алерты в CSV-файл."""
        result = await self.session.execute(
            select(StrategyAlert).order_by(StrategyAlert.created_at)
        )
        alerts = result.scalars().all()

        with open(filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Заголовки CSV
            writer.writerow([
                "id", "strategy", "exchange", "symbol",
                "old_price", "new_price", "volume", "created_at"
            ])
            # Строки
            for alert in alerts:
                writer.writerow([
                    alert.id,
                    alert.strategy,
                    alert.exchange,
                    alert.symbol,
                    alert.old_price,
                    alert.new_price,
                    alert.volume,
                    alert.created_at
                ])

    # Создать новый ордер
    async def create_order(self, strategy: str, exchange: str, symbol: str, order_type: str,
                           side: str, amount: float, price: float = None,
                           status: str = "open", order_id: str = None,
                           created_at: datetime = None):
        order = Order(
            strategy=strategy,
            exchange=exchange,
            symbol=symbol,
            order_type=order_type,
            side=side,
            amount=amount,
            price=price,
            status=status,
            order_id=order_id,
            created_at=created_at or datetime.utcnow()
        )
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    # Обновить статус ордера по id
    async def update_order_status(self, order_id: int, new_status: str):
        stmt = update(Order).where(Order.id == order_id).values(status=new_status)
        await self.session.execute(stmt)
        await self.session.commit()

    # Получить ордер по id
    async def get_order_by_id(self, order_id: int):
        stmt = select(Order).where(Order.id == order_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    # Получить все ордера по фильтрам (например, по бирже, символу, статусу)
    async def get_orders(self, exchange: str = None, symbol: str = None, status: str = None, limit: int = 50):
        stmt = select(Order).order_by(desc(Order.created_at)).limit(limit)
        if exchange:
            stmt = stmt.where(Order.exchange == exchange)
        if symbol:
            stmt = stmt.where(Order.symbol == symbol)
        if status:
            stmt = stmt.where(Order.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # Удалить все ордера из таблицы
    async def delete_all_orders(self) -> int:
        """Удаляет все записи из таблицы orders. Возвращает количество удалённых ордеров."""
        result = await self.session.execute(delete(Order))
        await self.session.commit()
        return result.rowcount



# ===============================
# Инициализация БД (создание таблиц)
# ===============================

async def init_db():
    """Создаёт все таблицы в базе данных, если они ещё не существуют."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
