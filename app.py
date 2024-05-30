import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
import numpy as np
import soundfile as sf
import noisereduce as nr
import librosa
import scipy.signal

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def convert_to_mono(data):
    if len(data.shape) == 2:  # Si data es estéreo, convierte a mono
        return np.mean(data, axis=1)
    return data

def apply_bandpass_filter(data, lowcut, highcut, rate, order=5):
    nyquist = 0.5 * rate
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = scipy.signal.butter(order, [low, high], btype='band')
    y = scipy.signal.lfilter(b, a, data)
    return y

def apply_highpass_filter(data, cutoff, rate, order=5):
    nyquist = 0.5 * rate
    high = cutoff / nyquist
    b, a = scipy.signal.butter(order, high, btype='high')
    y = scipy.signal.lfilter(b, a, data)
    return y

def enhance_audio(data, rate):
    # Aplicar reducción de ruido con parámetros ajustados
    reduced_noise = nr.reduce_noise(
        y=data, 
        sr=rate, 
        thresh_n_mult_nonstationary=1.5,  # Ajustar el umbral
        stationary=False,
    )
    
    # Normalizar el audio
    normalized_audio = librosa.util.normalize(reduced_noise)
    
    # Aplicar ecualización simple (amplificación de frecuencias altas)
    band1 = apply_bandpass_filter(normalized_audio, 1000, 3000, rate, order=2)
    band2 = apply_bandpass_filter(normalized_audio, 3000, 8000, rate, order=2)
    
    # Ajustar la ganancia de las bandas
    enhanced_audio = normalized_audio + 0.3 * band1 + 0.3 * band2
    
    # Aplicar filtro de paso alto para mejorar claridad
    highpass_audio = apply_highpass_filter(enhanced_audio, 5000, rate, order=2)
    
    # Combinar todo
    final_audio = enhanced_audio + 0.2 * highpass_audio
    
    return final_audio

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Asegúrate de que hay un archivo en la petición
        if 'file' not in request.files:
            return {"error": "No file part"}, 400
        file = request.files['file']
        # Si el usuario no selecciona un archivo, el navegador podría
        # enviar una parte sin nombre de archivo
        if file.filename == '':
            return {"error": "No selected file"}, 400
        if file and allowed_file(file.filename):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            # Leer el archivo y procesarlo
            data, rate = sf.read(filepath)
            data_mono = convert_to_mono(data)
            enhanced_audio = enhance_audio(data_mono, rate)
            
            # Guardar el archivo procesado
            processed_filename = 'processed_' + file.filename
            processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
            sf.write(processed_filepath, enhanced_audio, rate)
            
            # En lugar de redirigir, devolver una respuesta JSON
            return {"success": True, "filename": processed_filename}
    
    # Si es una solicitud GET, simplemente renderiza la plantilla HTML
    return render_template('index.html')

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'wav'}

if __name__ == "__main__":
    app.run(debug=True)
