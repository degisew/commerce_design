import openpyxl
from django.db.models import Sum, F, FloatField
from django.http import HttpResponse
from datetime import timedelta
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils.timezone import now
from apps.core.models import DataLookup
from apps.store.enums import InvoiceStatuses, PurchaseOrderStatuses
from .models import (
    Product,
    Category,
    PurchaseOrder,
    PurchaseOrderItem,
    Invoice,
    InvoiceItem,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
    exclude = ["deleted_at"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "unit_price", "get_category")
    search_fields = ("name", "sku")
    list_filter = ("category",)
    ordering = ("name",)
    exclude = ["deleted_at"]

    # * b/c relationship is optional
    def get_category(self, obj):
        return obj.category.name if hasattr(obj, "category") else "-"

    get_category.short_description = "Category"


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    exclude = ["deleted_at"]
    extra = 1
    autocomplete_fields = ("product",)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    actions = ["mark_as_cancelled"]
    list_display = ("order_code", "vendor", "order_date", "status", "total_cost")
    search_fields = ("vendor",)
    list_filter = ("status", "order_date")
    date_hierarchy = "order_date"
    ordering = ("-order_date",)
    exclude = ["deleted_at", "order_code"]
    inlines = [PurchaseOrderItemInline]

    def total_cost(self, obj):
        """
        Calculate total cost for the purchase order.
        """
        return sum(
            item.quantity * item.unit_price for item in obj.purchase_order_items.all()
        )

    def mark_as_cancelled(self, request, queryset) -> None:
        """
        Custom admin action to mark selected purchase orders as Cancelled.
        """
        try:
            purchase_order_status: DataLookup = DataLookup.objects.get(
                type=PurchaseOrderStatuses.TYPE.value,
                value=PurchaseOrderStatuses.CANCELLED.value,
            )
        except DataLookup.DoesNotExist:
            raise

        updated_count = queryset.update(status=purchase_order_status)

        self.message_user(
            request,
            _(f"{updated_count} order(s) successfully marked as Cancelled."),
            messages.SUCCESS,
        )

    mark_as_cancelled.short_description = "Mark selected orders as Cancelled"

    total_cost.short_description = "Total Cost"
    total_cost.admin_order_field = "purchase_order_items__unit_price"


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceItem
    exclude = ["deleted_at"]
    extra = 1
    autocomplete_fields = ("product",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    actions = ["mark_as_paid", "export_invoices_as_xlsx"]
    list_display = (
        "invoice_code",
        "customer",
        "invoice_date",
        "status",
        "total_amount",
        "highlight_invoice_date",
        "print_invoice",
    )
    search_fields = ("customer",)
    list_filter = ("status", "invoice_date")
    date_hierarchy = "invoice_date"
    ordering = ("-invoice_date",)
    exclude = ["deleted_at", "invoice_code"]
    inlines = [InvoiceLineItemInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(total_amount=Sum(
            F("invoice_items__quantity") * F("invoice_items__unit_price"),
            output_field=FloatField()
        ))

    def total_amount(self, obj) -> str:
        return f"ETB {obj.total_amount}" if obj.total_amount else "<b>ETB 0.00"

    total_amount.short_description = "Total Amount"

    def mark_as_paid(self, request, queryset) -> None:
        """
        Custom admin action to mark selected invoices as Paid.
        """
        try:
            invoice_status = DataLookup.objects.get(
                type=InvoiceStatuses.TYPE.value, value=InvoiceStatuses.PAID.value
            )
        except DataLookup.DoesNotExist:
            raise

        updated_count = queryset.update(status=invoice_status)

        self.message_user(
            request,
            _(f"{updated_count} invoice(s) successfully marked as Paid."),
            messages.SUCCESS,
        )

    def highlight_invoice_date(self, obj):
        """
        Displays the invoice date in red if the invoice is older than one week
        and is not marked as paid. Helps highlight potentially overdue invoices
        directly in the admin list view.
        """
        try:
            invoice_status: DataLookup = DataLookup.objects.get(
                type=InvoiceStatuses.TYPE.value,
                value=InvoiceStatuses.PAID.value
            )
        except DataLookup.DoesNotExist:
            raise

        one_week_ago = now().date() - timedelta(days=7)

        if obj.invoice_date and (
            obj.invoice_date < one_week_ago and obj.status != invoice_status
        ):
            return format_html(
                '<span style="background-color: red; color: white;"><strong>{}</strong></span>',
                obj.invoice_date,
            )
        return obj.invoice_date

    def print_invoice(self, obj):
        url = reverse("print_invoice", args=[obj.invoice_code])
        return format_html(f'<a class="button" href="{url}" target="_blank">Print</a>')

    def export_invoices_as_xlsx(self, request, queryset) -> HttpResponse:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Invoices"

        # Header
        ws.append(["Invoice Code", "Customer", "Total", "Status"])

        for invoice in queryset:
            total = invoice.calculate_total()  # implement in model
            ws.append([
                invoice.invoice_code,
                invoice.customer.email,
                total,
                invoice.status.name
            ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="invoices.xlsx"'
        wb.save(response)
        return response

    export_invoices_as_xlsx.short_description = "Export selected invoices to XLSX"

    print_invoice.short_description = "Action"

    print_invoice.allow_tags = True

    highlight_invoice_date.short_description = "Due Date"

    mark_as_paid.short_description = "Mark selected invoices as Paid"

    total_amount.short_description = "Total Amount"
    total_amount.admin_order_field = "invoice_items__unit_price"
