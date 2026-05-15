import base64
import json
import os
import requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import csv
import io
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'szafa-audyt-klucz-2024'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
DATA_FILE = os.path.join(BASE_DIR, 'data', 'wardrobe.json')
TEMP_DIR = os.path.join(BASE_DIR, 'data', 'temp')

TYPY = ['Sukienka', 'Bluzka', 'Spodnie', 'Sweter', 'Kurtka', 'Płaszcz', 'Spódnica', 'Dżinsy', 'T-shirt', 'Buty/Obuwie', 'Torebka/Akcesoria', 'Inne']
STANY = ['Nowe z metką', 'Bardzo dobry', 'Dobry', 'Używane']
STATUSY = ['Do wystawienia', 'Na Vinted', 'Sprzedane']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return []


def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_temp(upload_id, items):
    os.makedirs(TEMP_DIR, exist_ok=True)
    path = os.path.join(TEMP_DIR, f"{upload_id}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False)


def load_temp(upload_id):
    path = os.path.join(TEMP_DIR, f"{upload_id}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def delete_temp(upload_id):
    path = os.path.join(TEMP_DIR, f"{upload_id}.json")
    if os.path.exists(path):
        os.remove(path)


def analyze_image(image_path, filename):
    api_key = os.environ.get('TOGETHER_API_KEY')
    if not api_key:
        return {
            'nazwa': os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title(),
            'typ': 'Inne',
            'marka': 'Nieznana',
            'kolor': 'Nieznany',
            'blad': True
        }

    with open(image_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')

    payload = {
        "model": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
            {"type": "text", "text": "Przeanalizuj zdjęcie. Zwróć TYLKO JSON: {\"name\":\"nazwa po polsku\",\"type\":\"Sukienka|Bluzka|Spodnie|Sweter|Kurtka|Płaszcz|Spódnica|Dżinsy|T-shirt|Buty/Obuwie|Torebka/Akcesoria|Inne\",\"brand\":\"marka lub pusty\",\"color\":\"kolor po polsku\",\"note\":\"1 zdanie po polsku\"}. Dla butów (sneakersy, sandały, kozaki, szpilki itp.) użyj Buty/Obuwie. Dla torebek, plecaków, portfeli i akcesoriów użyj Torebka/Akcesoria."}
        ]}],
        "max_tokens": 300
    }

    response = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    response.raise_for_status()

    text = response.json()['choices'][0]['message']['content'].strip()
    if '```json' in text:
        text = text.split('```json')[1].split('```')[0].strip()
    elif '```' in text:
        text = text.split('```')[1].split('```')[0].strip()

    ai = json.loads(text)
    typ = ai.get('type', 'Inne')
    if typ not in TYPY:
        typ = 'Inne'
    return {
        'nazwa': ai.get('name', filename),
        'typ': typ,
        'marka': ai.get('brand', 'Nieznana') or 'Nieznana',
        'kolor': ai.get('color', ''),
    }


@app.route('/')
def index():
    items = load_data()
    stats = {
        'total': len(items),
        'do_wystawienia': sum(1 for i in items if i.get('status') == 'Do wystawienia'),
        'na_vinted': sum(1 for i in items if i.get('status') == 'Na Vinted'),
        'sprzedane': sum(1 for i in items if i.get('status') == 'Sprzedane'),
        'przychod': sum(float(i.get('cena') or 0) for i in items if i.get('status') == 'Sprzedane'),
        'wartosc_koszyka': sum(float(i.get('cena') or 0) for i in items if i.get('status') in ('Do wystawienia', 'Na Vinted'))
    }
    recent = sorted(items, key=lambda x: x.get('data_dodania', ''), reverse=True)[:8]
    return render_template('index.html', stats=stats, recent=recent)


