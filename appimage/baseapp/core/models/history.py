import datetime as dt
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords


class HistoryModel(models.Model):
    """Base model with UUIDs, timestamps, and no-op history suppression."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True

    @property
    def is_new(self):
        return self._state.adding

    @property
    def short_id(self):
        return str(self.id).split("-")[0]

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            update_fields = set(update_fields)
            kwargs["update_fields"] = update_fields

        self._validate_choice_fields()

        force_update = kwargs.get("force_update")

        if self._state.adding or kwargs.get("force_insert"):
            super().save(*args, **kwargs)
            return

        orig = self.__class__.objects.get(pk=self.pk)
        self._restore_sticky_fields(orig)

        has_changes, has_last_found_change = self._compare_field_values(
            orig, update_fields
        )

        if not has_changes:
            if has_last_found_change:
                self.__class__.objects.filter(id=self.id).update(
                    last_found=getattr(self, "last_found")
                )
                return
            if force_update:
                self._save_with_update_field_snapshot(orig, update_fields, args, kwargs)
            return

        self._save_with_update_field_snapshot(orig, update_fields, args, kwargs)

    def _save_with_update_field_snapshot(self, orig, update_fields, args, kwargs):
        if update_fields is None:
            super().save(*args, **kwargs)
            return

        excluded_values = self._restore_excluded_update_fields(orig, update_fields)
        try:
            super().save(*args, **kwargs)
        finally:
            for field_name, value in excluded_values.items():
                setattr(self, field_name, value)

    def get_change_url(self):
        return reverse(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
            args=(self.pk,),
        )

    def _validate_choice_fields(self):
        errors = {}
        for field in self.__class__._meta.fields:
            if not getattr(field, "choices", None):
                continue

            value = getattr(self, field.name)
            if value is None:
                continue

            try:
                field.validate(value, self)
            except ValidationError as exc:
                errors[field.name] = exc.error_list

        if errors:
            raise ValidationError(errors)

    def _restore_sticky_fields(self, orig):
        for field_name in getattr(self.__class__, "_sticky_fields", ()):
            setattr(self, field_name, getattr(orig, field_name))

    def _compare_field_values(self, orig, update_fields=None):
        has_changes = False
        has_last_found_change = False

        for field in self.__class__._meta.fields:
            if update_fields is not None and not self._field_in_update_fields(
                field, update_fields
            ):
                continue

            original_value = getattr(orig, field.attname)
            new_value = getattr(self, field.attname)

            if field.name == "last_found" and original_value != new_value:
                has_last_found_change = True
                continue

            original_value, new_value = self._normalize_comparable_values(
                original_value, new_value
            )
            if original_value != new_value:
                has_changes = True
                break

        return has_changes, has_last_found_change

    def _field_in_update_fields(self, field, update_fields):
        return field.name in update_fields or field.attname in update_fields

    def _restore_excluded_update_fields(self, orig, update_fields):
        excluded_values = {}

        for field in self.__class__._meta.fields:
            if self._field_in_update_fields(field, update_fields):
                continue

            excluded_values[field.attname] = getattr(self, field.attname)
            setattr(self, field.attname, getattr(orig, field.attname))

        return excluded_values

    def _normalize_comparable_values(self, original_value, new_value):
        if isinstance(original_value, dt.datetime) and isinstance(
            new_value, dt.datetime
        ):
            if timezone.is_aware(original_value):
                original_value = timezone.localtime(original_value)
            if timezone.is_aware(new_value):
                new_value = timezone.localtime(new_value)

        if (
            isinstance(original_value, dt.date)
            and not isinstance(original_value, dt.datetime)
            and isinstance(new_value, dt.datetime)
        ):
            new_value = new_value.date()

        return original_value, new_value
