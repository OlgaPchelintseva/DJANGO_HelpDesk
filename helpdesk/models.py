from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Client(models.Model):
    name = models.CharField(max_length=150, verbose_name='ФИО клиента')
    email = models.EmailField(unique=True, db_index=True, verbose_name='Email клиента')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Номер телефона')
    company = models.CharField(max_length=150, blank=True, verbose_name='Название компании')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return self.name

class Ticket(models.Model):
    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        NORMAL = 'normal', 'Нормальный' 
        HIGH = 'high', 'Высокий'
        CRITICAL = 'critical', 'Критичный'

    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        IN_PROGRESS = 'in_progress', 'В процессе'
        WAITING = 'waiting', 'Ожидание'
        CLOSED = 'closed', 'Закрытый'

    external_id = models.CharField(max_length=30, unique=True, verbose_name='ID из старой CRM')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='tickets', verbose_name='Клиент')
    subject = models.CharField(max_length=200, verbose_name='Тема заявки')
    description = models.TextField(blank=True, verbose_name='Подробное описание')
    priority = models.CharField(choices=Priority.choices, default=Priority.NORMAL, verbose_name='Уровень приоритета')
    status = models.CharField(choices=Status.choices, default=Status.NEW, verbose_name='Статус задачи')
    assignee = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tickets', verbose_name='Исполнитель')
    created_at = models.DateTimeField(verbose_name='Дата создания заявки')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата закрытия заявки')

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'assignee'], name='ticket_status_assignee_idx')]

    def __str__(self):
        return f'#{self.external_id} {self.subject}'

    def save(self, *args, **kwargs):
        if self.status == self.Status.CLOSED and not self.closed_at:
            self.closed_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.priority != self.Priority.CRITICAL or self.status == self.Status.CLOSED or not self.created_at:
            return False
        return (timezone.now() - self.created_at) > timedelta(hours=12)

class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments', verbose_name='Задача')
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, verbose_name='Автор комментария')
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания комментария')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Список комментариев'
        ordering = ['-created_at']

    def __str__(self):
        return self.text[:50]

class ImportLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, verbose_name='Менеджер, загрузивший файл')
    file_name = models.CharField(max_length=255, verbose_name='Имя загруженного файла')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки файла')
    total_rows = models.PositiveIntegerField(verbose_name='Всего строк в файле')
    created_count = models.PositiveIntegerField(verbose_name='Количество созданных заявок')
    updated_count = models.PositiveIntegerField(verbose_name='Количество обновленных заявок')
    skipped_count = models.PositiveIntegerField(verbose_name='Количество пропущенных строк')
    errors = models.JSONField(default=list, verbose_name='Список строк с описанием ошибок')

    class Meta:
        verbose_name = 'Журнал импортов'
        verbose_name_plural = 'Журналы импортов'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.file_name} - {self.uploaded_at:%Y-%m-%d %H:%M}'

