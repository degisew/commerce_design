from django.http import HttpResponse


def print_invoice(request, invoice_code) -> HttpResponse:
    # TODO: This can be made better by having an HTML template
    # TODO: to be rendered as an invoice than HTTpResponse
    return HttpResponse(f"<h1>Invoice {invoice_code} Printed.")
