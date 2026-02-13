from typing import List, Dict, Any
from datetime import timedelta

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Avg, Max, Min

from .models import Patient, FormTemplate, FormResponse, ObservationValue


# ===== 공통 =====
def _get_active_intake_template() -> FormTemplate:
    return FormTemplate.objects.get(name="초진 문진", version=1, is_active=True)


def render_response_table(template, answers):
    schema = template.schema_json or {}
    fields = schema.get("fields", [])
    answers = answers or {}

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
            f"<th style='text-align:left;padding:6px 10px;border-bottom:1px solid #eee;white-space:nowrap'>{label}</th>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;'>{display}</td>"
            "</tr>"
        )

    return (
        "<div style='max-width:900px'>"
        "<table style='width:100%;border-collapse:collapse;background:#fff;border:1px solid #eee;"
        "border-radius:10px;overflow:hidden'>"
        + "".join(rows) +
        "</table></div>"
    )


# ===== 환자 입력 페이지 =====
def patient_intake(request: HttpRequest, patient_id: int) -> HttpResponse:
    patient = get_object_or_404(Patient, id=patient_id)
    template = _get_active_intake_template()

    schema = template.schema_json or {}
    fields = schema.get("fields", [])

    if request.method == "POST":
        responses: dict = {}
        for f in fields:
            key = f.get("key")
            ftype = f.get("type", "text")
            if not key:
                continue

            raw = request.POST.get(key, "").strip()

            if ftype == "number":
                if raw == "":
                    responses[key] = None
                else:
                    try:
                        responses[key] = int(raw) if raw.isdigit() else float(raw)
                    except Exception:
                        responses[key] = raw
            else:
                responses[key] = raw

        FormResponse.objects.create(
            template=template,
            template_version=template.version,
            patient=patient,
            encounter=None,
            source="patient",
            submitted_at=timezone.now(),
            responses_json=responses,
        )
        return redirect("patient_intake_done", patient_id=patient.id)

    return render(
        request,
        "clinic/patient_intake.html",
        {"patient": patient, "template": template, "fields": fields},
    )


def patient_intake_done(request: HttpRequest, patient_id: int) -> HttpResponse:
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, "clinic/patient_intake_done.html", {"patient": patient})


# ===== 타임라인 =====
def patient_timeline(request: HttpRequest, patient_id: int) -> HttpResponse:
    patient = get_object_or_404(Patient, id=patient_id)

    encounters = list(patient.encounters.all())
    attachments = list(patient.attachments.all())
    form_responses = list(patient.form_responses.select_related("template").all())

    items: List[Dict[str, Any]] = []

    for e in encounters:
        items.append({
            "type": "encounter",
            "dt": e.visited_at,
            "title": f"{e.visit_type} / {e.chief_complaint or '-'}",
            "obj": e,
        })

    for a in attachments:
        items.append({
            "type": "attachment",
            "dt": a.uploaded_at,
            "title": f"첨부: {a.tag or '파일'}",
            "obj": a,
        })

    for r in form_responses:
        items.append({
            "type": "form",
            "dt": r.submitted_at,
            "title": f"문진: {r.template.name} (source={r.source})",
            "rendered_html": render_response_table(r.template, r.responses_json),
        })

    items.sort(key=lambda x: x["dt"], reverse=True)

    return render(
        request,
        "clinic/patient_timeline.html",
        {"patient": patient, "items": items},
    )


# ===== 대시보드 =====
DASH_CODES = ["PAIN_SITE", "PAIN_NRS", "SLEEP_QUALITY", "URINE_COLOR", "STOOL"]


def patient_dashboard(request: HttpRequest, patient_id: int) -> HttpResponse:
    patient = get_object_or_404(Patient, id=patient_id)

    latest = {}
    for code in DASH_CODES:
        latest[code] = (
            ObservationValue.objects
            .filter(patient=patient, code=code)
            .order_by("-recorded_at")
            .first()
        )

    recent = (
        ObservationValue.objects
        .filter(patient=patient, code__in=DASH_CODES)
        .order_by("-recorded_at")[:30]
    )

    return render(
        request,
        "clinic/patient_dashboard.html",
        {"patient": patient, "latest": latest, "recent": recent},
    )


# ===== 추세 API (앱 배포 대비: JSON 반환) =====
def patient_trends_api(request: HttpRequest, patient_id: int) -> JsonResponse:
    patient = get_object_or_404(Patient, id=patient_id)

    now = timezone.now()
    start_7 = now - timedelta(days=7)
    start_14 = now - timedelta(days=14)

    metric_codes = ["PAIN_NRS", "SLEEP_QUALITY"]

    result = {
        "patient_id": patient.id,
        "patient_name": patient.full_name,
        "generated_at": now.isoformat(),
        "metrics": {},
    }

    for code in metric_codes:
        qs14 = ObservationValue.objects.filter(
            patient=patient, code=code, recorded_at__gte=start_14, value_num__isnull=False
        )
        qs7 = ObservationValue.objects.filter(
            patient=patient, code=code, recorded_at__gte=start_7, value_num__isnull=False
        )

        agg14 = qs14.aggregate(avg=Avg("value_num"))
        agg7 = qs7.aggregate(avg=Avg("value_num"), mx=Max("value_num"), mn=Min("value_num"))

        avg14 = agg14["avg"]
        avg7 = agg7["avg"]
        mx7 = agg7["mx"]
        mn7 = agg7["mn"]

        points = list(
            ObservationValue.objects.filter(patient=patient, code=code, value_num__isnull=False)
            .order_by("-recorded_at")
            .values("recorded_at", "value_num")[:30]
        )
        points = [{"t": p["recorded_at"].isoformat(), "v": p["value_num"]} for p in reversed(points)]

        result["metrics"][code] = {
            "avg7": float(avg7) if avg7 is not None else None,
            "avg14": float(avg14) if avg14 is not None else None,
            "delta_7_vs_14": (float(avg7 - avg14) if (avg7 is not None and avg14 is not None) else None),
            "max7": float(mx7) if mx7 is not None else None,
            "min7": float(mn7) if mn7 is not None else None,
            "count7": qs7.count(),
            "count14": qs14.count(),
            "series": points,
        }

    text_codes = ["PAIN_SITE", "URINE_COLOR", "STOOL"]
    for code in text_codes:
        recent = (
            ObservationValue.objects.filter(patient=patient, code=code)
            .order_by("-recorded_at")
            .first()
        )
        recent_value = None
        if recent:
            recent_value = recent.value_text if recent.value_text not in (None, "") else (
                str(recent.value_num) if recent.value_num is not None else None
            )

        qs_text = ObservationValue.objects.filter(patient=patient, code=code, recorded_at__gte=start_14)
        freq = {}
        for r in qs_text:
            val = r.value_text if r.value_text not in (None, "") else (str(r.value_num) if r.value_num is not None else "")
            if val == "":
                continue
            freq[val] = freq.get(val, 0) + 1
        top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]

        result["metrics"][code] = {
            "recent": recent_value,
            "top14": [{"value": k, "count": v} for k, v in top],
            "count14": qs_text.count(),
        }

    return JsonResponse(result, json_dumps_params={"ensure_ascii": False})
