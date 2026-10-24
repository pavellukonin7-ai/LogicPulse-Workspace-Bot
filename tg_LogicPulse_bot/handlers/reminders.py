"""
Система напоминаний
"""
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot

from database.database import db


class ReminderScheduler:
    """Планировщик напоминаний"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.running = False
        self.sent_reminders = set()  # Множество ID задач, которым уже отправили напоминание
    
    async def start(self):
        """Запуск планировщика"""
        self.running = True
        asyncio.create_task(self._scheduler_loop())
    
    async def stop(self):
        """Остановка планировщика"""
        self.running = False
    
    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        while self.running:
            try:
                await self._check_and_send_reminders()
                # Проверяем каждую минуту
                await asyncio.sleep(60)
            except Exception as e:
                print(f"Ошибка в планировщике: {e}")
                await asyncio.sleep(60)
    
    async def _check_and_send_reminders(self):
        """Проверка и отправка напоминаний"""
        now = datetime.now()
        # Проверяем задачи в ближайшие 2 минуты
        future_time = now + timedelta(minutes=2)
        
        tasks = await db.get_upcoming_tasks(now)
        
        for task in tasks:
            # Проверяем, нужно ли отправить напоминание
            time_diff = (task.datetime_obj - now).total_seconds()
            
            # Отправляем напоминание за 5 минут до события или в момент события
            # И только если еще не отправляли
            if 0 <= time_diff <= 300 and task.id not in self.sent_reminders:  # 5 минут = 300 секунд
                await self._send_reminder(task)
                self.sent_reminders.add(task.id)
            
            # Удаляем из множества задачи, время которых уже прошло
            elif time_diff < 0:
                self.sent_reminders.discard(task.id)
    
    async def _send_reminder(self, task):
        """Отправка напоминания"""
        try:
            reminder_text = (
                "🔔 <b>Напоминание о задаче!</b>\n\n"
                f"📝 <b>{task.title}</b>\n"
                f"🏙 <b>Город:</b> {task.city}\n"
                f"📅 <b>Дата:</b> {task.date}\n"
                f"⏰ <b>Время:</b> {task.time}\n\n"
                "Не забудьте выполнить задачу!"
            )
            
            await self.bot.send_message(
                chat_id=task.user_id,
                text=reminder_text,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка при отправке напоминания: {e}")

