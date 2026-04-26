//burger
const hamburguesa = document.querySelector('.hamburguesa');
const menu = document.querySelector('.menu');

hamburguesa.addEventListener('click', () => {
  menu.classList.toggle('activo');
});

// Carrusel circular robusto
document.querySelectorAll(".carousel-container").forEach(container => {
    const slide = container.querySelector(".carousel-slide");
    const prevBtn = container.querySelector(".prevBtn");
    const nextBtn = container.querySelector(".nextBtn");

    let counter = 0;
    const images = slide.querySelectorAll("img");

    // Función para obtener tamaño dinámico (mejor en responsive)
    const getSize = () => images[0].getBoundingClientRect().width;

    // Inicial
    slide.style.transform = `translateX(${-getSize() * counter}px)`;
    slide.style.transition = "transform 0.4s ease-in-out";

    // Función para mover carrusel
    const moveSlide = () => {
        slide.style.transform = `translateX(${-getSize() * counter}px)`;
    };

    // Deshabilitar botones mientras se anima
    const disableButtons = () => {
        nextBtn.disabled = true;
        prevBtn.disabled = true;
    };
    const enableButtons = () => {
        nextBtn.disabled = false;
        prevBtn.disabled = false;
    };

    slide.addEventListener("transitionend", enableButtons);

    nextBtn.addEventListener("click", () => {
        disableButtons();
        counter++;
        if (counter >= images.length) {
            counter = 0; 
        }
        moveSlide();
    });

    prevBtn.addEventListener("click", () => {
        disableButtons();
        counter--;
        if (counter < 0) {
            counter = images.length - 1; 
        }
        moveSlide();
    });

    // Recalcular tamaño si la ventana cambia
    window.addEventListener("resize", () => {
        moveSlide();
    });
});


function ejecutarBusqueda() {
    const query = document.getElementById("searchInput").value.toLowerCase().trim();
    if (!query) return;

    // Selecciona h1, h2, h3 y p
    const elementos = document.querySelectorAll("h1, h2, h3, p");
    let found = false;

    elementos.forEach(el => {
        // Limpia estilos previos
        el.style.backgroundColor = "";
        el.style.color = "";

        if (el.textContent.toLowerCase().includes(query)) {
            el.style.backgroundColor = "#bbf1a2"; // resalta coincidencia
            el.style.color = "#000";
            el.scrollIntoView({ behavior: "smooth", block: "center" });
            found = true;
        }
    });

    if (!found) {
        alert("No se encontraron coincidencias 🐧");
    }
}


document.getElementById("searchBtn").addEventListener("click", ejecutarBusqueda);

document.getElementById("searchInput").addEventListener("keyup", (event) => {
    if (event.key === "Enter") {
        ejecutarBusqueda();
    }
});
