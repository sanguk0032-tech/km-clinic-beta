from django.contrib import admin
from .models import DailyEntry, MetricDefinition, MetricValue


@admin.register(MetricDefinition)
class MetricDefinitionAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'input_type', 'min_value', 'max_value', 'is_active', 'sort_order')
    list_editable = ('is_active', 'sort_order')
    search_fields = ('key', 'name')
    ordering = ('sort_order', 'id')


class MetricValueInline(admin.TabularInline):
    model = MetricValue
    extra = 0


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date')
    list_filter = ('date',)
    search_fields = ('user__username',)
    inlines = [MetricValueInline]
