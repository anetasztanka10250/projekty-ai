import requests
import os

# Wczytaj klucz remove.bg z klucz.txt
with open("klucz.txt", "r") as f:
    for linia in f:
        if "removebg" in linia.lower() or "remove.bg" in linia.lower() or "remove_bg" in linia.lower():
            klucz = linia.split(":")[-1].strip()
            break

print(f"Klucz znaleziony: {klucz[:8]}...")

torty = ["tort1.png", "tort2.png", "tort3.png"]

for nazwa in torty:
    if not os.path.exists(nazwa):
        print(f"Brak pliku: {nazwa} — pomijam")
        continue
    
    print(f"Wycinam tło z {nazwa}...")
    
    with open(nazwa, "rb") as f:
        response = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": f},
            data={"size": "auto"},
            headers={"X-Api-Key": klucz},
        )
    
    if response.status_code == 200:
        wynik = nazwa.replace(".png", "_wycienty.png")
        with open(wynik, "wb") as out:
            out.write(response.content)
        print(f"✅ Gotowe: {wynik}")
    else:
        print(f"❌ Błąd: {response.status_code} — {response.text}")