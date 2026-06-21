const API_URL = ''; 

const elNombre = document.getElementById('nombre-mascota');
const elAvatar = document.getElementById('pet-avatar');
const elContenedor = document.getElementById('pet-container');
const elLog = document.getElementById('event-log');
const elFx = document.getElementById('pet-fx');
const elMonedas = document.getElementById('coin-counter');
const roomBg = document.getElementById('room-background');

const barHambre = document.getElementById('bar-hambre');
const barFelicidad = document.getElementById('bar-felicidad');
const barEnergia = document.getElementById('bar-energia');

const panelControles = document.getElementById('control-buttons');
const btnRevivir = document.getElementById('btn-revive');

// --- 1. COMUNICACIÓN CON LA API ---
async function obtenerEstado() {
    try {
        const respuesta = await fetch(`${API_URL}/estado`);
        const json = await respuesta.json();
        actualizarUI(json.data);
    } catch (error) {
        mostrarMensaje('Error de conexión ❌');
    }
}

async function realizarAccion(accion) {
    try {
        const respuesta = await fetch(`${API_URL}/${accion}`, { method: 'POST' });
        const json = await respuesta.json();

        if (respuesta.ok) {
            mostrarMensaje(json.mensaje);
            if(accion !== 'reiniciar') dispararAnimacion(accion);
            setTimeout(() => actualizarUI(json.data), accion === 'reiniciar' ? 0 : 500);
        } else {
            mostrarMensaje(`⚠️ ${json.detail}`);
            dispararEfecto('❓');
        }
    } catch (error) {
        mostrarMensaje('Error en el servidor 🔌');
    }
}

// --- 2. ACTUALIZACIÓN VISUAL ---
function actualizarUI(mascota) {
    elNombre.textContent = mascota.nombre;
    elMonedas.textContent = mascota.monedas;
    
    barHambre.value = mascota.hambre;
    barFelicidad.value = mascota.felicidad;
    barEnergia.value = mascota.energia;

    if (mascota.estado === "fallecido") {
        elAvatar.textContent = "🪦"; 
        elContenedor.className = "pet-dead";
        
        // Muestra el botón de revivir y oculta los otros
        panelControles.style.display = 'none';
        btnRevivir.style.display = 'block';
    } else {
        elAvatar.textContent = "👾"; 
        elContenedor.className = "pet-idle";
        
        // Restaura los botones normales
        panelControles.style.display = 'grid';
        btnRevivir.style.display = 'none';
        roomBg.classList.remove('room-night');
    }
}

function mostrarMensaje(mensaje) {
    elLog.textContent = mensaje;
}

// --- 3. ANIMACIONES MAGNÍFICAS ---
function dispararAnimacion(accion) {
    elContenedor.classList.remove('pet-idle');
    
    if (accion === 'alimentar') {
        elContenedor.classList.add('anim-eat');
        dispararEfecto('🍗');
    } else if (accion === 'jugar') {
        elContenedor.classList.add('anim-play');
        dispararEfecto('✨');
    } else if (accion === 'dormir') {
        // Apaga la luz del cuarto
        roomBg.classList.add('room-night');
        dispararEfecto('💤');
    }

    setTimeout(() => {
        elContenedor.className = 'pet-idle';
        elFx.style.opacity = '0'; 
        // Prende la luz si estaba dormido
        if (accion === 'dormir') roomBg.classList.remove('room-night');
    }, 1500);
}

function dispararEfecto(emoji) {
    elFx.textContent = emoji;
    elFx.style.opacity = '1';
    elFx.style.transition = 'all 1s';
    elFx.style.transform = 'translateY(-30px)';
    
    setTimeout(() => {
        elFx.style.transform = 'translateY(0)';
        elFx.style.opacity = '0';
    }, 1000);
}

obtenerEstado();