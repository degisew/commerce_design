import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractBaseModel(models.Model):
    """
    Abstract base model that provides common fields for entity tracking
    across all inheriting models.

    Fields:
        id (UUID): Universally unique identifier for the record.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
        deleted_at (datetime, optional): Soft deletion marker. Indicates when the record was marked as deleted.

    Notes:
        - This model is intended to be inherited from and will not create its own database table.
        - The `deleted_at` field is useful for implementing soft deletes or audit logs.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("id"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("created at"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("updated at"),
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("deleted at"),
    )

    class Meta:
        abstract = True


class DataLookup(AbstractBaseModel):
    """
    A flexible key-value store used to manage static or semi-static data entries
    (e.g., statuses, types, account_states) across the application.

    This model allows storing metadata-driven choices that can be dynamically
    retrieved and filtered based on type, category, or other attributes.

    Attributes:
        type (str): A grouping identifier for the lookup item (e.g., "purchase_order_status").
        name (str): A human-readable label for the lookup entry.
        value (str): A unique internal value (e.g., "PENDING", "COMPLETE").
        description (str): Optional longer description of the lookup entry.
        category (str): Optional secondary grouping (e.g., "online", "offline").
        index (int): Controls display ordering of lookup items.
        is_default (bool): Marks this entry as the default option in its group.
        is_active (bool): Indicates if this entry is currently in use.
        remark (str): Optional notes for admin or internal reference.
    """

    type = models.CharField(max_length=200, verbose_name=_("Type"))

    name = models.CharField(max_length=200, verbose_name=_("Name"))

    value = models.CharField(unique=True, max_length=200, verbose_name=_("Value"))

    description = models.TextField(blank=True, verbose_name=_("Description"))

    category = models.CharField(max_length=200, blank=True, verbose_name=_("Category"))

    index = models.PositiveIntegerField(default=0, verbose_name=_("Index"))

    is_default = models.BooleanField(default=False, verbose_name=_("Is Default"))

    is_active = models.BooleanField(default=False, verbose_name=_("Is Active"))

    remark = models.TextField(blank=True, verbose_name=_("Remark"))

    class Meta:
        verbose_name = _("Data Lookup")
        verbose_name_plural = _("Data Lookups")
        db_table = "data_lookups"
        constraints = [
            # Constraint: Only one default value per type
            models.UniqueConstraint(
                fields=["type", "is_default"],
                condition=models.Q(is_default=True),
                name="data_lookups_type_is_default_idx",
            ),
            # Constraint: Unique index for each type
            models.UniqueConstraint(
                fields=["type", "index"], name="data_lookups_type_index_idx"
            ),
            # Constraint: Unique value across all types
            models.UniqueConstraint(fields=["value"], name="data_lookups_value_idx"),
        ]

    def __str__(self):
        return f"{self.type} :: {self.name}"
