import datetime as dt
import uuid

from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered, NotRegistered
from django.core.exceptions import ValidationError
from django.db import connection, models
from django.test import TransactionTestCase, override_settings
from django.urls import clear_url_caches, path, reverse
from django.utils import timezone

from core.models import HistoryModel

urlpatterns = []


class ExampleHistoryModel(HistoryModel):
    _sticky_fields = ("sticky_code",)

    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"
    CATEGORY_GENERAL = "general"
    CATEGORY_SPECIAL = "special"

    name = models.CharField(max_length=64)
    status = models.CharField(
        max_length=16,
        choices=((STATUS_ACTIVE, "Active"), (STATUS_ARCHIVED, "Archived")),
        default=STATUS_ACTIVE,
    )
    grouped_category = models.CharField(
        max_length=16,
        choices=(
            ("Standard", ((CATEGORY_GENERAL, "General"),)),
            ("Featured", ((CATEGORY_SPECIAL, "Special"),)),
        ),
        default=CATEGORY_GENERAL,
    )
    sticky_code = models.CharField(max_length=32, default="fixed")
    last_found = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"


class ExampleParentModel(HistoryModel):
    name = models.CharField(max_length=64)

    class Meta:
        app_label = "core"


class ExampleChildModel(HistoryModel):
    name = models.CharField(max_length=64)
    parent = models.ForeignKey(ExampleParentModel, on_delete=models.CASCADE)

    class Meta:
        app_label = "core"


