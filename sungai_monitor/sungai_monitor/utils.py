import os
import requests
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def send_alert_notification(sensor_data, threshold):
    """
    Kirim notifikasi alert ke user yang terdaftar
    
    Args:
        sensor_data: SensorData instance
        threshold: SensorThreshold instance
    """
    from .models import AlertNotification, UserProfile
    
    device = sensor_data.device
    
    # Get users yang menerima alert
    users = UserProfile.objects.filter(
        receive_email_alerts=True
    ) | UserProfile.objects.filter(
        receive_telegram_alerts=True
    )
    
    for user_profile in users:
        # Email notification
        if user_profile.receive_email_alerts and user_profile.user.email:
            try:
                notification = AlertNotification.objects.create(
                    sensor_data=sensor_data,
                    notification_type='email',
                    recipient=user_profile.user.email,
                    message=f"Alert: {device.name} - {threshold.message}"
                )
                
                send_email_alert(
                    user_profile.user.email,
                    device,
                    sensor_data,
                    threshold
                )
                
                notification.status = 'sent'
                notification.sent_at = datetime.now()
                notification.save()
                
            except Exception as e:
                logger.error(f"Failed to send email alert: {str(e)}")
                notification.status = 'failed'
                notification.error_message = str(e)
                notification.save()
        
        # Telegram notification
        if user_profile.receive_telegram_alerts and user_profile.telegram_id:
            try:
                notification = AlertNotification.objects.create(
                    sensor_data=sensor_data,
                    notification_type='telegram',
                    recipient=user_profile.telegram_id,
                    message=f"Alert: {device.name} - {threshold.message}"
                )
                
                send_telegram_alert(
                    user_profile.telegram_id,
                    device,
                    sensor_data,
                    threshold
                )
                
                notification.status = 'sent'
                notification.sent_at = datetime.now()
                notification.save()
                
            except Exception as e:
                logger.error(f"Failed to send telegram alert: {str(e)}")
                notification.status = 'failed'
                notification.error_message = str(e)
                notification.save()


def send_email_alert(email, device, sensor_data, threshold):
    """Send email alert"""
    subject = f'⚠️ Alert: {device.name} - {threshold.alert_level.upper()}'
    
    context = {
        'device': device,
        'sensor_data': sensor_data,
        'threshold': threshold,
        'timestamp': sensor_data.timestamp,
    }
    
    html_message = render_to_string('monitoring/email/alert.html', context)
    
    send_mail(
        subject=subject,
        message=threshold.message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )


def send_telegram_alert(telegram_id, device, sensor_data, threshold):
    """Send Telegram alert"""
    if not hasattr(settings, 'TELEGRAM_BOT_TOKEN'):
        logger.warning("Telegram bot token not configured")
        return
    
    bot_token = settings.TELEGRAM_BOT_TOKEN
    
    message = f"""
🚨 *ALERT: {threshold.alert_level.upper()}*

📍 Device: {device.name}
📊 Current Value: {sensor_data.value} {sensor_data.unit}
⏰ Time: {sensor_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

⚠️ {threshold.message}

Location: {device.location_name}
    """.strip()
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': telegram_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()


def send_whatsapp_alert(phone_number, device, sensor_data, threshold):
    """
    Send WhatsApp alert menggunakan Twilio atau WhatsApp Business API
    
    Note: Butuh konfigurasi Twilio atau WhatsApp Business API
    """
    if not hasattr(settings, 'TWILIO_ACCOUNT_SID'):
        logger.warning("Twilio not configured")
        return
    
    from twilio.rest import Client
    
    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )
    
    message = f"""
*ALERT: {threshold.alert_level.upper()}*

Device: {device.name}
Value: {sensor_data.value} {sensor_data.unit}
Time: {sensor_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{threshold.message}
    """.strip()
    
    client.messages.create(
        from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
        to=f"whatsapp:{phone_number}",
        body=message
    )


