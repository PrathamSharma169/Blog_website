from django.shortcuts import render
from django.http import HttpResponse
from django.core.management import call_command
def home(request):
    return render(request,'layout.html')

import os
from django.core.management import call_command
from django.http import HttpResponse
from django.contrib.auth.models import User

from django.http import HttpResponse
from django.core.management import call_command

def run_migrations(request):
    try:
        call_command('makemigrations')  # Create migration files
        call_command('migrate', 'tweet', fake=True) # Apply them to the DB
        return HttpResponse("✅ Makemigrations and Migrate applied successfully.")
    except Exception as e:
        return HttpResponse(f"❌ Error: {e}")

    
def run_collectstatic(request):
    try:
        call_command('collectstatic', '--noinput')
        return HttpResponse("✅ collectstatic completed.")
    except Exception as e:
        return HttpResponse(f"❌ Error: {e}")