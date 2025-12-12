from rest_framework import serializers
from .models import Sensor, Reading

class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = '__all__'

class ReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reading
        fields = '__all__'
