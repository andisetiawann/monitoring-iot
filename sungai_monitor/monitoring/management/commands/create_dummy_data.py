from django.core.management.base import BaseCommand
from monitoring.models import Sensor, Reading
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Create dummy data for sensors and readings'

    def handle(self, *args, **options):
        # Create dummy sensors
        sensors_data = [
            {
                'name': 'Sensor Sungai A',
                'identifier': 'SRF001',
                'location': 'Sungai A - Pintu Air Utama',
                'latitude': -6.2088,
                'longitude': 106.8456
            },
            {
                'name': 'Sensor Sungai B',
                'identifier': 'SRF002',
                'location': 'Sungai B - Bendungan',
                'latitude': -6.2146,
                'longitude': 106.8227
            },
            {
                'name': 'Sensor Sungai C',
                'identifier': 'SRF003',
                'location': 'Sungai C - Muara',
                'latitude': -6.1214,
                'longitude': 106.7744
            }
        ]

        sensors = []
        for sensor_data in sensors_data:
            sensor, created = Sensor.objects.get_or_create(
                identifier=sensor_data['identifier'],
                defaults=sensor_data
            )
            sensors.append(sensor)
            if created:
                self.stdout.write(f'Created sensor: {sensor.name}')
            else:
                self.stdout.write(f'Sensor already exists: {sensor.name}')

        # Create dummy readings for the last 24 hours
        now = timezone.now()
        for sensor in sensors:
            for i in range(24):  # One reading per hour for last 24 hours
                timestamp = now - timezone.timedelta(hours=i)
                
                Reading.objects.get_or_create(
                    sensor=sensor,
                    timestamp=timestamp,
                    defaults={
                        'flow_rate': round(random.uniform(0.5, 5.0), 2),  # 0.5 - 5.0 m³/s
                        'distance': round(random.uniform(50, 200), 1),    # 50 - 200 cm
                        'battery': round(random.uniform(85, 100), 1),     # 85% - 100%
                        'raw': {
                            'temperature': round(random.uniform(25, 35), 1),
                            'humidity': round(random.uniform(60, 90), 1)
                        }
                    }
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully created dummy data'))