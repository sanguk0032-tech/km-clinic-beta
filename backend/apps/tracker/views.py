from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DailyEntry, MetricDefinition, MetricValue
from .serializers import DailyEntrySerializer, DailyEntryUpsertSerializer, MetricDefinitionSerializer


class MetricListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        metrics = MetricDefinition.objects.filter(is_active=True).order_by('sort_order', 'id')
        return Response(MetricDefinitionSerializer(metrics, many=True).data)


class TodayEntryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        entry, _ = DailyEntry.objects.get_or_create(user=request.user, date=today)
        return Response(DailyEntrySerializer(entry).data)


class EntryUpsertView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = DailyEntryUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        entry, _ = DailyEntry.objects.update_or_create(
            user=request.user,
            date=payload['date'],
            defaults={'note': payload.get('note', '')},
        )

        metric_map = {m.key: m for m in MetricDefinition.objects.filter(is_active=True)}
        for item in payload['values']:
            metric_key = item['metric_key']
            metric = metric_map.get(metric_key)
            if not metric:
                continue

            value_int = item.get('value_int')
            value_text = item.get('value_text', '')

            if metric.input_type == MetricDefinition.INPUT_SCALE:
                if value_int is None:
                    continue
                if metric.min_value is not None and value_int < metric.min_value:
                    continue
                if metric.max_value is not None and value_int > metric.max_value:
                    continue

            MetricValue.objects.update_or_create(
                entry=entry,
                metric=metric,
                defaults={
                    'value_int': value_int if metric.input_type == MetricDefinition.INPUT_SCALE else None,
                    'value_text': value_text if metric.input_type == MetricDefinition.INPUT_CHOICE else '',
                },
            )

        entry.refresh_from_db()
        return Response(DailyEntrySerializer(entry).data, status=status.HTTP_200_OK)


class TrendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        metric_key = request.query_params.get('metric_key')
        days = int(request.query_params.get('days', '30'))
        if days not in (7, 30, 90):
            days = 30

        metric = MetricDefinition.objects.filter(key=metric_key, is_active=True).first()
        if not metric:
            return Response({'detail': 'Invalid metric_key'}, status=status.HTTP_400_BAD_REQUEST)

        start_date = timezone.localdate() - timedelta(days=days - 1)
        values = (
            MetricValue.objects.filter(
                entry__user=request.user,
                entry__date__gte=start_date,
                metric=metric,
            )
            .select_related('entry')
            .order_by('entry__date')
        )

        points = []
        for mv in values:
            points.append({
                'date': mv.entry.date.isoformat(),
                'value': mv.value_int if metric.input_type == MetricDefinition.INPUT_SCALE else mv.value_text,
            })

        return Response({'metric_key': metric_key, 'days': days, 'points': points})
