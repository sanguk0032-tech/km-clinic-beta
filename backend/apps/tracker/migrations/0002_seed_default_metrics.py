from django.db import migrations


def create_default_metrics(apps, schema_editor):
    MetricDefinition = apps.get_model('tracker', 'MetricDefinition')

    defaults = [
        {'key': 'sleep_quality', 'name': '수면의 질', 'input_type': 'scale', 'min_value': 0, 'max_value': 10, 'sort_order': 1},
        {'key': 'fatigue', 'name': '피로감', 'input_type': 'scale', 'min_value': 0, 'max_value': 10, 'sort_order': 2},
        {'key': 'stress', 'name': '스트레스', 'input_type': 'scale', 'min_value': 0, 'max_value': 10, 'sort_order': 3},
        {'key': 'digestion', 'name': '소화 상태', 'input_type': 'scale', 'min_value': 0, 'max_value': 10, 'sort_order': 4},
        {'key': 'bowel', 'name': '대변 상태', 'input_type': 'choice', 'min_value': None, 'max_value': None, 'sort_order': 5},
    ]

    for item in defaults:
        MetricDefinition.objects.update_or_create(key=item['key'], defaults=item)


def reverse_default_metrics(apps, schema_editor):
    MetricDefinition = apps.get_model('tracker', 'MetricDefinition')
    MetricDefinition.objects.filter(key__in=['sleep_quality', 'fatigue', 'stress', 'digestion', 'bowel']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_metrics, reverse_default_metrics),
    ]
