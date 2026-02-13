from django.db import models
from django.utils import timezone

from django.db.models.signals import post_save
from django.dispatch import receiver


class Patient(models.Model):
    full_name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    memo = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.full_name}"


class Encounter(models.Model):
    VISIT_TYPE_CHOICES = [
        ("초진", "초진"),
        ("재진", "재진"),
        ("기타", "기타"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="encounters")
    visited_at = models.DateTimeField(default=timezone.now)
    visit_type = models.CharField(max_length=10, choices=VISIT_TYPE_CHOICES, default="초진")

    chief_complaint = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True)

    is_finalized = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-visited_at"]

    def __str__(self) -> str:
        return f"{self.patient.full_name} / {self.visited_at:%Y-%m-%d %H:%M}"


class FormTemplate(models.Model):
    SCOPE_CHOICES = [
        ("patient", "환자 단위"),
        ("encounter", "내원 단위"),
    ]

    name = models.CharField(max_length=100)
    version = models.PositiveIntegerField(default=1)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default="encounter")
    description = models.TextField(blank=True)

    schema_json = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("name", "version")

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class FormResponse(models.Model):
    SOURCE_CHOICES = [
        ("staff", "원내 입력"),
        ("patient", "환자 입력"),
    ]

    template = models.ForeignKey(FormTemplate, on_delete=models.PROTECT, related_name="responses")
    template_version = models.PositiveIntegerField(default=1)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="form_responses")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.CASCADE, related_name="form_responses")

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="staff")
    submitted_at = models.DateTimeField(default=timezone.now)

    responses_json = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"{self.patient.full_name} / {self.template.name} v{self.template_version}"


class Attachment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="attachments")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.CASCADE, related_name="attachments")

    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    tag = models.CharField(max_length=50, blank=True)
    note = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"{self.patient.full_name} / {self.tag or 'attachment'}"


class ObservationValue(models.Model):
    SOURCE_CHOICES = [
        ("staff", "원내 입력"),
        ("patient", "환자 입력"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="observations")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.CASCADE, related_name="observations")

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="patient")

    code = models.CharField(max_length=50)      # PAIN_NRS, SLEEP_QUALITY 등
    label = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=20, blank=True)

    value_num = models.FloatField(null=True, blank=True)
    value_text = models.TextField(blank=True)

    recorded_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["patient", "code", "-recorded_at"])]
        ordering = ["-recorded_at"]

    def __str__(self) -> str:
        return f"{self.patient.full_name} / {self.code} / {self.recorded_at:%Y-%m-%d}"


# =========================
# ✅ 여기서부터가 핵심: 무조건 로드되는 post_save
# =========================

_MAPPING = [
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
def _create_obs_after_formresponse_save(sender, instance: FormResponse, created: bool, **kwargs):
    # 새로 생성될 때만(베타)
    if not created:
        return

    data = instance.responses_json or {}

    for json_key, code, label, unit, kind in _MAPPING:
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
