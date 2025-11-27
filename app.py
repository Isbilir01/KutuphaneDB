from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from config import DB_CONFIG
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'kutuphane_secret_key_2024'

# Veritabanı bağlantısı
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ANASAYFA - Dashboard
@app.route('/')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Toplam kitap sayısı
    cursor.execute("SELECT COUNT(*) as toplam FROM kitap")
    toplam_kitap = cursor.fetchone()['toplam']
    
    # Toplam adet
    cursor.execute("SELECT SUM(adet) as toplam_adet FROM kitap")
    toplam_adet = cursor.fetchone()['toplam_adet'] or 0
    
    # Toplam okuyucu
    cursor.execute("SELECT COUNT(*) as toplam FROM okuyucu")
    toplam_okuyucu = cursor.fetchone()['toplam']
    
    # Aktif ödünç (iade_tarihi NULL olanlar)
    cursor.execute("SELECT COUNT(*) as aktif FROM odunc WHERE iade_tarihi IS NULL")
    aktif_odunc = cursor.fetchone()['aktif']
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', 
                         toplam_kitap=toplam_kitap,
                         toplam_adet=toplam_adet,
                         toplam_okuyucu=toplam_okuyucu,
                         aktif_odunc=aktif_odunc)

# KİTAP İŞLEMLERİ
@app.route('/kitaplar')
def kitap_listesi():
    search = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search:
        cursor.execute("""
            SELECT k.*, y.ad as yazar_adi, ya.adi as yayinevi_adi 
            FROM kitap k
            LEFT JOIN yazar y ON k.yazar_id = y.yazar_id
            LEFT JOIN yayinevi ya ON k.yayinevi_id = ya.yayinevi_id
            WHERE k.kitap_adi LIKE %s
            ORDER BY k.kitap_id ASC
        """, (f'%{search}%',))
    else:
        cursor.execute("""
            SELECT k.*, y.ad as yazar_adi, ya.adi as yayinevi_adi 
            FROM kitap k
            LEFT JOIN yazar y ON k.yazar_id = y.yazar_id
            LEFT JOIN yayinevi ya ON k.yayinevi_id = ya.yayinevi_id
            ORDER BY k.kitap_id ASC
        """)
    
    kitaplar = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('kitap_listesi.html', kitaplar=kitaplar, search=search)

@app.route('/kitap/ekle', methods=['GET', 'POST'])
def kitap_ekle():
    if request.method == 'POST':
        kitap_adi = request.form['kitap_adi']
        yazar_id = request.form['yazar_id']
        yayinevi_id = request.form['yayinevi_id']
        basim_yili = request.form['basim_yili']
        tur = request.form['tur']
        adet = request.form['adet']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO kitap (kitap_adi, yazar_id, yayinevi_id, basim_yili, tur, adet)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (kitap_adi, yazar_id, yayinevi_id, basim_yili, tur, adet))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Kitap başarıyla eklendi!', 'success')
        return redirect(url_for('kitap_listesi'))
    
    # GET isteği için yazar ve yayınevi listelerini getir
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM yazar ORDER BY ad")
    yazarlar = cursor.fetchall()
    cursor.execute("SELECT * FROM yayinevi ORDER BY adi")
    yayinevleri = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('kitap_ekle.html', yazarlar=yazarlar, yayinevleri=yayinevleri)