@override_settings(ROOT_URLCONF=__name__)
class HistoryModelTests(TransactionTestCase):
    _created_model_tables = []
    _created_history_tables = []
    _registered_admin = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            existing_tables = set(connection.introspection.table_names())
            with connection.schema_editor() as schema_editor:
                for model in (
                    ExampleHistoryModel,
                    ExampleParentModel,
                    ExampleChildModel,
                ):
                    if model._meta.db_table not in existing_tables:
                        schema_editor.create_model(model)
                        cls._created_model_tables.append(model)
                for model in (
                    ExampleHistoryModel.history.model,
                    ExampleParentModel.history.model,
                    ExampleChildModel.history.model,
                ):
                    if model._meta.db_table not in existing_tables:
                        schema_editor.create_model(model)
                        cls._created_history_tables.append(model)
            try:
                admin.site.register(ExampleHistoryModel)
                cls._registered_admin = True
            except AlreadyRegistered:
                pass
            cls._refresh_urlpatterns()
        except Exception:
            cls._cleanup_dynamic_model()
            raise

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_dynamic_model()
        super().tearDownClass()

    @classmethod
    def _cleanup_dynamic_model(cls):
        if cls._registered_admin:
            try:
                admin.site.unregister(ExampleHistoryModel)
            except NotRegistered:
                pass
            cls._registered_admin = False
            cls._refresh_urlpatterns()

        with connection.schema_editor() as schema_editor:
            for model in reversed(cls._created_history_tables):
                schema_editor.delete_model(model)
            cls._created_history_tables = []
            for model in reversed(cls._created_model_tables):
                schema_editor.delete_model(model)
            cls._created_model_tables = []

    @classmethod
    def _refresh_urlpatterns(cls):
        global urlpatterns

        urlpatterns = [path("admin/", admin.site.urls)]
        clear_url_caches()

    def test_create_sets_uuid_timestamps_short_id_and_history(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")

        self.assertIsInstance(obj.id, uuid.UUID)
        self.assertFalse(obj.is_new)
        self.assertEqual(obj.short_id, str(obj.id).split("-")[0])
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.modified_at)
        self.assertEqual(obj.history.count(), 1)

    def test_unchanged_save_does_not_create_history_row(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")

        obj.save()

        self.assertEqual(obj.history.count(), 1)

    def test_force_update_on_unchanged_save_creates_history_row(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")

        obj.save(force_update=True)

        self.assertEqual(obj.history.count(), 2)

    def test_changed_save_creates_history_row(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")

        obj.name = "Beta"
        obj.save()

        self.assertEqual(obj.history.count(), 2)

    def test_sticky_field_is_restored_on_existing_save(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha", sticky_code="original")

        obj.name = "Beta"
        obj.sticky_code = "changed"
        obj.save()

        obj.refresh_from_db()
        self.assertEqual(obj.name, "Beta")
        self.assertEqual(obj.sticky_code, "original")

    def test_force_update_restores_sticky_field(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha", sticky_code="original")

        obj.name = "Beta"
        obj.sticky_code = "changed"
        obj.save(force_update=True)

        obj.refresh_from_db()
        history = obj.history.latest()
        self.assertEqual(obj.name, "Beta")
        self.assertEqual(obj.sticky_code, "original")
        self.assertEqual(history.name, "Beta")
        self.assertEqual(history.sticky_code, "original")

    def test_invalid_choice_raises_validation_error(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")
        obj.status = "wrong"

        with self.assertRaises(ValidationError):
            obj.save()

    def test_grouped_choice_validation_uses_django_field_validation(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")

        obj.grouped_category = ExampleHistoryModel.CATEGORY_SPECIAL
        obj.save()

        obj.grouped_category = "wrong"
        with self.assertRaises(ValidationError):
            obj.save()

    def test_last_found_only_change_updates_without_history_row(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")
        found_at = timezone.make_aware(dt.datetime(2026, 6, 3, 12, 0, 0))

        obj.last_found = found_at
        obj.save()

        obj.refresh_from_db()
        self.assertEqual(obj.last_found, found_at)
        self.assertEqual(obj.history.count(), 1)

    def test_update_fields_last_found_ignores_excluded_in_memory_changes(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")
        found_at = timezone.make_aware(dt.datetime(2026, 6, 3, 12, 0, 0))

        obj.name = "Beta"
        obj.last_found = found_at
        obj.save(update_fields=["last_found"])

        obj.refresh_from_db()
        self.assertEqual(obj.name, "Alpha")
        self.assertEqual(obj.last_found, found_at)
        self.assertEqual(obj.history.count(), 1)

    def test_update_fields_history_uses_persisted_values_for_excluded_fields(self):
        obj = ExampleHistoryModel.objects.create(
            name="Alpha",
            status=ExampleHistoryModel.STATUS_ACTIVE,
        )

        obj.name = "Beta"
        obj.status = ExampleHistoryModel.STATUS_ARCHIVED
        obj.save(update_fields=["name"])

        self.assertEqual(obj.status, ExampleHistoryModel.STATUS_ARCHIVED)
        obj.refresh_from_db()
        history = obj.history.latest()
        self.assertEqual(obj.name, "Beta")
        self.assertEqual(obj.status, ExampleHistoryModel.STATUS_ACTIVE)
        self.assertEqual(history.name, "Beta")
        self.assertEqual(history.status, ExampleHistoryModel.STATUS_ACTIVE)

    def test_force_update_fields_history_uses_persisted_values_for_excluded_fields(
        self,
    ):
        obj = ExampleHistoryModel.objects.create(
            name="Alpha",
            status=ExampleHistoryModel.STATUS_ACTIVE,
        )

        obj.name = "Beta"
        obj.status = ExampleHistoryModel.STATUS_ARCHIVED
        obj.save(update_fields=["name"], force_update=True)

        obj.refresh_from_db()
        history = obj.history.latest()
        self.assertEqual(obj.name, "Beta")
        self.assertEqual(obj.status, ExampleHistoryModel.STATUS_ACTIVE)
        self.assertEqual(history.name, "Beta")
        self.assertEqual(history.status, ExampleHistoryModel.STATUS_ACTIVE)

    def test_update_fields_uses_foreign_key_attname_for_excluded_values(self):
        parent = ExampleParentModel.objects.create(name="Parent")
        child = ExampleChildModel.objects.create(name="Alpha", parent=parent)
        missing_parent_id = uuid.uuid4()

        child.name = "Beta"
        child.parent_id = missing_parent_id
        child.save(update_fields=["name"])

        child.refresh_from_db()
        history = child.history.latest()
        self.assertEqual(child.name, "Beta")
        self.assertEqual(child.parent_id, parent.id)
        self.assertEqual(history.name, "Beta")
        self.assertEqual(history.parent_id, parent.id)

    def test_get_change_url_uses_admin_route(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")

        self.assertEqual(
            obj.get_change_url(),
            reverse("admin:core_examplehistorymodel_change", args=(obj.pk,)),
        )
