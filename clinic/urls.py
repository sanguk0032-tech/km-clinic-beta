from django.urls import path
from . import views

urlpatterns = [
    path("healthz/", views.healthz, name="healthz"),
    path("p/<int:patient_id>/intake/", views.patient_intake, name="patient_intake"),
    path("p/<int:patient_id>/intake/done/", views.patient_intake_done, name="patient_intake_done"),
    path("timeline/<int:patient_id>/", views.patient_timeline, name="patient_timeline"),  
    path("dashboard/<int:patient_id>/", views.patient_dashboard, name="patient_dashboard"),
    path("api/trends/<int:patient_id>/", views.patient_trends_api, name="patient_trends_api"),
]

