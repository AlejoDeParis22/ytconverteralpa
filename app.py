from flask import Flask, render_template, request, send_file, redirect, url_for, flash, Response
import os
import yt_dlp
import uuid
import re
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def es_url_valida(url):
    patron = r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+'
    return re.match(patron, url)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form.get('url')
        if not video_url or not es_url_valida(video_url):
            flash("Por favor ingresa un enlace válido de YouTube.")
            return redirect(url_for('index'))

        unique_id = str(uuid.uuid4())
        temp_output = os.path.join(DOWNLOAD_FOLDER, f"{unique_id}.%(ext)s")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_output,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }

        try:
            # Extraer información del video para obtener el título.
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl_info:
                info = ydl_info.extract_info(video_url, download=False)
            title = info.get('title', unique_id)
            title_sanitizado = re.sub(r'[\\/*?:"<>|]', "", title)

            # Descargar el audio.
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Buscar el archivo generado.
            archivo_descarga = None
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f.startswith(unique_id):
                    archivo_descarga = os.path.join(DOWNLOAD_FOLDER, f)
                    break

            if not archivo_descarga:
                flash("No se encontró el archivo descargado.")
                return redirect(url_for('index'))
            
            # Leer el archivo en memoria.
            with open(archivo_descarga, 'rb') as f:
                data = f.read()
            os.remove(archivo_descarga)
            
            # Enviar el archivo como respuesta.
            return Response(
                data,
                mimetype="audio/mpeg",
                headers={"Content-Disposition": f"attachment;filename={title_sanitizado}.mp3"}
            )
        except Exception as e:
            flash(f"Error al procesar el video: {e}")
            return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
