document.addEventListener("DOMContentLoaded", function(){

    const formulario = document.getElementById("formulario");

    const cliente = document.getElementById("cliente");
    const corte = document.getElementById("corte");

    const previewCliente = document.getElementById("previewCliente");
    const previewCorte = document.getElementById("previewCorte");

    const cargando = document.getElementById("cargando");
    const imagenResultado = document.getElementById("imagenResultado");

    // Verificar que los elementos existen; no abortar, solo avisar
    if (!formulario || !cliente || !corte || !previewCliente || !previewCorte || !cargando || !imagenResultado) {
        console.error("Elementos del formulario no encontrados en el DOM", {formulario, cliente, corte, previewCliente, previewCorte, cargando, imagenResultado});
    }

    console.log("script.js inicializado");


// Vista previa Cliente
if (cliente && previewCliente) {
    cliente.addEventListener("change", function(){
        console.log("cliente change", cliente.files.length);
        if (cliente.files.length > 0) {
            previewCliente.src = URL.createObjectURL(cliente.files[0]);
            previewCliente.hidden = false;
        }
    });
}

// Vista previa Corte
if (corte && previewCorte) {
    corte.addEventListener("change", function(){
        console.log("corte change", corte.files.length);
        if (corte.files.length > 0) {
            previewCorte.src = URL.createObjectURL(corte.files[0]);
            previewCorte.hidden = false;
        }
    });
}



// Comprimir imagen
function comprimirImagen(file, maxWidth=800, maxHeight=800, quality=0.8) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;
                
                if (width > height) {
                    if (width > maxWidth) {
                        height = Math.round((height * maxWidth) / width);
                        width = maxWidth;
                    }
                } else {
                    if (height > maxHeight) {
                        width = Math.round((width * maxHeight) / height);
                        height = maxHeight;
                    }
                }
                
                canvas.width = width;
                canvas.height = height;
                canvas.getContext('2d').drawImage(img, 0, 0, width, height);
                
                canvas.toBlob((blob) => {
                    const comprimido = new File([blob], file.name, { type: 'image/jpeg' });
                    resolve(comprimido);
                }, 'image/jpeg', quality);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
}

// Enviar formulario
if (formulario) {
    formulario.addEventListener("submit", async function(e){

    e.preventDefault();

    if(cliente.files.length==0){

        alert("Seleccione la foto del cliente");
        return;

    }

    if(corte.files.length==0){

        alert("Seleccione la foto del corte");
        return;

    }

        if (cargando) {
            cargando.hidden=false;
            cargando.innerHTML="Comprimiendo imágenes...";
        }

    // Comprimir imágenes antes de enviar
    const clienteComprimido = await comprimirImagen(cliente.files[0]);
    const corteComprimido = await comprimirImagen(corte.files[0]);

        if (cargando) {
            cargando.innerHTML="Generando peinado...";
        }

    let datos=new FormData();

    datos.append("cliente", clienteComprimido);
    datos.append("corte", corteComprimido);

    // Asegurar que siempre enviamos `cara` en el request.
    // Si existe input con id `cara` y tiene archivo, se usa.
    // Si no, se usa el cliente como respaldo.
    (function ensureOptionalFields(){
        const caraInput = document.getElementById("cara");

        function cloneFile(file, newName){
            try{
                return new File([file], newName, { type: file.type });
            }catch(e){
                // En entornos más antiguos, File() puede fallar; usar Blob como fallback
                try{
                    const b = new Blob([file], { type: file.type });
                    b.name = newName;
                    return b;
                }catch(err){
                    return file;
                }
            }
        }

        if (caraInput && caraInput.files && caraInput.files.length > 0){
            datos.append("cara", caraInput.files[0]);
        }else{
            // clonar cliente
            if (cliente && cliente.files && cliente.files.length > 0){
                const cloned = cloneFile(cliente.files[0], "cara_"+cliente.files[0].name);
                datos.append("cara", cloned);
            }
        }

        // No se envía `peluca` desde la UI visible.
    })();

    // Adjuntar orientación si existe en el formulario, si no, dejar que el backend use el valor por defecto
    const orientElem = document.getElementById("orientacion");
    if (orientElem && orientElem.value) {
        datos.append("orientacion", orientElem.value);
    }

    try{
        console.count("FETCH");
        let respuesta=await fetch("/upload",{

            method:"POST",
            body:datos

        });

        let json=await respuesta.json();
        console.log("respuesta /upload", json);

        if(json.ok){

            if (imagenResultado) {
                imagenResultado.src=json.result+"?"+new Date().getTime();
                imagenResultado.hidden=false;
            }
            if (cargando) cargando.innerHTML="Proceso terminado";

        }else{

            if (cargando) cargando.innerHTML=json.error;

        }

    }catch(error){
        console.error("fetch /upload error:", error);
        console.error("error.message:", error.message);
        console.error("error.stack:", error.stack);
        if (cargando) {
            cargando.innerHTML="Error de conexión: " + error.message;
        }
    }

    });
}})