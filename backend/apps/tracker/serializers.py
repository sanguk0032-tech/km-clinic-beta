from rest_framework import serializers
from .models import DailyEntry, MetricDefinition, MetricValue


class MetricDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricDefinition
        fields = ['id', 'key', 'name', 'input_type', 'min_value', 'max_value', 'is_active', 'sort_order']


class MetricValueSerializer(serializers.ModelSerializer):
    metric_key = serializers.CharField(source='metric.key', read_only=True)

    class Meta:
        model = MetricValue
        fields = ['metric_key', 'value_int', 'value_text']


class DailyEntrySerializer(serializers.ModelSerializer):
    metric_values = MetricValueSerializer(many=True, read_only=True)

    class Meta:
        model = DailyEntry
        fields = ['id', 'date', 'note', 'metric_values']


class MetricInputSerializer(serializers.Serializer):
    metric_key = serializers.CharField()
    value_int = serializers.IntegerField(required=False, allow_null=True)
    value_text = serializers.CharField(required=False, allow_blank=True)


class DailyEntryUpsertSerializer(serializers.Serializer):
    date = serializers.DateField()
    note = serializers.CharField(required=False, allow_blank=True)
    values = MetricInputSerializer(many=True)
