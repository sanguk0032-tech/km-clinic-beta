from django.conf import settings
from django.db import models


class MetricDefinition(models.Model):
    INPUT_SCALE = 'scale'
    INPUT_CHOICE = 'choice'
    INPUT_TYPES = [
        (INPUT_SCALE, 'Scale'),
        (INPUT_CHOICE, 'Choice'),
    ]

    key = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    input_type = models.CharField(max_length=20, choices=INPUT_TYPES)
    min_value = models.IntegerField(null=True, blank=True)
    max_value = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.name


class DailyEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_entries')
    date = models.DateField()
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self) -> str:
        return f'{self.user.username} - {self.date}'


class MetricValue(models.Model):
    entry = models.ForeignKey(DailyEntry, on_delete=models.CASCADE, related_name='metric_values')
    metric = models.ForeignKey(MetricDefinition, on_delete=models.CASCADE, related_name='metric_values')
    value_int = models.IntegerField(null=True, blank=True)
    value_text = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('entry', 'metric')

    def __str__(self) -> str:
        return f'{self.entry} / {self.metric.key}'
