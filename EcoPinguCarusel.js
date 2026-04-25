//burger
const hamburguesa = document.querySelector('.hamburguesa');
const menu = document.querySelector('.menu');

hamburguesa.addEventListener('click', () => {
  menu.classList.toggle('activo');
});

//carusel
const slide = document.querySelector('.carousel-slide');
const images = document.querySelectorAll('.carousel-slide img');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');

let index = 0;

function mostrarImagen(i) {
    if (i < 0) {
        index = images.length - 1;
    } else if (i >= images.length) {
        index = 0;
    } else {
        index = i;
    }
    slide.style.transform = `translateX(-${index * 100}%)`;
}

prevBtn.addEventListener('click', () => mostrarImagen(index - 1));
nextBtn.addEventListener('click', () => mostrarImagen(index + 1));

// Inicializar
mostrarImagen(index);

