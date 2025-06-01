from django.shortcuts import render
from django.http import HttpResponse
from django.core.management import call_command
def home(request):
    return render(request,'layout.html')

import os
from django.core.management import call_command
from django.http import HttpResponse
from django.contrib.auth.models import User

def run_setup(request):
    try:
        base_path = os.getcwd()
        fixture_path = os.path.join(base_path, 'data.json')
        if not os.path.exists(fixture_path):
            return HttpResponse("❌ data.json not found at: " + fixture_path)

        call_command('migrate')
        call_command('loaddata', fixture_path)
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        return HttpResponse("✅ Migrations done. Superuser created. Data loaded.")
    except Exception as e:
        return HttpResponse(f"❌ Error: {e}")