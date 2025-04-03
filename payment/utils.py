from .models import Order, OrderItem
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from .models import Order, OrderItem
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def generate_invoice_pdf(order_id):
    order = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.select_related("product").filter(order=order)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y_position = height - 40  # Start position for writing text

    # Company Name
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "OneStopShop Store")
    y_position -= 30

    # Invoice Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(230, y_position, "Invoice")
    p.line(50, y_position - 5, 550, y_position - 5)  # Horizontal Line
    y_position -= 30

    # Customer & Order Details
    p.setFont("Helvetica", 12)
    details = [
        f"Full Name: {order.shipping_full_name}",
        f"Contact: {order.shipping_phone}",
        f"Order ID: {order.id}",
        f"Order Date: {order.date_ordered.strftime('%B %d, %Y')}",
        f"Payment Method: {order.payment_method}",
        f"Total Amount: ${order.amount_paid}",
    ]
    for detail in details:
        p.drawString(50, y_position, detail)
        y_position -= 20

    # Shipping Address Section
    y_position -= 30  # Space before address
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_position, "Shipping Address:")
    p.setFont("Helvetica", 12)

    styles = getSampleStyleSheet()
    shipping_text = Paragraph(f"{order.shipping_address.replace('\n', '<br/>')}", styles["Normal"])
    shipping_text.wrapOn(p, 400, 200)
    shipping_text.drawOn(p, 50, y_position - 80)
    y_position -= 120

    # Table Header & Data
    data = [["Product", "Qty", "Unit Price", "Total Price"]]
    for item in order_items:
        data.append([item.product.name, str(item.quantity), f"${item.price}", f"${item.total_price}"])

    # Table Styling
    table = Table(data, colWidths=[200, 70, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Dynamic Table Handling
    max_rows_per_page = 16  # Adjust as needed
    header = data[0]  # Table header
    rows = data[1:]  # Table rows

    while rows:
        rows_to_draw = rows[:max_rows_per_page]  # Get rows that fit on this page
        rows = rows[max_rows_per_page:]  # Remaining rows for next page

        # Create table for this page
        page_data = [header] + rows_to_draw
        table = Table(page_data, colWidths=[200, 70, 100, 100])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        # Check if table fits, otherwise create a new page
        if y_position - (len(rows_to_draw) * 20) < 100:
            p.showPage()  # Create a new page
            y_position = height - 40  # Reset position

        table.wrapOn(p, width, height)
        table.drawOn(p, 50, y_position - (len(rows_to_draw) * 20))
        y_position -= (len(rows_to_draw) * 20 + 30)

    # Net Total at the bottom of the last page
    p.setFont("Helvetica-Bold", 14)
    p.drawString(400, y_position, "Net Total:")
    p.drawString(470, y_position, f"${order.amount_paid}")

    # Footer
    p.setFont("Helvetica", 10)
    p.drawString(50, 30, "Thank you for shopping with us!")
    p.drawString(50, 15, "For any queries, contact support@onestopshop.com")

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()