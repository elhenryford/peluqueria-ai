const formulario = document.getElementById("formulario");

const cliente = document.getElementById("cliente");
const corte = document.getElementById("corte");

const previewCliente = document.getElementById("previewCliente");
const previewCorte = document.getElementById("previewCorte");

const cargando = document.getElementById("cargando");
const imagenResultado = document.getElementById("imagenResultado");


// Vista previa Cliente
cliente.addEventListener("change", function(){

    previewCliente.src = URL.createObjectURL(cliente.files[0]);
    previewCliente.hidden = false;

});


// Vista previa Corte
corte.addEventListener("change", function(){

    previewCorte.src = URL.createObjectURL(corte.files[0]);
    previewCorte.hidden = false;

});


// Enviar formulario
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

    cargando.hidden=false;
    cargando.innerHTML="Generando peinado...";

    let datos=new FormData();

    datos.append("cliente",cliente.files[0]);
    datos.append("corte",corte.files[0]);

    try{

        let respuesta=await fetch("/upload",{

            method:"POST",
            body:datos

        });

        let json=await respuesta.json();

        if(json.ok){

            imagenResultado.src=json.result+"?"+new Date().getTime();
            imagenResultado.hidden=false;

            cargando.innerHTML="Proceso terminado";

        }else{

            cargando.innerHTML=json.error;

        }

    }catch(error){

        cargando.innerHTML="Error de conexión";

    }

});