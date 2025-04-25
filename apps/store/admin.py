from django.contrib import admin
from .models import (
    Product,
    Category,
    PurchaseOrder,
    PurchaseOrderLineItem,
    Invoice,
    InvoiceLineItem
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "unit_price", "get_category")
    search_fields = ("name", "sku")
    list_filter = ("category",)
    ordering = ("name",)

    def get_category(self, obj):
        return obj.category.name if hasattr(obj, "category") else "-"

    get_category.short_description = "Category"


class PurchaseOrderLineItemInline(admin.TabularInline):
    model = PurchaseOrderLineItem
    extra = 1
    autocomplete_fields = ("product",)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor_name", "order_date", "status")
    search_fields = ("vendor_name",)
    list_filter = ("status", "order_date")
    date_hierarchy = "order_date"
    ordering = ("-order_date",)
    inlines = [PurchaseOrderLineItemInline]


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1
    autocomplete_fields = ("product",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "invoice_date", "status")
    search_fields = ("customer_name",)
    list_filter = ("status", "invoice_date")
    date_hierarchy = "invoice_date"
    ordering = ("-invoice_date",)
    inlines = [InvoiceLineItemInline]


# admin.site.register(Category, CategoryAdmin)
# admin.site.register(Product, ProductAdmin)
# admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
# admin.site.register(Invoice, InvoiceAdmin)
