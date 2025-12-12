from django.contrib import admin
from .models import Sensor, Reading

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('name','identifier','location','created_at')

@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ('sensor','timestamp','flow_rate','distance','created_at')
    list_filter = ('sensor',)
