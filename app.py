from flask import Flask, render_template, request
import os
import time
from PIL import Image
from io import BytesIO
import re
from coordonate import coordonate
import numpy as np
import easyocr

app = Flask(__name__)
def cautare_anaf(localitate):
    lower_localitate = localitate.lower()
    
    from anaf.alba import alba
    from anaf.bucuresti import bucuresti
    from anaf.cluj import cluj
    from anaf.craiova import craiova
    from anaf.galati import galati
    from anaf.iasi import iasi
    from anaf.ploiesti import ploiesti
    from anaf.timisoara import timisoara

    anaf_data = [alba, bucuresti, cluj, craiova, galati, iasi, ploiesti, timisoara]

    for data in anaf_data:
        for directie, judete in data.items():
            #if isinstance(directie, dict):  # Verifică dacă directie este un dicționar
                for judet, unitati in judete.items():
                    if isinstance(unitati, dict):  # Verifică dacă unitati este un dicționar
                        for unitate, localitati in unitati.items():
                            if isinstance(localitati, list):  # Verifică dacă localitati este o listă
                                for loc in localitati:
                                    if loc.lower() == lower_localitate:
                                        return unitate, judet, directie
    return "Unknown", "UnKnown", "UNKNOWN"

def replace_diacritics(text):
    text = text.replace('ă', 'a')
    text = text.replace('â', 'a')
    text = text.replace('î', 'i')
    text = text.replace('ș', 's')
    text = text.replace('ț', 't')
    text = text.replace('Ă', 'A')
    text = text.replace('Â', 'A')
    text = text.replace('Î', 'I')
    text = text.replace('Ș', 'S')
    text = text.replace('Ț', 'T')
    return text  # Add return statement

# Directorul unde sunt salvate fișierele încărcate
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Funcția de ștergere a fișierelor mai vechi de 24 de ore
def sterge_fisiere_vechi():
    folder_upload = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(folder_upload):
        file_path = os.path.join(folder_upload, filename)
        if os.path.getmtime(file_path) < time.time() - 3600 :  # 86400 secunde = 24h
            os.remove(file_path)
            print(f"Fișierul {filename} a fost șters, fiind mai vechi de 24 de ore.")

# Funcție pentru procesarea textului din imagine
def filtru_cifre(text):
    return ''.join(re.findall(r'[0-9]', text))  # Păstrează doar cifrele

def filtru_litere(text):
    text = text.replace('-', ' ')
    text = text.replace(',', ' ')
    return ''.join(re.findall(r'[a-zA-ZăâîșțĂÂÎȘȚ ]', text))  # Păstrează doar literele

def filtru_nume(text):
    text = text.replace('-', ' ')  # Înlocuiește cratimele cu spațiu
    text = text.replace(',', ' ')  # Înlocuiește virgulele cu spațiu
    # Adaugă un spațiu înainte de literele mari care sunt urmate de litere mici
    text = re.sub(r'(?<=[a-zA-ZăâîșțĂÂÎȘȚ])(?=[A-ZĂÂÎȘȚ])', ' ', text)
    # Păstrează doar literele și spațiile
    return ''.join(re.findall(r'[a-zA-ZăâîșțĂÂÎȘȚ ]', text))

def capitalize_words(text):
    return ' '.join([word.capitalize() for word in text.split()])

# Configurare EasyOCR
reader = easyocr.Reader(['en'])

# Funcție pentru procesarea unei zone din imagine
def proceseaza_zona(coord, idx, image):
    zona_decupata = image.crop(coord)
    # if idx == 13:  # Apartament (zona 14)
    #     zona_decupata = zona_decupata.resize((zona_decupata.width * 4, zona_decupata.height * 4))  # Mărire imagine
    # elif idx == 6:  # Email (zona 7)
    #     zona_decupata = zona_decupata.resize((zona_decupata.width * 4, zona_decupata.height * 4))  # Mărire imagine
    # elif idx == 0 or idx == 1:  # Prenume (zona 1) și Nume (zona 2)
    #     zona_decupata = zona_decupata.resize((zona_decupata.width * 4, zona_decupata.height * 4))
    # else:
    #     zona_decupata = zona_decupata.resize((zona_decupata.width * 4, zona_decupata.height * 4))  # Mărire imagine
    zona_decupata = zona_decupata.resize((zona_decupata.width * 4, zona_decupata.height * 4))  # Mărire imagine
    zona_np = np.array(zona_decupata)  # Convertim în array NumPy
    rezultate = reader.readtext(zona_np)  # OCR
    text = " ".join([rezultat[1] for rezultat in rezultate])  # Extragem textul
    
    # Afișăm în terminal textul citit
    print(f"Text citit din zona {idx + 1}: {text}")
    # print('*' * 50)  # Linie de debug
    
    return text

