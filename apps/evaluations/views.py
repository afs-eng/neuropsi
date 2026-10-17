from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from apps.common.clinical_views import clinical_view
from apps.common.clinical_access import owned_patients, owned_evaluations
from apps.patients.models import Patient
from apps.evaluations.models import Evaluation
from apps.tests.models.instruments import Instrument
from apps.tests.models.applications import TestApplication


@clinical_view
def evaluation_list_view(request):
    evaluations = owned_evaluations(Evaluation.objects.select_related("patient", "examiner"), request.user).order_by(
        "-created_at"
    )
    data = [
        {
            "id": e.id,
            "patient_id": e.patient_id,
            "status": e.status,
            "created_at": e.created_at.isoformat()
            if getattr(e, "created_at", None)
            else None,
        }
        for e in evaluations
    ]
    return JsonResponse({"evaluations": data})


@clinical_view
def evaluation_create_view(request):
    patients = owned_patients(Patient.objects.all(), request.user)

    if request.method == "POST":
        patient_id = request.POST.get("patient")
        referral_reason = request.POST.get("referral_reason", "")
        evaluation_purpose = request.POST.get("evaluation_purpose", "")

        patient = get_object_or_404(owned_patients(Patient.objects.all(), request.user), pk=patient_id)

        evaluation = Evaluation.objects.create(
            patient=patient,
            examiner=request.user,
            referral_reason=referral_reason,
            evaluation_purpose=evaluation_purpose,
            status="collecting_data",
        )

        return JsonResponse({"id": evaluation.pk, "ok": True})

    return JsonResponse(
        {"patients": [{"id": p.id, "full_name": p.full_name} for p in patients]}
    )


@clinical_view
def evaluation_detail_view(request, pk):
    evaluation = get_object_or_404(owned_evaluations(Evaluation.objects.select_related("patient"), request.user), pk=pk)
    applications = TestApplication.objects.filter(evaluation=evaluation).select_related(
        "instrument"
    )

    instruments = Instrument.objects.filter(is_active=True)

    applied_codes = applications.values_list("instrument__code", flat=True)
    available_instruments = instruments.exclude(code__in=applied_codes)

    context = {
        "evaluation": evaluation,
        "applications": applications,
        "available_instruments": available_instruments,
    }
    apps_data = [
        {
            "id": a.id,
            "instrument": a.instrument.code if a.instrument else None,
            "applied_on": a.applied_on.isoformat() if a.applied_on else None,
        }
        for a in applications
    ]
    return JsonResponse(
        {
            "evaluation": {"id": evaluation.id, "patient_id": evaluation.patient_id},
            "applications": apps_data,
            "available_instruments": [i.code for i in available_instruments],
        }
    )
