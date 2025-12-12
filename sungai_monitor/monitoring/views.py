from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.utils.dateparse import parse_datetime
from .models import Sensor, Reading
from .serializers import SensorSerializer, ReadingSerializer
from django.shortcuts import get_object_or_404

class SensorListCreate(generics.ListCreateAPIView):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer

class SensorDetail(generics.RetrieveUpdateAPIView):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer

class ReadingList(generics.ListAPIView):
    queryset = Reading.objects.all()
    serializer_class = ReadingSerializer

class ReadingBySensor(generics.ListAPIView):
    serializer_class = ReadingSerializer
    def get_queryset(self):
        sensor_id = self.kwargs['sensor_id']
        limit = int(self.request.GET.get('limit', 100))
        return Reading.objects.filter(sensor__id=sensor_id).order_by('-timestamp')[:limit]

@api_view(['POST'])
def ingest_reading(request):
    """Ingest sensor readings from IoT devices"""
    data = request.data
    
    # Get or create sensor
    sensor, _ = Sensor.objects.get_or_create(
        sensor_id=data.get('sensor_id'),
        defaults={'name': data.get('name', f'Sensor {data.get("sensor_id")}')}
    )
    
    # Create reading
    reading = Reading.objects.create(
        sensor=sensor,
        value=data.get('value'),
        timestamp=parse_datetime(data.get('timestamp')) if data.get('timestamp') else None
    )
    
    serializer = ReadingSerializer(reading)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
