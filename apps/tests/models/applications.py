from django.db import models

from apps.evaluations.models import Evaluation
from apps.tests.models.instruments import Instrument


class TestApplicationQuerySet(models.QuerySet):
    def with_details(self):
        return self.select_related("evaluation", "evaluation__patient", "instrument")


class TestApplication(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        COMPLETED = "completed", "Aplicação concluída"
        SCORED = "scored", "Corrigido"
        INTERPRETED = "interpreted", "Interpretação gerada"
        REVIEWED = "reviewed", "Revisado"
        LOCKED = "locked", "Travado"

    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="test_applications",
        verbose_name="avaliação",
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.PROTECT,
        related_name="applications",
        verbose_name="instrumento",
    )
    applied_on = models.DateField("data de aplicação", null=True, blank=True)

    raw_payload = models.JSONField("dados brutos", default=dict, blank=True)
    computed_payload = models.JSONField("dados calculados", default=dict, blank=True)
    classified_payload = models.JSONField("dados classificados", default=dict, blank=True)
    reviewed_payload = models.JSONField("dados revisados", default=dict, blank=True)

    interpretation_text = models.TextField("interpretação", blank=True)

    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    is_validated = models.BooleanField("validado", default=False)

    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Aplicação de teste"
        verbose_name_plural = "Aplicações de teste"

    objects = TestApplicationQuerySet.as_manager()

    def _derived_status(self) -> str:
        if self.status == self.Status.LOCKED:
            return self.Status.LOCKED
        if self.is_validated:
            return self.Status.REVIEWED
        if (self.interpretation_text or "").strip():
            return self.Status.INTERPRETED
        if self.classified_payload or self.computed_payload:
            return self.Status.SCORED
        if self.raw_payload or self.reviewed_payload or self.applied_on:
            return self.Status.COMPLETED
        return self.Status.DRAFT

    def sync_workflow_state(self):
        self.status = self._derived_status()

    def save(self, *args, **kwargs):
        self.sync_workflow_state()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"status"}
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.evaluation.patient.full_name} - {self.instrument.code}"
