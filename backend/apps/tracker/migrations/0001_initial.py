from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MetricDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=64, unique=True)),
                ('name', models.CharField(max_length=128)),
                ('input_type', models.CharField(choices=[('scale', 'Scale'), ('choice', 'Choice')], max_length=20)),
                ('min_value', models.IntegerField(blank=True, null=True)),
                ('max_value', models.IntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
            ],
            options={'ordering': ['sort_order', 'id']},
        ),
        migrations.CreateModel(
            name='DailyEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('note', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-date'], 'unique_together': {('user', 'date')}},
        ),
        migrations.CreateModel(
            name='MetricValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value_int', models.IntegerField(blank=True, null=True)),
                ('value_text', models.CharField(blank=True, max_length=255)),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metric_values', to='tracker.dailyentry')),
                ('metric', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metric_values', to='tracker.metricdefinition')),
            ],
            options={'unique_together': {('entry', 'metric')}},
        ),
    ]