def generate_pdf_report(report):
    """
    Generate PDF report
    
    Args:
        report: Report instance
        
    Returns:
        BytesIO: PDF file buffer
    """
    from .models import SensorData
    from django.db.models import Avg, Max, Min
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
    )
    
    # Title
    title = Paragraph(report.title, title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Report Info
    info_data = [
        ['Report Period:', f"{report.start_date.strftime('%Y-%m-%d %H:%M')} to {report.end_date.strftime('%Y-%m-%d %H:%M')}"],
        ['Generated By:', report.generated_by.get_full_name() or report.generated_by.username],
        ['Generated At:', report.created_at.strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Device Statistics
    for device in report.devices.all():
        # Device header
        device_title = Paragraph(f"<b>{device.name}</b> ({device.sensor_type})", styles['Heading2'])
        story.append(device_title)
        story.append(Spacer(1, 0.1*inch))
        
        # Get data
        data = SensorData.objects.filter(
            device=device,
            timestamp__gte=report.start_date,
            timestamp__lte=report.end_date
        )
        
        if not data.exists():
            story.append(Paragraph("No data available for this period.", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            continue
        
        # Statistics
        stats = data.aggregate(
            avg=Avg('value'),
            max=Max('value'),
            min=Min('value'),
            count=models.Count('id')
        )
        
        stats_data = [
            ['Metric', 'Value'],
            ['Average', f"{stats['avg']:.2f}"],
            ['Maximum', f"{stats['max']:.2f}"],
            ['Minimum', f"{stats['min']:.2f}"],
            ['Total Readings', str(stats['count'])],
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Alert Summary
        alerts = data.exclude(alert_level='safe')
        if alerts.exists():
            alert_counts = {}
            for alert in alerts:
                alert_counts[alert.alert_level] = alert_counts.get(alert.alert_level, 0) + 1
            
            alert_data = [['Alert Level', 'Count']]
            for level, count in alert_counts.items():
                alert_data.append([level.capitalize(), str(count)])
            
            alert_table = Table(alert_data, colWidths=[2*inch, 2*inch])
            alert_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(Paragraph("<b>Alerts Summary</b>", styles['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            story.append(alert_table)
        
        story.append(Spacer(1, 0.4*inch))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer


def export_data_to_csv(queryset, fields):
    """
    Export queryset to CSV
    
    Args:
        queryset: Django queryset
        fields: List of field names to export
        
    Returns:
        str: CSV content
    """
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(fields)
    
    # Write data
    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field)
            if hasattr(value, 'strftime'):  # DateTime field
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            row.append(str(value))
        writer.writerow(row)
    
    return output.getvalue()


def calculate_device_health(device):
    """
    Calculate device health metrics
    
    Args:
        device: SensorDevice instance
        
    Returns:
        dict: Health metrics
    """
    from .models import SensorData
    from django.utils import timezone
    
    now = timezone.now()
    
    # Last 24 hours
    yesterday = now - timedelta(hours=24)
    
    # Expected readings (assuming 1 reading per 5 minutes = 288 per day)
    expected_readings = 288
    
    # Actual readings
    actual_readings = SensorData.objects.filter(
        device=device,
        timestamp__gte=yesterday
    ).count()
    
    # Uptime percentage
    uptime = (actual_readings / expected_readings * 100) if expected_readings > 0 else 0
    
    # Last reading
    last_reading = device.readings.first()
    
    # Time since last reading
    if last_reading:
        time_since_last = (now - last_reading.timestamp).total_seconds()
    else:
        time_since_last = None
    
    # Health status
    if uptime >= 90:
        health_status = 'excellent'
    elif uptime >= 70:
        health_status = 'good'
    elif uptime >= 50:
        health_status = 'fair'
    else:
        health_status = 'poor'
    
    return {
        'uptime_24h': round(uptime, 2),
        'expected_readings': expected_readings,
        'actual_readings': actual_readings,
        'time_since_last_reading': time_since_last,
        'health_status': health_status,
        'last_reading': last_reading
    }