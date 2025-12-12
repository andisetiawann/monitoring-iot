from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# ========== MODELS EXISTING (Your Original) ==========

class Sensor(models.Model):
    """
    Identitas sensor / perangkat (flow sensor + ultrasonic)
    """
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100, unique=True)  # mis: MAC atau id perangkat
    location = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ===== TAMBAHAN FIELDS UNTUK FITUR BARU =====
    sensor_type = models.CharField(
        max_length=20, 
        choices=[
            ('flow', 'Flow Meter'),
            ('ultrasonic', 'Ultrasonic SRF'),
            ('combined', 'Combined (Flow + Ultrasonic)'),
        ],
        default='combined'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('maintenance', 'Maintenance'),
        ],
        default='offline'
    )
    api_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.identifier})"
    
    def update_status(self):
        """Update status berdasarkan last_seen"""
        if self.last_seen:
            time_diff = timezone.now() - self.last_seen
            if time_diff.total_seconds() > 300:  # 5 menit
                self.status = 'offline'
            else:
                self.status = 'online'
            self.save()
    
    class Meta:
        verbose_name = 'Sensor Device'
        verbose_name_plural = 'Sensor Devices'
        ordering = ['-created_at']


class Reading(models.Model):
    """
    Pembacaan dari sensor
    """
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField()  # waktu pembacaan dari perangkat
    flow_rate = models.FloatField(blank=True, null=True)   # e.g. liter/s atau m3/s
    distance = models.FloatField(blank=True, null=True)    # SRF (cm)
    battery = models.FloatField(blank=True, null=True)     # optional
    raw = models.JSONField(blank=True, null=True)          # untuk menyimpan payload tambahan
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ===== TAMBAHAN FIELDS UNTUK FITUR ALERT =====
    alert_level = models.CharField(
        max_length=20,
        choices=[
            ('safe', 'Safe'),
            ('warning', 'Warning'),
            ('danger', 'Danger'),
            ('critical', 'Critical'),
        ],
        default='safe'
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['sensor', 'timestamp']),
            models.Index(fields=['alert_level', '-timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.sensor.identifier} @ {self.timestamp.isoformat()}"
    
    def check_thresholds(self):
        """
        Cek threshold untuk flow_rate dan distance
        Set alert_level berdasarkan threshold yang aktif
        """
        # Check flow rate thresholds
        if self.flow_rate is not None:
            flow_thresholds = self.sensor.thresholds.filter(
                is_active=True,
                threshold_type='flow'
            ).order_by('-min_value')
            
            for threshold in flow_thresholds:
                if threshold.min_value and threshold.max_value:
                    if threshold.min_value <= self.flow_rate <= threshold.max_value:
                        self.alert_level = threshold.alert_level
                        return threshold
                elif threshold.min_value and self.flow_rate >= threshold.min_value:
                    self.alert_level = threshold.alert_level
                    return threshold
                elif threshold.max_value and self.flow_rate <= threshold.max_value:
                    self.alert_level = threshold.alert_level
                    return threshold
        
        # Check distance thresholds
        if self.distance is not None:
            distance_thresholds = self.sensor.thresholds.filter(
                is_active=True,
                threshold_type='distance'
            ).order_by('-min_value')
            
            for threshold in distance_thresholds:
                if threshold.min_value and threshold.max_value:
                    if threshold.min_value <= self.distance <= threshold.max_value:
                        self.alert_level = threshold.alert_level
                        return threshold
                elif threshold.min_value and self.distance >= threshold.min_value:
                    self.alert_level = threshold.alert_level
                    return threshold
                elif threshold.max_value and self.distance <= threshold.max_value:
                    self.alert_level = threshold.alert_level
                    return threshold
        
        self.alert_level = 'safe'
        return None


# ========== NEW MODELS FOR FEATURES ==========

class SensorThreshold(models.Model):
    """Model untuk threshold/batas ambang sensor"""
    ALERT_LEVELS = [
        ('safe', 'Safe'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
        ('critical', 'Critical'),
    ]
    
    THRESHOLD_TYPES = [
        ('flow', 'Flow Rate'),
        ('distance', 'Distance (Water Level)'),
    ]
    
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='thresholds')
    threshold_type = models.CharField(max_length=20, choices=THRESHOLD_TYPES)
    alert_level = models.CharField(max_length=20, choices=ALERT_LEVELS)
    min_value = models.FloatField(blank=True, null=True)
    max_value = models.FloatField(blank=True, null=True)
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['sensor', 'threshold_type', 'min_value']
        verbose_name = 'Sensor Threshold'
        verbose_name_plural = 'Sensor Thresholds'
    
    def __str__(self):
        return f"{self.sensor.name} - {self.threshold_type} - {self.alert_level}"


class AlertNotification(models.Model):
    """Model untuk notifikasi alert"""
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
        ('web', 'Web Push'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    reading = models.ForeignKey(Reading, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Alert Notification'
        verbose_name_plural = 'Alert Notifications'
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient} - {self.status}"


class SystemLog(models.Model):
    """Model untuk system logging"""
    LOG_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    level = models.CharField(max_length=20, choices=LOG_LEVELS)
    module = models.CharField(max_length=100)
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    extra_data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', '-timestamp']),
            models.Index(fields=['module', '-timestamp']),
        ]
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.module} - {self.timestamp}"


class UserProfile(models.Model):
    """Extended user profile"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('operator', 'Operator'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    phone = models.CharField(max_length=20, blank=True)
    telegram_id = models.CharField(max_length=100, blank=True)
    receive_email_alerts = models.BooleanField(default=True)
    receive_telegram_alerts = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Report(models.Model):
    """Model untuk laporan yang di-generate"""
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('custom', 'Custom Report'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    sensors = models.ManyToManyField(Sensor)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.FileField(upload_to='reports/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
    
    def __str__(self):
        return f"{self.title} - {self.status}"