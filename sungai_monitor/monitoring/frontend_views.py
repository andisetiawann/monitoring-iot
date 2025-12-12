from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Sensor, Reading
from django.db.models import Avg, Max, Min, Count
from django.utils import timezone
from datetime import timedelta

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get all sensors
    sensors = Sensor.objects.all()
    
    # Get recent readings (last 24 hours)
    last_24h = timezone.now() - timedelta(hours=24)
    recent_readings = Reading.objects.filter(timestamp__gte=last_24h).order_by('-timestamp')[:50]
    
    # Get statistics
    total_sensors = sensors.count()
    total_readings = Reading.objects.filter(timestamp__gte=last_24h).count()
    
    # Get latest readings for each sensor
    sensor_stats = []
    for sensor in sensors:
        latest_reading = Reading.objects.filter(sensor=sensor).order_by('-timestamp').first()
        if latest_reading:
            sensor_stats.append({
                'sensor': sensor,
                'latest_reading': latest_reading,
                'readings_24h': Reading.objects.filter(sensor=sensor, timestamp__gte=last_24h).count()
            })
    
    # Get system overview stats
    stats_24h = Reading.objects.filter(timestamp__gte=last_24h).aggregate(
        avg_flow=Avg('flow_rate'),
        max_flow=Max('flow_rate'),
        min_flow=Min('flow_rate'),
        avg_distance=Avg('distance'),
        avg_battery=Avg('battery')
    )
    
    context = {
        'sensors': sensors,
        'recent_readings': recent_readings,
        'sensor_stats': sensor_stats,
        'total_sensors': total_sensors,
        'total_readings': total_readings,
        'stats_24h': stats_24h,
    }
    
    return render(request, 'monitor/dashboard.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username atau password salah')
    return render(request, 'monitor/login.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Akun berhasil dibuat! Silakan login.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'monitor/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')
