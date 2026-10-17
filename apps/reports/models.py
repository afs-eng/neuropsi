from django.conf import settings
from django.db import models
from apps.evaluations.models import Evaluation
from apps.patients.models import Patient


class ReportTemplate(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="report_templates"
    )
    name = models.CharField(max_length=255)
    instrument_code = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]


class ReportTemplateVersion(models.Model):
    template = models.ForeignKey(
        ReportTemplate, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    # Armazenamento privado: não publica DOCX clínico no MEDIA_URL.
    document = models.BinaryField(editable=False)
    sha256 = models.CharField(max_length=64)
    original_filename = models.CharField(max_length=255)
    validation_payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["template", "version_number"], name="unique_report_template_version"
            )
        ]


class ReportQuerySet(models.QuerySet):
    def with_details(self):
        return self.select_related("evaluation", "patient", "author").prefetch_related(
            "sections", "versions"
        )


class ReportStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    GENERATING = "generating", "Gerando texto..."
    IN_REVIEW = "in_review", "Em revisão"
    FINALIZED = "finalized", "Finalizado"
    SENT = "sent", "Enviado ao paciente"


class Report(models.Model):
    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name="avaliação",
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name="paciente",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reports",
        verbose_name="autor",
    )

    title = models.CharField("título", max_length=255, default="Laudo Neuropsicológico")
    interested_party = models.CharField("interessado", max_length=255, blank=True)
    purpose = models.TextField("finalidade", blank=True)
    status = models.CharField(
        "status",
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.DRAFT,
    )

    # Snapshot dos dados usados para gerar (garante imutabilidade se os testes mudarem depois)
    context_payload = models.JSONField("contexto clínico", default=dict, blank=True)

    # Texto consolidado (Markdown)
    generated_text = models.TextField("texto gerado pela IA", blank=True)
    edited_text = models.TextField("texto editado", blank=True)
    final_text = models.TextField("texto finalizado", blank=True)
    ai_metadata = models.JSONField("metadados de IA", default=dict, blank=True)

    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)
    generated_at = models.DateTimeField("gerado em", null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Laudo"
        verbose_name_plural = "Laudos"

    objects = ReportQuerySet.as_manager()

    def __str__(self):
        return f"{self.title} - {self.patient.full_name}"


class ReportSection(models.Model):
    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="sections", verbose_name="laudo"
    )
    key = models.CharField(
        "chave da seção", max_length=100
    )  # ex: 'anamnese', 'atencao'
    title = models.CharField("título da seção", max_length=255)
    order = models.PositiveIntegerField("ordem", default=0)

    content_generated = models.TextField("conteúdo IA", blank=True)
    content_edited = models.TextField("conteúdo editado", blank=True)
    generation_metadata = models.JSONField(
        "metadados da geracao", default=dict, blank=True
    )
    warnings_payload = models.JSONField("avisos da geracao", default=list, blank=True)

    is_locked = models.BooleanField("bloqueado para edição", default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("report", "key")
        verbose_name = "Seção de laudo"
        verbose_name_plural = "Seções de laudo"


class ReportVersion(models.Model):
    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="versions", verbose_name="laudo"
    )
    version_number = models.PositiveIntegerField("versão")
    content = models.TextField("conteúdo")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="criado por",
    )
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        verbose_name = "Versão de laudo"
        verbose_name_plural = "Versões de laudo"


class SpecialistRun(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Na fila"
        RUNNING = "running", "Em processamento"
        NEEDS_REVIEW = "needs_review", "Aguardando revisão profissional"
        FAILED = "failed", "Falhou"
        STALE = "stale", "Resultados alterados"

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="specialist_runs")
    application = models.ForeignKey("tests.TestApplication", on_delete=models.CASCADE)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    instrument_code = models.CharField(max_length=50)
    specialist_version = models.CharField(max_length=50)
    source_sha256 = models.CharField(max_length=64)
    input_payload = models.JSONField(default=dict)
    model_name = models.CharField(max_length=255)
    provider_base_url = models.URLField(max_length=500)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    output_payload = models.JSONField(default=dict)
    usage_payload = models.JSONField(default=dict)
    error_code = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["status", "created_at"], name="specialist_queue_idx")]
        constraints = [models.UniqueConstraint(
            fields=["report", "application", "source_sha256", "specialist_version", "model_name", "provider_base_url"],
            name="unique_specialist_source_run",
        )]
