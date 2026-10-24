"""
Работа с базой данных
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import List, Optional

from tg_LogicPulse_bot.database.models import Base, Task, TeamTask
from tg_LogicPulse_bot.config.settings import DB_PATH


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.engine = None
        self.async_session = None
    
    async def init(self):
        """Инициализация базы данных"""
        # Используем aiosqlite для асинхронной работы с SQLite
        database_url = f"sqlite+aiosqlite:///{self.db_path}"
        self.engine = create_async_engine(
            database_url,
            echo=False,
            future=True,
            pool_pre_ping=True  # Проверка соединения перед использованием
        )
        
        # Создаем таблицы
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Создаем сессию
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,  # Автоматическая синхронизация
            autocommit=False
        )
    
    async def close(self):
        """Закрытие соединения с БД"""
        if self.engine:
            await self.engine.dispose()
    
    async def add_task(
        self,
        user_id: int,
        title: str,
        city: str,
        date: str,
        time: str,
        datetime_obj: datetime
    ) -> Task:
        """Добавить задачу с гарантированным сохранением"""
        async with self.async_session() as session:
            try:
                task = Task(
                    user_id=int(user_id),
                    title=str(title),
                    city=str(city),
                    date=str(date),
                    time=str(time),
                    datetime_obj=datetime_obj,
                    is_completed=False
                )
                session.add(task)
                await session.flush()
                task_id = task.id
                
                await session.commit()
                
                # Проверяем сохранение
                async with self.async_session() as verify_session:
                    from sqlalchemy import select
                    verify_query = select(Task).where(Task.id == task_id)
                    verify_result = await verify_session.execute(verify_query)
                    verified_task = verify_result.scalar_one_or_none()
                    
                    if not verified_task:
                        raise Exception(f"Задача с ID {task_id} не найдена после сохранения")
                    
                    return verified_task
                    
            except Exception as e:
                await session.rollback()
                raise
    
    async def get_user_tasks(
        self,
        user_id: int,
        completed: Optional[bool] = None
    ) -> List[Task]:
        """
        Получить задачи пользователя

        ``completed=False`` возвращает активные задачи, а ``completed=True`` —
        сохранённую историю завершённых.
        """
        async with self.async_session() as session:
            from sqlalchemy import select
            
            query = select(Task).where(Task.user_id == user_id)
            
            if completed is not None:
                query = query.where(Task.is_completed == completed)
            
            query = query.order_by(Task.datetime_obj.asc())
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def get_task_by_id(self, task_id: int, user_id: int) -> Optional[Task]:
        """Получить задачу по ID"""
        async with self.async_session() as session:
            from sqlalchemy import select
            
            query = select(Task).where(
                Task.id == task_id,
                Task.user_id == user_id
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def complete_task(self, task_id: int, user_id: int) -> bool:
        """Отметить задачу как выполненную с гарантированным сохранением"""
        async with self.async_session() as session:
            from sqlalchemy import select
            
            query = select(Task).where(
                Task.id == task_id,
                Task.user_id == user_id
            )
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            
            if task:
                task.is_completed = True
                await session.commit()
                await session.flush()
                return True
            return False
    
    async def delete_task(self, task_id: int, user_id: int) -> bool:
        """Удалить задачу с гарантированным сохранением"""
        async with self.async_session() as session:
            from sqlalchemy import select
            
            query = select(Task).where(
                Task.id == task_id,
                Task.user_id == user_id
            )
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            
            if task:
                await session.delete(task)
                await session.commit()
                await session.flush()
                return True
            return False
    
    async def get_upcoming_tasks(self, current_datetime: datetime) -> List[Task]:
        """Получить предстоящие задачи для напоминаний"""
        async with self.async_session() as session:
            from sqlalchemy import select
            
            query = select(Task).where(
                Task.datetime_obj >= current_datetime,
                Task.is_completed == False
            )
            result = await session.execute(query)
            return list(result.scalars().all())

    async def add_team_task(
        self,
        text: str,
        author_name: str,
        author_id: Optional[int],
    ) -> TeamTask:
        """Добавить общую командную задачу."""
        async with self.async_session() as session:
            task = TeamTask(
                text=text,
                author_name=author_name,
                author_id=author_id,
                status="open",
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    async def get_team_tasks(
        self,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 8,
    ) -> List[TeamTask]:
        """Получить страницу командных задач."""
        from sqlalchemy import select

        async with self.async_session() as session:
            query = select(TeamTask)
            if status is not None:
                query = query.where(TeamTask.status == status)
            query = query.order_by(TeamTask.created_at.desc(), TeamTask.id.desc())
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def count_team_tasks(self, status: Optional[str] = None) -> int:
        """Посчитать командные задачи для меню и пагинации."""
        from sqlalchemy import func, select

        async with self.async_session() as session:
            query = select(func.count(TeamTask.id))
            if status is not None:
                query = query.where(TeamTask.status == status)
            result = await session.execute(query)
            return int(result.scalar_one())

    async def get_team_tasks_by_author(
        self,
        author_name: str,
        limit: int = 20,
    ) -> List[TeamTask]:
        """Найти командные задачи по точному имени автора."""
        from sqlalchemy import select

        async with self.async_session() as session:
            query = (
                select(TeamTask)
                .where(TeamTask.author_name == author_name)
                .order_by(TeamTask.created_at.desc(), TeamTask.id.desc())
                .limit(limit)
            )
            result = await session.execute(query)
            return list(result.scalars().all())

    async def complete_team_task(self, task_id: int) -> bool:
        """Перенести командную задачу в завершённые."""
        from sqlalchemy import select

        async with self.async_session() as session:
            result = await session.execute(
                select(TeamTask).where(TeamTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            if task is None:
                return False
            task.status = "done"
            task.completed_at = datetime.now()
            await session.commit()
            return True

    async def delete_team_task(self, task_id: int) -> bool:
        """Удалить командную задачу."""
        from sqlalchemy import select

        async with self.async_session() as session:
            result = await session.execute(
                select(TeamTask).where(TeamTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            if task is None:
                return False
            await session.delete(task)
            await session.commit()
            return True

    async def migrate_legacy_team_tasks(self, legacy_db_path: Path) -> int:
        """Однократно импортировать задачи из старого бота TgLP3.

        Связка ``source + legacy_id`` защищает от дублей при перезапусках.
        Если путь не существует или схема отличается, импорт просто пропускается.
        """
        legacy_path = Path(legacy_db_path).resolve()
        current_path = Path(self.db_path).resolve()
        if not legacy_path.exists() or legacy_path == current_path:
            return 0

        try:
            connection = sqlite3.connect(
                f"file:{legacy_path.as_posix()}?mode=ro",
                uri=True,
            )
            try:
                columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
                }
                required = {"id", "text", "user", "created_at", "status"}
                if not required.issubset(columns):
                    return 0
                rows = connection.execute(
                    "SELECT id, text, user, created_at, status FROM tasks ORDER BY id"
                ).fetchall()
            finally:
                connection.close()
        except sqlite3.Error:
            return 0

        if not rows:
            return 0

        from sqlalchemy import select

        imported = 0
        async with self.async_session() as session:
            existing_result = await session.execute(
                select(TeamTask.legacy_id).where(TeamTask.source == "tglp3")
            )
            existing_ids = set(existing_result.scalars().all())

            for legacy_id, text, author, created_at, status in rows:
                if legacy_id in existing_ids:
                    continue
                try:
                    parsed_created_at = datetime.fromisoformat(created_at)
                except (TypeError, ValueError):
                    parsed_created_at = datetime.now()
                session.add(
                    TeamTask(
                        text=str(text),
                        author_name=str(author),
                        author_id=None,
                        status="done" if status == "done" else "open",
                        created_at=parsed_created_at,
                        completed_at=(
                            parsed_created_at if status == "done" else None
                        ),
                        source="tglp3",
                        legacy_id=int(legacy_id),
                    )
                )
                imported += 1

            if imported:
                await session.commit()
        return imported


# Глобальный экземпляр базы данных
db = Database()
