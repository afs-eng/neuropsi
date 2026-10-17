from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from apps.common.clinical_views import clinical_view
from apps.common.clinical_access import owned_patients, owned_evaluations, owned_evaluation_children
from apps.patients.models import Patient
from apps.evaluations.models import Evaluation


@clinical_view
def dashboard_view(request):
    patients_qs = owned_patients(Patient.objects.all(), request.user)[:5]
    evaluations_qs = owned_evaluations(Evaluation.objects.select_related("patient"), request.user).order_by(
        "-created_at"
    )[:5]

    recent_patients = [{"id": p.id, "full_name": p.full_name} for p in patients_qs]
    recent_evaluations = [
        {
            "id": e.id,
            "patient_id": e.patient_id,
            "status": e.status,
            "created_at": e.created_at.isoformat()
            if getattr(e, "created_at", None)
            else None,
        }
        for e in evaluations_qs
    ]

    context = {
        "total_patients": owned_patients(Patient.objects.all(), request.user).count(),
        "active_evaluations": owned_evaluations(Evaluation.objects.all(), request.user).filter(
            status__in=["draft", "collecting_data"]
        ).count(),
        "tests_applied": 0,
        "pending_reports": 0,
        "recent_patients": recent_patients,
        "recent_evaluations": recent_evaluations,
    }
    return JsonResponse(context)


@clinical_view
def patient_list_view(request):
    patients = owned_patients(Patient.objects.all(), request.user)
    data = [
        {
            "id": p.id,
            "full_name": p.full_name,
            "birth_date": p.birth_date.isoformat() if p.birth_date else None,
        }
        for p in patients
    ]
    return JsonResponse({"patients": data})


@clinical_view
def patient_detail_view(request, pk):
    patient = get_object_or_404(owned_patients(Patient.objects.all(), request.user), pk=pk)
    from apps.tests.models.applications import TestApplication

    test_applications = (
        owned_evaluation_children(TestApplication.objects.all(), request.user).filter(evaluation__patient=patient)
        .select_related("instrument", "evaluation")
        .order_by("-applied_on", "-created_at")
    )
    apps_data = [
        {
            "id": app.id,
            "instrument": app.instrument.code if app.instrument else None,
            "is_validated": app.is_validated,
            "applied_on": app.applied_on.isoformat() if app.applied_on else None,
        }
        for app in test_applications
    ]

    patient_data = {
        "id": patient.id,
        "full_name": patient.full_name,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
    }

    return JsonResponse({"patient": patient_data, "test_applications": apps_data})


@clinical_view
def patient_create_view(request):
    if request.method == "POST":
        patient = Patient.objects.create(
            created_by=request.user,
            full_name=request.POST.get("full_name"),
            birth_date=request.POST.get("birth_date") or None,
            sex=request.POST.get("sex", ""),
            schooling=request.POST.get("schooling", ""),
            school_name=request.POST.get("school_name", ""),
            phone=request.POST.get("phone", ""),
            email=request.POST.get("email", ""),
            mother_name=request.POST.get("mother_name", ""),
            father_name=request.POST.get("father_name", ""),
            city=request.POST.get("city", ""),
            state=request.POST.get("state", ""),
            notes=request.POST.get("notes", ""),
        )
        return JsonResponse({"id": patient.id, "ok": True})
    return JsonResponse({"error": "method not allowed"}, status=405)


@clinical_view
def patient_edit_view(request, pk):
    patient = get_object_or_404(owned_patients(Patient.objects.all(), request.user), pk=pk)
    if request.method == "POST":
        patient.full_name = request.POST.get("full_name", patient.full_name)
        patient.birth_date = request.POST.get("birth_date") or None
        patient.sex = request.POST.get("sex", "")
        patient.schooling = request.POST.get("schooling", "")
        patient.school_name = request.POST.get("school_name", "")
        patient.phone = request.POST.get("phone", "")
        patient.email = request.POST.get("email", "")
        patient.mother_name = request.POST.get("mother_name", "")
        patient.father_name = request.POST.get("father_name", "")
        patient.city = request.POST.get("city", "")
        patient.state = request.POST.get("state", "")
        patient.notes = request.POST.get("notes", "")
        patient.save()
        return JsonResponse({"id": patient.id, "ok": True})
    patient_data = {
        "id": patient.id,
        "full_name": patient.full_name,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
    }
    return JsonResponse({"patient": patient_data})