@app.route('/dodaj', methods=['GET', 'POST'])
def dodaj():
    if request.method == 'GET':
        return render_template('dodaj.html')

    files = request.files.getlist('zdjecia')
    valid = [f for f in files if f and f.filename and allowed_file(f.filename)]

    if not valid:
        flash('Nie wybrano prawidłowych plików. Akceptowane: JPG, PNG, WEBP, GIF', 'warning')
        return render_template('dodaj.html')

    analyzed = []
    for file in valid:
        orig = secure_filename(file.filename)
        unique = f"{uuid.uuid4().hex[:8]}_{orig}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], unique)
        file.save(path)

        try:
            ai = analyze_image(path, orig)
            analyzed.append({
                'filename': unique,
                'original': orig,
                'nazwa': ai.get('nazwa', orig),
                'typ': ai.get('typ', 'Inne'),
                'marka': ai.get('marka', 'Nieznana'),
                'kolor': ai.get('kolor', ''),
                'ai_ok': not ai.get('blad', False)
            })
        except Exception as e:
            analyzed.append({
                'filename': unique,
                'original': orig,
                'nazwa': orig,
                'typ': 'Inne',
                'marka': 'Nieznana',
                'kolor': '',
                'ai_ok': False
            })

    ai_errors = sum(1 for a in analyzed if not a['ai_ok'])
    if ai_errors:
        flash(f'AI nie przeanalizował {ai_errors} zdjęć (brak klucza lub błąd) — uzupełnij ręcznie.', 'warning')

    upload_id = str(uuid.uuid4())
    save_temp(upload_id, analyzed)
    session['upload_id'] = upload_id
    return redirect(url_for('przejrzyj'))


@app.route('/przejrzyj')
def przejrzyj():
    upload_id = session.get('upload_id')
    if not upload_id:
        flash('Brak danych. Dodaj zdjęcia.', 'info')
        return redirect(url_for('dodaj'))
    items = load_temp(upload_id)
    if not items:
        flash('Sesja wygasła. Dodaj zdjęcia ponownie.', 'warning')
        return redirect(url_for('dodaj'))
    return render_template('przejrzyj.html', items=items, typy=TYPY, stany=STANY, upload_id=upload_id)


@app.route('/zapisz', methods=['POST'])
def zapisz():
    upload_id = request.form.get('upload_id') or session.get('upload_id')
    data = load_data()

    filenames = request.form.getlist('filename')
    nazwy = request.form.getlist('nazwa')
    typy_f = request.form.getlist('typ')
    marki = request.form.getlist('marka')
    kolory = request.form.getlist('kolor')
    stany = request.form.getlist('stan')

    saved = 0
    for i, fn in enumerate(filenames):
        if not fn:
            continue
        data.append({
            'id': str(uuid.uuid4()),
            'filename': fn,
            'nazwa': nazwy[i] if i < len(nazwy) else '',
            'typ': typy_f[i] if i < len(typy_f) else 'Inne',
            'marka': marki[i] if i < len(marki) else 'Nieznana',
            'kolor': kolory[i] if i < len(kolory) else '',
            'stan': stany[i] if i < len(stany) else 'Dobry',
            'status': 'Do wystawienia',
            'link_vinted': '',
            'cena': '',
            'data_dodania': datetime.now().isoformat()
        })
        saved += 1

    save_data(data)
    if upload_id:
        delete_temp(upload_id)
        session.pop('upload_id', None)

    flash(f'Dodano {saved} ubrań! Ustaw status i linki Vinted w katalogu.', 'success')
    return redirect(url_for('katalog'))


