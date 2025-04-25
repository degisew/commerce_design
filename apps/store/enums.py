from enum import Enum


class InvoiceStatuses(Enum):
    TYPE = "invoice_status"

    PENDING = "invoice_status_pending"
    PAID = "invoice_status_paid"


class PurchaseOrderStatuses(Enum):
    TYPE = "purchase_order_status"

    PENDING = "purchase_order_status_pending"
    COMPLETED = "purchase_order_status_completed"
    CANCELLED = "purchase_order_status_cancelled"
