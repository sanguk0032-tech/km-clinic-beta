from django.urls import path
from .views import EntryUpsertView, MetricListView, TodayEntryView, TrendView

urlpatterns = [
    path('metrics/', MetricListView.as_view(), name='metrics-list'),
    path('entries/today/', TodayEntryView.as_view(), name='entries-today'),
    path('entries/upsert/', EntryUpsertView.as_view(), name='entries-upsert'),
    path('entries/trend/', TrendView.as_view(), name='entries-trend'),
]
