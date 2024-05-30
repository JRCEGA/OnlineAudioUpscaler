document.getElementById('file-upload').onchange = function() {
    // Mostrar mensaje de procesamiento
    document.getElementById('processing-message').style.display = 'block';
    
    // Preparar datos para enviar
    var formData = new FormData();
    formData.append('file', this.files[0]);

    // Realizar la petición AJAX para cargar el archivo
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/', true);

    // Configurar la lógica de manejo de respuesta
    xhr.onload = function () {
        if (xhr.status === 200) {
            // Ocultar mensaje de procesamiento
            document.getElementById('processing-message').style.display = 'none';
            
            // Mostrar botón de descarga y actualizar el enlace con la ruta del archivo procesado
            var response = JSON.parse(xhr.responseText);
            var downloadButton = document.getElementById('download-link');
            downloadButton.href = '/uploads/' + response.filename;
            downloadButton.style.display = 'block';
        } else {
            // Manejar el error
            alert('Error al procesar el archivo.');
        }
    };

    // Enviar el archivo
    xhr.send(formData);
};
