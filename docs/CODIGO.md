# Documentación del sitio LUMKO

Este proyecto es una landing page estática hecha con HTML, CSS y JavaScript puro. La intención es mantenerla simple, rápida de abrir y fácil de ajustar sin depender de frameworks.

## Estructura

```text
.
├── index.html
├── src/
│   ├── styles.css
│   └── script.js
├── assets/
│   ├── hero/
│   │   └── homebanner.jpg
│   └── reference/
│       └── inspiracion.jpg
├── icons/
├── images/
├── logo/
├── lottie/
├── content/
│   ├── empresa.md
│   └── servicios.md
├── docs/
│   ├── CODIGO.md
│   └── IMAGE_GENERATION.md
└── tools/
    └── generate_images.py
```

## Cómo Funciona

`index.html` contiene toda la estructura de la landing: navegación, banner principal, beneficios, paquetes, portafolio/carrusel, llamada a la acción y footer.

`src/styles.css` define el sistema visual: colores, tipografías, espaciados, responsive, hero con imagen de fondo, tarjetas, carrusel y estados interactivos. El diseño está pensado mobile-first y luego se ajusta con media queries para escritorio.

`src/script.js` controla la interacción: menú móvil, animaciones de entrada con `IntersectionObserver` y carrusel de clientes con flechas, dots y autoplay. También respeta `prefers-reduced-motion` para reducir animaciones si el usuario lo tiene configurado.

`images/` contiene los screenshots de clientes que alimentan el carrusel de “Marcas que confían en LUMKO”.

`icons/` contiene los íconos de beneficios del bloque oscuro.

`assets/hero/homebanner.jpg` es la imagen de fondo del banner principal.

`content/` guarda los textos fuente originales usados para construir la landing.

`tools/generate_images.py` permite generar imágenes con la API configurada en `.env`. La explicación completa está en `docs/IMAGE_GENERATION.md`.

## Qué Se Podría Mejorar

- Convertir los datos de paquetes y clientes a un archivo JSON para no repetir HTML manualmente.
- Optimizar imágenes a WebP/AVIF y agregar versiones responsive con `srcset`.
- Agregar links reales a WhatsApp, Instagram y proyectos del portafolio.
- Separar el carrusel en una función reusable si se agregan más sliders.
- Añadir una página o modal de detalle para cada paquete.
- Mejorar SEO con Open Graph, favicon y datos estructurados.
- Revisar rendimiento con Lighthouse cuando el diseño esté cerrado.
- Agregar una validación visual en móvil real, especialmente en 375px y 430px.
