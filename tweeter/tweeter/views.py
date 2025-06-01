from django.shortcuts import render
from django.http import HttpResponse
from django.core.management import call_command
def home(request):
    return render(request,'layout.html')

import os
from django.core.management import call_command
from django.http import HttpResponse
from django.contrib.auth.models import User

def run_setup_view(request):
    try:
        call_command('migrate')
        
        # ✅ Create a new superuser only if not already created
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("pratham", "pratham@google.com", "Abcdef@123")
        
        return HttpResponse("✅ Migration complete. Superuser created.")
    except Exception as e:
        return HttpResponse(f"❌ Error: {type(e).__name__}<br>{e}")