from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FormResponse, ObservationValue


# FormResponse.responses_json 에서 뽑을 key -> ObservationValue.code 매핑
MAPPING = [
    # (json_key, code, label, unit, kind)
    ("pain_site", "PAIN_SITE", "통증 부위", "", "text"),
    ("pain_nrs", "PAIN_NRS", "통증 NRS", "NRS", "num"),
    ("sleep_quality", "SLEEP_QUALITY", "수면 질", "score", "num"),
    ("urine_color", "URINE_COLOR", "소변 색", "", "text"),
    ("stool", "STOOL", "대변 상태", "", "text"),
]


def _to_float(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


@receiver(post_save, sender=FormResponse)
def create_observations_from_form(sender, instance: FormResponse, created: bool, **kwargs):
    """
    FormResponse가 새로 생성될 때(created=True),
    핵심 지표를 ObservationValue로 자동 저장합니다.
    """
    if not created:
        return

    data = instance.responses_json or {}

    for json_key, code, label, unit, kind in MAPPING:
        val = data.get(json_key)
        if val in (None, ""):
            continue

        obs = ObservationValue(
            patient=instance.patient,
            encounter=instance.encounter,
            source=instance.source,
            code=code,
            label=label,
            unit=unit,
            recorded_at=instance.submitted_at,
        )

        if kind == "num":
            obs.value_num = _to_float(val)
            if obs.value_num is None:
                obs.value_text = str(val)
        else:
            obs.value_text = str(val)

        obs.save()
