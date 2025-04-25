from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import AbstractBaseModel, DataLookup
from apps.core.utils import generate_unique_code


class Category(AbstractBaseModel):
    """
    Represents a category used to group related products.

    Categories help organize products into logical groupings
    (e.g., Electronics, Clothing, Books) for easier navigation and filtering.

    Attributes:
        name (str): The name of the category.
        description (str, optional): A brief description of the category.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Category Name"))

    description = models.TextField(verbose_name=_("Category Description"), blank=True)

    class Meta:
        verbose_name: str = _("Category")
        verbose_name_plural: str = _("Categories")
        db_table: str = "categories"

    def __str__(self) -> str:
        return self.name


class Product(AbstractBaseModel):
    """
    Represents a product in the store.

    Attributes:
        name (str): The name of the product.
        sku (str): A unique identifier for the product (Stock Keeping Unit).
        unit_price (Decimal): The price per unit of the product.
        description (str, optional): A brief description of the product.
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Category"),
    )

    name = models.CharField(max_length=255, verbose_name=_("Product Name"))

    description = models.TextField(verbose_name=_("Description"), blank=True)

    sku = models.CharField(max_length=100, unique=True, verbose_name=_("SKU"))

    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name=_("Unit Price"),
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name: str = _("Product")
        verbose_name_plural: str = _("Products")
        db_table: str = "products"

    def __str__(self) -> str:
        return self.name


class PurchaseOrder(AbstractBaseModel):
    """
    Represents a purchase order from a vendor.

    Attributes:
        vendor (str): The name of the vendor for this order.
        order_date (date): The date when the order was placed.
        status (ForeignKey): The current status of the order (e.g., Pending, Shipped, Cancelled, Completed).
    """

    # * This relationship is assumed that our vendors
    # * are our users and needs to login. otherwise, we can have
    # * a separate Vendor model and use that here.
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_("Vendor")
    )

    order_code = models.CharField(
        max_length=100, verbose_name=_("Unique Invoice Code")
    )

    order_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("Order Date")
    )

    status = models.ForeignKey(
        DataLookup,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="+",
        limit_choices_to={"type": "purchase_order_status"},
    )

    class Meta:
        verbose_name: str = _("Purchase Order")
        verbose_name_plural: str = _("Purchase Orders")
        db_table: str = "purchase_orders"

    def save(self, *args, **kwargs) -> None:

        # * Auto-generate the purchase order unique code
        if not self.order_code:
            self.order_code = generate_unique_code("PUR_ORD", self.id)

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"PO-{self.order_code} - {self.vendor.email}"


class PurchaseOrderItem(AbstractBaseModel):
    """
    Represents an item in a purchase order, linking a product to the order.

    Attributes:
        purchase_order (ForeignKey): The purchase order this item belongs to.
        product (ForeignKey): The product that is part of the order.
        quantity (int): The quantity of the product ordered.
        unit_price (Decimal): The cost of the product for this order line.
    """

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        related_name="purchase_order_items",
        on_delete=models.CASCADE,
        verbose_name=_("Purchase Order"),
    )

    product = models.ForeignKey(
        Product,
        related_name="purchase_order_items",
        on_delete=models.CASCADE,
        verbose_name=_("Product"),
    )

    quantity = models.PositiveIntegerField(verbose_name=_("Quantity"))

    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Unit Price"))

    class Meta:
        verbose_name: str = _("Purchase Order Item")
        verbose_name_plural: str = _("Purchase Order Items")
        db_table: str = "purchase_order_items"

    def __str__(self) -> str:
        return f"{self.product.name} - {self.quantity} units"


class Invoice(AbstractBaseModel):
    """
    Represents a customer invoice.

    Attributes:
        customer_name (str): The name of the customer being invoiced.
        invoice_date (date): The date the invoice was generated.
        status (ForeignKey): The status of the invoice (e.g., Pending, Paid, Cancelled).
    """

    # * Same logic like we did for the Vendor in the PurchasOrder Model.
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_("Customer")
    )

    invoice_code = models.CharField(
        max_length=100, verbose_name=_("Unique Invoice Code")
    )

    invoice_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("Invoice Date")
    )

    status = models.ForeignKey(
        DataLookup,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="+",
        limit_choices_to={"type": "invoice_status"},
    )

    class Meta:
        verbose_name: str = _("Invoice")
        verbose_name_plural: str = _("Invoices")
        db_table: str = "invoices"

    def save(self, *args, **kwargs):
        # * Auto-generate the invoice code
        if not self.invoice_code:
            self.invoice_code = generate_unique_code("INV", self.id)

        super().save(*args, **kwargs)

    def calculate_total(self) -> int:
        return sum([item.unit_price for item in self.invoice_items.all()])

    def __str__(self) -> str:
        return f"Invoice-{self.invoice_code} - {self.customer.email}"


class InvoiceItem(AbstractBaseModel):
    """
    Represents an item in an invoice, linking a product to the invoice.

    Attributes:
        invoice (ForeignKey): The invoice this item belongs to.
        product (ForeignKey): The product that is being invoiced.
        quantity (int): The quantity of the product invoiced.
        unit_price (Decimal): The price of a single unit of the product for this invoice.
    """

    invoice = models.ForeignKey(
        Invoice,
        related_name="invoice_items",
        on_delete=models.CASCADE,
        verbose_name=_("Invoice"),
    )

    product = models.ForeignKey(
        Product,
        related_name="invoice_items",
        on_delete=models.CASCADE,
        verbose_name=_("Product"),
    )

    quantity = models.PositiveIntegerField(verbose_name=_("Quantity"))

    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Unit Price")
    )

    def __str__(self) -> str:
        return f"{self.product.name} - {self.quantity} units @ {self.unit_price}"

    class Meta:
        verbose_name: str = _("Invoice Item")
        verbose_name_plural: str = _("Invoice Items")
        db_table: str = "invoice_items"
