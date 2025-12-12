from django.urls import path
from . import views

urlpatterns = [
    path('sensors/', views.SensorListCreate.as_view(), name='sensor-list'),
    path('sensors/<int:pk>/', views.SensorDetail.as_view(), name='sensor-detail'),
    path('sensors/<int:sensor_id>/readings/', views.ReadingBySensor.as_view(), name='sensor-readings'),
    path('readings/', views.ReadingList.as_view(), name='reading-list'),
    path('ingest/', views.ingest_reading, name='ingest'),
]
