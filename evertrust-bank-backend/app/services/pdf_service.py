from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
import io

def generate_statement_pdf(account, transactions, start_date, end_date):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Title
    elements.append(Paragraph("EverTrust Bank - Account Statement", title_style))
    
    # Account information
    account_info = [
        ["Account Number:", account.number],
        ["Account Type:", account.type],
        ["Statement Period:", f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"],
        ["Current Balance:", f"${account.balance:.2f}"],
        ["Statement Date:", datetime.now().strftime('%Y-%m-%d')]
    ]
    
    account_table = Table(account_info, colWidths=[2*inch, 3*inch])
    account_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    
    elements.append(account_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Transactions header
    elements.append(Paragraph("Transactions", styles['Heading2']))
    
    # Transactions table
    transaction_data = [["Date", "Description", "Type", "Amount", "Balance"]]
    
    running_balance = account.balance
    for tx in reversed(transactions):  # Show in chronological order
        if tx.type == 'Withdrawal' or tx.type == 'Transfer':
            amount = f"-${tx.amount:.2f}"
            running_balance += tx.amount  # Add back to get previous balance
        else:
            amount = f"${tx.amount:.2f}"
            running_balance -= tx.amount  # Subtract to get previous balance
        
        transaction_data.append([
            tx.created_at.strftime('%Y-%m-%d'),
            tx.description[:30] + '...' if len(tx.description) > 30 else tx.description,
            tx.type,
            amount,
            f"${running_balance:.2f}"
        ])
    
    # Add final balance (current balance)
    transaction_data.append([
        "",
        "Current Balance",
        "",
        "",
        f"${account.balance:.2f}"
    ])
    
    transaction_table = Table(transaction_data, colWidths=[0.8*inch, 2*inch, 1*inch, 1*inch, 1*inch])
    transaction_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(transaction_table)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Thank you for banking with EverTrust Bank", styles['Italic']))
    elements.append(Paragraph("Customer Service: 1-800-EVERTRUST", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    return buffer