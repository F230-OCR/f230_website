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
            'apartament': '', 'bloc': '', 'localitate': '', 'judet': '', 'cp': '', 'telefon': '', 'doiani': ''
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
        try:
            text = proceseaza_zona(coord, idx, image)
            if idx == 0:  # Prenume
                if text and text[0] == 'l' and text[0] != 'I':  # Corectare 'l' în 'I'
                    text = 'I' + text[1:]
                info['prenume'] = capitalize_words(filtru_nume(text))
            elif idx == 1:  # Nume
                if text and text[0] == 'l' and text[0] != 'I':  # Corectare 'l' în 'I'
                    text = 'I' + text[1:]
                info['nume'] = capitalize_words(filtru_nume(text))
            elif idx == 2:  # Inițiala tatălui
                info['initiala_tatalui'] = filtru_litere(text)
            elif idx == 3:  # Strada
                strada = capitalize_words(text)
            elif idx == 4:  # Număr
                nr = text.lstrip('0')
            elif idx == 5:  # CNP
                info['cnp'] = filtru_cifre(text)
            elif idx == 6:  # Email
                text.replace(" @", "@")  # Elimină spațiul din fața simbolului @
                # before the word com we have to put a dot, but if there is a dot before com, we don't have to put another one
                text = text.replace(' ', '.')  # Replace spaces with dots
                text = text.replace('..', '.')  # Replace double dots with single dots
                text = text.replace('com.', 'com')  # Replace com. with com
                #define find
                if text.find('.com') == -1:
                    text = text.replace('com', '.com')  # Add . before com
                info['email'] = text
            elif idx == 7:  # Județ
                judet = capitalize_words(text)
            elif idx == 8:  # Localitate
                text = text.replace('-', ' ')  # Înlocuiește cratimele cu spațiu
                text = text.replace(',', ' ')  # Înlocuiește virgulele cu spațiu
                localitate = capitalize_words(text)
            elif idx == 9:  # Cod poștal
                cp = filtru_cifre(text)
            elif idx == 10:  # Bloc 
                bloc = text.upper()
            elif idx == 11:  # Scara
                info['scara'] = text.upper()
            elif idx == 12:  # etaj
                etaj = text.upper()
            elif idx == 13:  # Apartament
                info['apartament'] = text
            elif idx == 14: #telefon
                info['telefon'] = text
            elif idx == 15: #2 ani
                if text!='':
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)