@app.route('/katalog')
def katalog():
    items = load_data()
    filtr_typ = request.args.get('typ', '')
    filtr_status = request.args.get('status', '')
    filtr_stan = request.args.get('stan', '')
    szukaj = request.args.get('szukaj', '')

    if filtr_typ:
        items = [i for i in items if i.get('typ') == filtr_typ]
    if filtr_status:
        items = [i for i in items if i.get('status') == filtr_status]
    if filtr_stan:
        items = [i for i in items if i.get('stan') == filtr_stan]
    if szukaj:
        q = szukaj.lower()
        items = [i for i in items if q in i.get('nazwa', '').lower()
                 or q in i.get('marka', '').lower() or q in i.get('kolor', '').lower()]

    return render_template('katalog.html', items=items, typy=TYPY, stany=STANY, statusy=STATUSY,
                           filtr_typ=filtr_typ, filtr_status=filtr_status, filtr_stan=filtr_stan,
                           szukaj=szukaj, total=len(items))


@app.route('/edytuj/<item_id>', methods=['GET', 'POST'])
def edytuj(item_id):
    data = load_data()
    item = next((i for i in data if i['id'] == item_id), None)
    if not item:
        flash('Nie znaleziono ubrania.', 'danger')
        return redirect(url_for('katalog'))

    if request.method == 'POST':
        item['nazwa'] = request.form.get('nazwa', item['nazwa'])
        item['typ'] = request.form.get('typ', item['typ'])
        item['marka'] = request.form.get('marka', item['marka'])
        item['kolor'] = request.form.get('kolor', item['kolor'])
        item['stan'] = request.form.get('stan', item['stan'])
        item['status'] = request.form.get('status', item['status'])
        item['link_vinted'] = request.form.get('link_vinted', '').strip()
        cena = request.form.get('cena', '').strip().replace(',', '.')
        item['cena'] = cena if cena else ''
        save_data(data)
        flash('Zaktualizowano ubranie.', 'success')
        return redirect(url_for('katalog'))

    return render_template('edytuj.html', item=item, typy=TYPY, stany=STANY, statusy=STATUSY)


@app.route('/usun/<item_id>', methods=['POST'])
def usun(item_id):
    data = load_data()
    item = next((i for i in data if i['id'] == item_id), None)
    if item:
        fp = os.path.join(app.config['UPLOAD_FOLDER'], item.get('filename', ''))
        if os.path.exists(fp):
            os.remove(fp)
        data = [i for i in data if i['id'] != item_id]
        save_data(data)
        flash('Ubranie usunięte.', 'success')
    return redirect(url_for('katalog'))


@app.route('/statystyki')
def statystyki():
    items = load_data()
    typ_counts = {t: sum(1 for i in items if i.get('typ') == t) for t in TYPY}
    status_counts = {s: sum(1 for i in items if i.get('status') == s) for s in STATUSY}
    stan_counts = {s: sum(1 for i in items if i.get('stan') == s) for s in STANY}

    sprzedane = [i for i in items if i.get('status') == 'Sprzedane']
    przychod_total = sum(float(i.get('cena') or 0) for i in sprzedane)
    wartosc_koszyka = sum(float(i.get('cena') or 0) for i in items if i.get('status') in ('Do wystawienia', 'Na Vinted'))

    miesiace = {}
    for i in sprzedane:
        if i.get('cena'):
            m = i.get('data_dodania', '')[:7]
            if m:
                miesiace[m] = miesiace.get(m, 0) + float(i.get('cena') or 0)

    return render_template('statystyki.html',
                           total=len(items),
                           typ_counts=typ_counts,
                           status_counts=status_counts,
                           stan_counts=stan_counts,
                           sprzedane=sprzedane,
                           przychod_total=przychod_total,
                           wartosc_koszyka=wartosc_koszyka,
                           miesiace=sorted(miesiace.items()))


@app.route('/eksport')
def eksport():
    data = load_data()
    output = io.StringIO()
    fields = ['id', 'nazwa', 'typ', 'marka', 'kolor', 'stan', 'status', 'link_vinted', 'cena', 'data_dodania']
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    for item in data:
        writer.writerow({k: item.get(k, '') for k in fields})
    output.seek(0)
    return Response(
        '﻿' + output.getvalue(),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename=szafa_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)
    app.run(debug=True, host='127.0.0.1', port=5000)
