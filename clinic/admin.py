import json

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    Patient,
    Encounter,
    FormTemplate,
    FormResponse,
    Attachment,
    ObservationValue,
)


# =========================
# Inline 설정
# =========================

class EncounterInline(admin.TabularInline):
    model = Encounter
    extra = 0
    fields = ("visited_at", "visit_type", "chief_complaint", "is_finalized")
    show_change_link = True


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    fields = ("tag", "file", "uploaded_at")
    readonly_fields = ("uploaded_at",)
    show_change_link = True


class FormResponseInline(admin.TabularInline):
    model = FormResponse
    extra = 0
    fields = ("template", "source", "submitted_at")
    readonly_fields = ("submitted_at",)
    show_change_link = True


# =========================
# Patient
# =========================

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "birth_date", "sex", "phone", "created_at")
    search_fields = ("full_name", "phone")
    list_filter = ("sex",)
    ordering = ("-created_at",)
    inlines = [EncounterInline, AttachmentInline, FormResponseInline]


# =========================
# Encounter
# =========================

@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "visited_at", "visit_type", "is_finalized")
    search_fields = ("patient__full_name", "chief_complaint", "note")
    list_filter = ("visit_type", "is_finalized")
    ordering = ("-visited_at",)


# =========================
# FormTemplate
# =========================

@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "version", "scope", "is_active", "updated_at")
    search_fields = ("name",)
    list_filter = ("scope", "is_active")
    ordering = ("-updated_at",)


# =========================
# FormResponse (읽기 쉽게 표시)
# =========================

@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "template",
        "source",
        "submitted_at",
        "pain_nrs",
        "sleep_quality",
        "quick_summary",
    )
    list_filter = ("source", "template")
    search_fields = ("patient__full_name",)
    ordering = ("-submitted_at",)

    readonly_fields = ("readable_view", "pretty_json_view")

    fieldsets = (
        ("기본 정보", {
            "fields": ("template", "template_version", "patient", "encounter", "source", "submitted_at")
        }),
        ("읽기 쉬운 문진 보기", {
            "fields": ("readable_view",),
        }),
        ("원본 JSON", {
            "fields": ("pretty_json_view", "responses_json"),
        }),
    )

    # 숫자 추출 helper
    def _get_num(self, obj, key):
        try:
            v = (obj.responses_json or {}).get(key)
            if v in (None, ""):
                return None
            return float(v)
        except Exception:
            return None

    @admin.display(description="통증 NRS")
    def pain_nrs(self, obj):
        v = self._get_num(obj, "pain_nrs")
        return "-" if v is None else v

    @admin.display(description="수면 질")
    def sleep_quality(self, obj):
        v = self._get_num(obj, "sleep_quality")
        return "-" if v is None else v

    @admin.display(description="요약")
    def quick_summary(self, obj):
        d = obj.responses_json or {}
        parts = []
        if d.get("pain_site"):
            parts.append(f"{d.get('pain_site')}")
        if d.get("pain_nrs") not in (None, ""):
            parts.append(f"NRS {d.get('pain_nrs')}")
        if d.get("sleep_quality") not in (None, ""):
            parts.append(f"수면 {d.get('sleep_quality')}")
        if d.get("urine_color"):
            parts.append(f"소변 {d.get('urine_color')}")
        if d.get("stool"):
            parts.append(f"대변 {d.get('stool')}")

        return " / ".join(parts) if parts else "-"

    @admin.display(description="정리된 문진 보기")
    def readable_view(self, obj):
        template = obj.template
        schema = template.schema_json or {}
        fields = schema.get("fields", [])
        answers = obj.responses_json or {}

        rows = []
        for f in fields:
            key = f.get("key")
            label = f.get("label", key)
            unit = f.get("unit")

            if not key:
                continue

            val = answers.get(key)
            if val in (None, ""):
                display = "-"
            else:
                display = str(val)
                if unit:
                    display = f"{display} {unit}"

            rows.append(
                "<tr>"
                f"<th style='text-align:left;padding:6px 10px;border-bottom:1px solid #eee;'>{label}</th>"
                f"<td style='padding:6px 10px;border-bottom:1px solid #eee;'>{display}</td>"
                "</tr>"
            )

        return mark_safe(
            "<table style='width:100%;border-collapse:collapse'>"
            + "".join(rows)
            + "</table>"
        )

    @admin.display(description="JSON 보기")
    def pretty_json_view(self, obj):
        try:
            pretty = json.dumps(obj.responses_json or {}, ensure_ascii=False, indent=2)
        except Exception:
            pretty = str(obj.responses_json)
        return format_html("<pre>{}</pre>", pretty)


# =========================
# Attachment
# =========================

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "tag", "uploaded_at")
    list_filter = ("tag",)
    ordering = ("-uploaded_at",)


# =========================
# ObservationValue
# =========================

@admin.register(ObservationValue)
class ObservationValueAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "code", "value_num", "value_text", "unit", "recorded_at", "source")
    list_filter = ("code", "source")
    search_fields = ("patient__full_name",)
    ordering = ("-recorded_at",)