@app.route('/kitap/duzenle/<int:kitap_id>', methods=['GET', 'POST'])
def kitap_duzenle(kitap_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        kitap_adi = request.form['kitap_adi']
        yazar_id = request.form['yazar_id']
        yayinevi_id = request.form['yayinevi_id']
        basim_yili = request.form['basim_yili']
        tur = request.form['tur']
        adet = request.form['adet']
        
        cursor.execute("""
            UPDATE kitap 
            SET kitap_adi=%s, yazar_id=%s, yayinevi_id=%s, basim_yili=%s, tur=%s, adet=%s
            WHERE kitap_id=%s
        """, (kitap_adi, yazar_id, yayinevi_id, basim_yili, tur, adet, kitap_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Kitap başarıyla güncellendi!', 'success')
        return redirect(url_for('kitap_listesi'))
    
    cursor.execute("SELECT * FROM kitap WHERE kitap_id=%s", (kitap_id,))
    kitap = cursor.fetchone()
    cursor.execute("SELECT * FROM yazar ORDER BY ad")
    yazarlar = cursor.fetchall()
    cursor.execute("SELECT * FROM yayinevi ORDER BY adi")
    yayinevleri = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('kitap_duzenle.html', kitap=kitap, yazarlar=yazarlar, yayinevleri=yayinevleri)

@app.route('/kitap/sil/<int:kitap_id>')
def kitap_sil(kitap_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kitap WHERE kitap_id=%s", (kitap_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Kitap başarıyla silindi!', 'success')
    return redirect(url_for('kitap_listesi'))

# YAZAR İŞLEMLERİ
@app.route('/yazarlar')
def yazar_listesi():
    search = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search:
        cursor.execute("SELECT * FROM yazar WHERE ad LIKE %s ORDER BY yazar_id ASC", (f'%{search}%',))
    else:
        cursor.execute("SELECT * FROM yazar ORDER BY yazar_id ASC")
    
    yazarlar = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('yazar_listesi.html', yazarlar=yazarlar, search=search)

@app.route('/yazar/ekle', methods=['GET', 'POST'])
def yazar_ekle():
    if request.method == 'POST':
        ad = request.form['ad']
        ulke = request.form['ulke']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO yazar (ad, ulke) VALUES (%s, %s)", (ad, ulke))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Yazar başarıyla eklendi!', 'success')
        return redirect(url_for('yazar_listesi'))
    
    return render_template('yazar_ekle.html')

@app.route('/yazar/duzenle/<int:yazar_id>', methods=['GET', 'POST'])
def yazar_duzenle(yazar_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        ad = request.form['ad']
        ulke = request.form['ulke']
        
        cursor.execute("UPDATE yazar SET ad=%s, ulke=%s WHERE yazar_id=%s", (ad, ulke, yazar_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Yazar başarıyla güncellendi!', 'success')
        return redirect(url_for('yazar_listesi'))
    
    cursor.execute("SELECT * FROM yazar WHERE yazar_id=%s", (yazar_id,))
    yazar = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('yazar_duzenle.html', yazar=yazar)

@app.route('/yazar/sil/<int:yazar_id>')
def yazar_sil(yazar_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM yazar WHERE yazar_id=%s", (yazar_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Yazar başarıyla silindi!', 'success')
    return redirect(url_for('yazar_listesi'))

# YAYINEVİ İŞLEMLERİ
@app.route('/yayinevleri')
def yayinevi_listesi():
    search = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search:
        cursor.execute("SELECT * FROM yayinevi WHERE adi LIKE %s ORDER BY yayinevi_id ASC", (f'%{search}%',))
    else:
        cursor.execute("SELECT * FROM yayinevi ORDER BY yayinevi_id ASC")
    
    yayinevleri = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('yayinevi_listesi.html', yayinevleri=yayinevleri, search=search)

@app.route('/yayinevi/ekle', methods=['GET', 'POST'])
def yayinevi_ekle():
    if request.method == 'POST':
        adi = request.form['adi']
        adres = request.form['adres']
        telno = request.form['telno']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO yayinevi (adi, adres, telno) VALUES (%s, %s, %s)", (adi, adres, telno))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Yayınevi başarıyla eklendi!', 'success')
        return redirect(url_for('yayinevi_listesi'))
    
    return render_template('yayinevi_ekle.html')

@app.route('/yayinevi/duzenle/<int:yayinevi_id>', methods=['GET', 'POST'])
def yayinevi_duzenle(yayinevi_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        adi = request.form['adi']
        adres = request.form['adres']
        telno = request.form['telno']
        
        cursor.execute("UPDATE yayinevi SET adi=%s, adres=%s, telno=%s WHERE yayinevi_id=%s", 
                      (adi, adres, telno, yayinevi_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Yayınevi başarıyla güncellendi!', 'success')
        return redirect(url_for('yayinevi_listesi'))
    
    cursor.execute("SELECT * FROM yayinevi WHERE yayinevi_id=%s", (yayinevi_id,))
    yayinevi = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('yayinevi_duzenle.html', yayinevi=yayinevi)

@app.route('/yayinevi/sil/<int:yayinevi_id>')
def yayinevi_sil(yayinevi_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM yayinevi WHERE yayinevi_id=%s", (yayinevi_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Yayınevi başarıyla silindi!', 'success')
    return redirect(url_for('yayinevi_listesi'))

# OKUYUCU İŞLEMLERİ
@app.route('/okuyucular')
def okuyucu_listesi():
    search = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search:
        cursor.execute("SELECT * FROM okuyucu WHERE ad LIKE %s ORDER BY okuyucu_id ASC", (f'%{search}%',))
    else:
        cursor.execute("SELECT * FROM okuyucu ORDER BY okuyucu_id ASC")
    
    okuyucular = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('okuyucu_listesi.html', okuyucular=okuyucular, search=search)

@app.route('/okuyucu/ekle', methods=['GET', 'POST'])
def okuyucu_ekle():
    if request.method == 'POST':
        ad = request.form['ad']
        telefon = request.form['telefon']
        email = request.form['email']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO okuyucu (ad, telefon, email) VALUES (%s, %s, %s)", 
                      (ad, telefon, email))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Okuyucu başarıyla eklendi!', 'success')
        return redirect(url_for('okuyucu_listesi'))
    
    return render_template('okuyucu_ekle.html')

@app.route('/okuyucu/duzenle/<int:okuyucu_id>', methods=['GET', 'POST'])
def okuyucu_duzenle(okuyucu_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        ad = request.form['ad']
        telefon = request.form['telefon']
        email = request.form['email']
        
        cursor.execute("UPDATE okuyucu SET ad=%s, telefon=%s, email=%s WHERE okuyucu_id=%s", 
                      (ad, telefon, email, okuyucu_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Okuyucu başarıyla güncellendi!', 'success')
        return redirect(url_for('okuyucu_listesi'))
    
    cursor.execute("SELECT * FROM okuyucu WHERE okuyucu_id=%s", (okuyucu_id,))
    okuyucu = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('okuyucu_duzenle.html', okuyucu=okuyucu)

@app.route('/okuyucu/sil/<int:okuyucu_id>')
def okuyucu_sil(okuyucu_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM okuyucu WHERE okuyucu_id=%s", (okuyucu_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Okuyucu başarıyla silindi!', 'success')
    return redirect(url_for('okuyucu_listesi'))

# ÖDÜNÇ İŞLEMLERİ
@app.route('/oduncler')
def odunc_listesi():
    search = request.args.get('search', '')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search:
        cursor.execute("""
            SELECT o.*, k.kitap_adi, ok.ad as okuyucu_adi
            FROM odunc o
            JOIN kitap k ON o.kitap_id = k.kitap_id
            JOIN okuyucu ok ON o.okuyucu_id = ok.okuyucu_id
            WHERE k.kitap_adi LIKE %s OR ok.ad LIKE %s
            ORDER BY o.odunc_id ASC
        """, (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("""
            SELECT o.*, k.kitap_adi, ok.ad as okuyucu_adi
            FROM odunc o
            JOIN kitap k ON o.kitap_id = k.kitap_id
            JOIN okuyucu ok ON o.okuyucu_id = ok.okuyucu_id
            ORDER BY o.odunc_id ASC
        """)
    
    oduncler = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('odunc_listesi.html', oduncler=oduncler, search=search)

@app.route('/odunc/ver', methods=['GET', 'POST'])
def odunc_ver():
    if request.method == 'POST':
        kitap_id = request.form['kitap_id']
        okuyucu_id = request.form['okuyucu_id']
        alis_tarihi = request.form['alis_tarihi']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO odunc (kitap_id, okuyucu_id, alis_tarihi, iade_tarihi)
            VALUES (%s, %s, %s, NULL)
        """, (kitap_id, okuyucu_id, alis_tarihi))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Kitap başarıyla ödünç verildi!', 'success')
        return redirect(url_for('odunc_listesi'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM kitap ORDER BY kitap_adi")
    kitaplar = cursor.fetchall()
    cursor.execute("SELECT * FROM okuyucu ORDER BY ad")
    okuyucular = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('odunc_ver.html', kitaplar=kitaplar, okuyucular=okuyucular)

@app.route('/odunc/teslim/<int:odunc_id>', methods=['POST'])
def odunc_teslim(odunc_id):
    iade_tarihi = request.form.get('iade_tarihi', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE odunc SET iade_tarihi=%s WHERE odunc_id=%s", (iade_tarihi, odunc_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Kitap başarıyla teslim alındı!', 'success')
    return redirect(url_for('odunc_listesi'))

if __name__ == '__main__':
    app.run(debug=True)