# Funcție pentru procesarea fișierului
def proceseaza_fisier(image):
    info = {
            'nume': '', 'initiala_tatalui': '', 'prenume': '', 'cnp': '', 'adresa': '', 'email': '', 'scara': '', 
            'apartament': '', 'bloc': '', 'localitate': '', 'judet': '', 'cp': '', 'telefon': '', 'doiani': '',
            'anaf1' : '', 'anaf2' : '', 'anaf3' : ''
            }

    # Definim variabilele pentru detaliile adresei
    strada = ""
    nr = ""
    localitate = ""
    judet = ""
    cp = ""
    bloc = ""
    etaj = ""
    
    for idx, coord in enumerate(coordonate):
        text = proceseaza_zona(coord, idx, image)
        text_initial = text
        try:
            if idx == 0:  # Prenume (zona 1)
                text_filtrat = capitalize_words(filtru_nume(text_initial))
                prenume = text_filtrat
                #daca prima litera e L si ultima e 'a' atunci incepe cu I, nu cu L
                if prenume[0] == 'L' and prenume[-1] == 'a':
                    prenume = 'I'+ prenume[1:]
                info['prenume'] = prenume
            elif idx == 1:  # Nume (zona 2)
                text_filtrat = capitalize_words(filtru_nume(text_initial))
                nume = text_filtrat
                info['nume'] = nume
            elif idx == 2:  # Inițiala tatălui (zona 3)
                text_filtrat = filtru_litere(text_initial)
                initiala_tatalui = text_filtrat
                info['initiala_tatalui'] = initiala_tatalui
            elif idx == 3:  # Strada (zona 4)
                text_filtrat = text_initial.capitalize()
                strada = text_filtrat
            elif idx == 4:  # Număr (zona 5)
                text_filtrat = text_initial.lstrip('0')
                numar = text_filtrat
            elif idx == 5:  # CNP (zona 6)
                text_filtrat = filtru_cifre(text_initial)
                cnp_total = text_filtrat  # Inițializăm cnp_tota
                info['cnp'] = cnp_total
            elif idx == 6:  # Email (zona 7)
                text_filtrat = text_initial.replace(' ', '.')  # Înlocuiește spațiile cu puncte
                text_filtrat = text_filtrat.replace('..', '.')  # Înlocuiește punctele duble
                text_filtrat = text_filtrat.replace('com.', 'com')  # Înlocuiește "com." cu "com"
                if text_filtrat.find('.com') == -1:
                    text_filtrat = text_filtrat.replace('com', '.com')  # Adaugă un punct înainte de "com"
                email = text_filtrat  # Actualizează variabila email
                info['email'] = email
            elif idx == 7:  # Județ (zona 8)
                text_filtrat = capitalize_words(text_initial)
                text_filtrat = replace_diacritics(text_filtrat)
                judet = text_filtrat
                info['judet'] = judet
                #memoreaza variabila judet ca sa pot sa o accesez si cand idx e 8
            elif idx == 8:  # Localitate (zona 9)
                text_initial = text_initial.replace('-', ' ')  # Înlocuiește cratimele cu spațiu
                text_initial = text_initial.replace(',', ' ')  # Înlocuiește virgulele cu spațiu
                text_filtrat = capitalize_words(text_initial)
                text_filtrat = replace_diacritics(text_filtrat)
                #strip text
                text_filtrat = text_filtrat.strip()
                localitate = text_filtrat
                if localitate.lower() != "bucuresti":
                    print("am intrat in if")
                    folder_localitate_mic,folder_localitate_med, folder_localitate_mare = cautare_anaf(localitate) # Caută localitatea în baza de date ANAF
                    if folder_localitate_mic == "Unknown":
                        folder_localitate_mic = localitate
                        folder_localitate = localitate
                        #debug_afisare(idx, "Localitate", text_initial, text_filtrat)
                        print(cautare_anaf(localitate))
                        print(f"Localitatea din if {localitate} nu a fost găsită în baza de date ANAF")
                    if folder_localitate_med == "UnKnown":
                        folder_localitate_med = localitate
                    if folder_localitate_mare == "UNKNOWN":
                        folder_localitate_mare = localitate
                elif localitate.lower() == "bucuresti":
                    print(f"am intrat in else, cautam judetul {judet}")
                    temp_judet= judet.lower()
                    print (temp_judet)
                    print (judet)
                    folder_localitate_mic,folder_localitate_med, folder_localitate_mare = cautare_anaf(temp_judet)
                    #debug_afisare(idx, "Localitate", text_initial, text_filtrat)
                    print(cautare_anaf(temp_judet))
                    print(f"Judetul {judet} nu a fost găsită în baza de date ANAF")
                    if folder_localitate_mic == "Unknown":
                        folder_localitate = localitate
                    if folder_localitate_med == "UnKnown":
                        folder_localitate_med = judet
                    if folder_localitate_mare == "UNKNOWN":
                        folder_localitate_mare = judet
                info['anaf1'] = folder_localitate_mic
                info['anaf2'] = folder_localitate_med
                info['anaf3'] = folder_localitate_mare
                info['localitate'] = localitate
            elif idx == 9:  # Cod postal (zona 10)
                text_filtrat = filtru_cifre(text_initial) if text_initial else ""
                cp = text_filtrat
                info['cp'] = cp
            elif idx == 10:  # Bloc (zona 11)
                text_filtrat = text_initial.upper() if text_initial else ""
                bloc = text_filtrat
                info['bloc'] = bloc
            elif idx == 11:  # Scara (zona 12)
                text_filtrat = text_initial.upper() if text_initial else ""
                scara = text_filtrat
                info['scara'] = scara
            elif idx == 12:  # Etaj (zona 13)
                text_filtrat = filtru_cifre(text_initial) if text_initial else ""
                etaj = text_filtrat
                info['etaj'] = etaj
            elif idx == 13:  # Apartament (zona 14)
                text_filtrat = text_initial
                apartament = text_filtrat
                info['apartament'] = apartament
            elif idx == 14:  # Telefon (zona 15)
                text_filtrat = filtru_cifre(text_initial)
                phone = text_filtrat
                info['telefon'] = phone
            elif idx == 15: #2 ani
                    if text_initial!='':
                        info['doiani'] = 'DA'
                    else:
                        info['doiani'] = 'NU'
        except Exception as e:
            print(f"Eroare la procesarea zonei {idx + 1}: {e}")

    # Construim adresa conform formatului dorit
    info['adresa'] = f"Str. {strada} NR. {nr} LOC. {localitate} JUD. {judet}"
    
    if bloc:
        info['adresa'] += f" Bl. {bloc}"
        print(f"Bloc: {bloc}")
    if info['scara']:
        info['adresa'] += f" Sc. {info['scara']}"
        print(f"Scara: {info['scara']}")
    if etaj:
        info['adresa'] += f" Et. {etaj}"
        print(f"Etaj: {etaj}")
    if info['apartament']:
        info['adresa'] += f" Ap. {info['apartament']}"
        print(f"Apartament: {info['apartament']}")
    if cp:
        info['adresa'] += f" CP. {cp}"
    print(f"Adresa completă: {info['adresa']}")
    return info

# Ruta principală pentru încărcarea imaginii
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files['file']
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Deschide imaginea și procesează-o
            image = Image.open(file_path)
            info = proceseaza_fisier(image)

            # Șterge fișierele mai vechi de 24 de ore
            sterge_fisiere_vechi()

            return render_template('index.html', info=info)

    # Apelăm funcția pentru a șterge fișierele vechi la fiecare cerere GET
    sterge_fisiere_vechi()

    return render_template('index.html', info=None)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))