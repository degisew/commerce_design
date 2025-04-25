from apps.core.models import AbstractBaseModel, DataLookup
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.account.managers import UserManager


class Role(AbstractBaseModel):
    name = models.CharField(max_length=50, verbose_name=_("Name"))

    code = models.CharField(max_length=50, verbose_name=_("Code"))

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        db_table = "roles"
        constraints = [
            # Constraint: Unique code
            models.UniqueConstraint(fields=["code"], name="roles_code_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class User(AbstractUser, AbstractBaseModel):
    email = models.EmailField(verbose_name=_("email address"), unique=True)

    role = models.ForeignKey(
        Role, null=True, blank=True, on_delete=models.RESTRICT, related_name="+"
    )

    state = models.ForeignKey(
        DataLookup,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="+",
        limit_choices_to={"type": "account_state_type"},
    )

    username = None
    first_name = None
    last_name = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name: str = _("user")
        verbose_name_plural: str = _("users")
        ordering = ("-created_at",)
        db_table: str = "users"

    def __str__(self) -> str:
        return self.email
