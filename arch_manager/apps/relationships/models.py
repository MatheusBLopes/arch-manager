from django.db import models

from arch_manager.apps.resources.models import Resource


RELATIONSHIP_TYPE_CHOICES = [
    ("invokes", "Invokes"),
    ("publishes_to", "Publishes to"),
    ("subscribes_to", "Subscribes to"),
    ("reads_from", "Reads from"),
    ("writes_to", "Writes to"),
    ("persists_in", "Persists in"),
    ("consumes_from", "Consumes from"),
    ("exposes", "Exposes"),
    ("routes_to", "Routes to"),
    ("depends_on", "Depends on"),
    ("calls", "Calls"),
    ("triggers", "Triggers"),
    ("sends_to", "Sends to"),
    ("receives_from", "Receives from"),
]


class ResourceRelationship(models.Model):
    """Conexão explícita entre dois recursos."""

    source_resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    target_resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )
    relationship_type = models.CharField(
        max_length=50,
        choices=RELATIONSHIP_TYPE_CHOICES,
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["source_resource", "relationship_type", "target_resource"]
        verbose_name = "Relacionamento"
        verbose_name_plural = "Relacionamentos"

    def __str__(self):
        return f"{self.source_resource} --[{self.get_relationship_type_display()}]--> {self.target_resource}"
