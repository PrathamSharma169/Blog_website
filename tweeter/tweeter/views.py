from django.shortcuts import render
from django.http import HttpResponse
from django.core.management import call_command
def home(request):
    return render(request,'layout.html')

def run_setup_view(request):
    try:
        call_command('migrate')
        call_command('loaddata', 'data.json')  # Assumes it's in project root
        return HttpResponse("✅ Migrations and data load complete.")
    except Exception as e:
        return HttpResponse(f"❌ Error: {e}")