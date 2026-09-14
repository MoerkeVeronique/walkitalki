import os
import json
import time
import subprocess
from datetime import datetime, timedelta, timezone
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

MEDIA_PATH = "/var/www/walki-talki/meine_app/media"
BENUTZER_DATEI = os.path.join(settings.BASE_DIR, "benutzer.json")

# --- HILFSFUNKTIONEN ---
def formatiere_zeit(dateiname):
    try:
        parts = dateiname.replace(".mp3", "").replace(".webm", "").split("_")
        datum_str = parts[-2]
        zeit_str = parts[-1]
        
        server_zeit = datetime.strptime(f"{datum_str}{zeit_str}", "%Y%m%d%H%M%S")
        anzeige_zeit = server_zeit + timedelta(hours=2)
        
        return anzeige_zeit.strftime("%d.%m.%Y - %H:%M")
    except:
        return "Unbekannt"

# --- LOGIN / REGISTER / LOGOUT ---
def login(request):
    if not os.path.exists(BENUTZER_DATEI): return render(request, "meine_app/login.html")
    with open(BENUTZER_DATEI, "r") as f: users = json.load(f)
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        for u in users:
            if u["username"] == username and u["password"] == password:
                request.session["username"] = username
                return redirect("dashboard")
    return render(request, "meine_app/login.html")

def register(request):
    users = []
    if os.path.exists(BENUTZER_DATEI):
        with open(BENUTZER_DATEI, "r") as f: users = json.load(f)
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        users.append({"username": username, "password": password, "id": int(time.time())})
        with open(BENUTZER_DATEI, "w") as f: json.dump(users, f, indent=2)
        return redirect("login")
    return render(request, "meine_app/register.html")

def logout(request):
    request.session.flush()
    return redirect("login")

# --- DASHBOARD & PTT ---
def dashboard(request):
    if not request.session.get("username"): return redirect("login")
    nachrichten = []
    gesendete_files = []
    
    if os.path.exists(MEDIA_PATH):
        for datei in os.listdir(MEDIA_PATH):
            if datei.endswith(".mp3") or datei.endswith(".webm"):
                zeit_formatiert = formatiere_zeit(datei)
                if datei.startswith("von_pi_1_") or datei.startswith("von_pi_2_"):
                    absender = "Walkie-Talkie_1" if "pi_1" in datei else "Walkie-Talkie_2"
                    nachrichten.append({"name": datei, "absender": absender, "zeit": zeit_formatiert, "url": f"/media/{datei}"})
                    
    gesendet_pfad = os.path.join(MEDIA_PATH, "meine_aufnahmen")
    if os.path.exists(gesendet_pfad):
        for datei in os.listdir(gesendet_pfad):
            if datei.endswith(".mp3") or datei.endswith(".webm"):
                zeit_formatiert = formatiere_zeit(datei)
                gesendete_files.append({"name": datei, "zeit": zeit_formatiert, "url": f"/media/meine_aufnahmen/{datei}", "type": "audio/webm" if datei.endswith(".webm") else "audio/mpeg"})
                
    def get_time(item):
        if "von_pi" in item["name"]:
            pfad = os.path.join(MEDIA_PATH, item["name"])
        else:
            pfad = os.path.join(MEDIA_PATH, "meine_aufnahmen", item["name"])
        return os.path.getmtime(pfad)

 
    nachrichten.sort(key=get_time, reverse=True)
    gesendete_files.sort(key=get_time, reverse=True)
    
    return render(request, "meine_app/dashboard.html", {
        "nachrichten": nachrichten, 
        "gesendete_files": gesendete_files, 
        "username": request.session.get("username")
    })

@csrf_exempt
def pushtotalk(request):
    if not request.session.get("username"): return redirect("login")
    return render(request, "meine_app/pushtotalk.html")

# --- API ENDPUNKTE FÜR UPLOADS ---
@csrf_exempt
def website_audio_upload(request):
    if request.method == "POST" and request.FILES.get("audio_data"):
        ziel_ordner = os.path.join(MEDIA_PATH, "meine_aufnahmen")
        os.makedirs(ziel_ordner, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        temp_webm = os.path.join(ziel_ordner, f"temp_{timestamp}.webm")
        final_mp3 = os.path.join(ziel_ordner, f"von_website_{timestamp}.mp3")
        with open(temp_webm, "wb+") as dest:
            for chunk in request.FILES["audio_data"].chunks():
                dest.write(chunk)
        subprocess.run(['ffmpeg', '-y', '-i', temp_webm, '-acodec', 'libmp3lame', '-ar', '44100', '-ac', '2', '-ab', '128k', final_mp3])
        if os.path.exists(temp_webm): os.remove(temp_webm)
        return JsonResponse({"status": "erfolg", "file": final_mp3})
    return JsonResponse({"status": "fehler"}, status=400)

@csrf_exempt
def pi_api_upload(request):
    wer_sendet = request.GET.get("absender", "pi_1")
    if request.method == "POST" and request.FILES.get("audio_from_pi"):
        os.makedirs(MEDIA_PATH, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        dateiname = f"von_{wer_sendet}_{timestamp}.mp3"
        
        with open(os.path.join(MEDIA_PATH, dateiname), "wb+") as dest:
            for chunk in request.FILES["audio_from_pi"].chunks(): 
                dest.write(chunk)
        return JsonResponse({"status": "erfolg"})
    return JsonResponse({"status": "fehler"}, status=400)

# --- PI ABHOL-ENDPUNKT ---
@csrf_exempt
def pi_api_get_latest(request):
    alle_dateien = []
    
    # 1. Pi-Nachrichten sammeln
    if os.path.exists(MEDIA_PATH):
        for f in os.listdir(MEDIA_PATH):
            if f.endswith(".mp3") or f.endswith(".webm"):
                alle_dateien.append(os.path.join(MEDIA_PATH, f))
    
    # 2. Website-Nachrichten sammeln
    website_ordner = os.path.join(MEDIA_PATH, "meine_aufnahmen")
    if os.path.exists(website_ordner):
        for f in os.listdir(website_ordner):
            if f.endswith(".mp3") or f.endswith(".webm"):
                alle_dateien.append(os.path.join(website_ordner, f))
                
    if alle_dateien:
        alle_dateien.sort(key=os.path.getmtime, reverse=True)
        neueste_datei = alle_dateien[0]
        
        response = FileResponse(open(neueste_datei, 'rb'), content_type='audio/mpeg')
        response['X-Dateiname'] = os.path.basename(neueste_datei)
        return response
    
    return JsonResponse({"status": "leer"}, status=404)

# --- Nachrichten Löschen ---
def loesche_aufnahme(request, dateiname):
    pfad = os.path.join(MEDIA_PATH, dateiname)
    if not os.path.exists(pfad):
        pfad = os.path.join(MEDIA_PATH, "meine_aufnahmen", dateiname)

    # Löschen
    if os.path.exists(pfad):
        os.remove(pfad)
    return redirect("dashboard")