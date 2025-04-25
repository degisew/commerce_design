from django.urls import path

from apps.store.views import print_invoice


urlpatterns = [
    path(
        "invoices/print/<str:invoice_code>/",
        print_invoice,
        name="print_invoice"
    )
]
