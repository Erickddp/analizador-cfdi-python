document.addEventListener('DOMContentLoaded', () => {
    // === THEME TOGGLE ===
    const themeBtn = document.getElementById('theme-toggle');
    const html = document.documentElement;

    // Check local storage or system preference
    const savedTheme = localStorage.getItem('theme');
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';

    const currentTheme = savedTheme || systemTheme;
    html.setAttribute('data-theme', currentTheme);

    // Update button visibility (managed by CSS but good for state)

    themeBtn.addEventListener('click', () => {
        const existingTheme = html.getAttribute('data-theme');
        const newTheme = existingTheme === 'dark' ? 'light' : 'dark';

        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    // === CAROUSEL (RESPONSIVE & TOUCH) ===
    const track = document.getElementById('carouselTrack');
    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');

    if (track && track.children.length > 0) {
        const slides = Array.from(track.children);
        let currentIndex = 0;

        // Touch handling variables
        let touchStartX = 0;
        let touchEndX = 0;

        const updateCarousel = () => {
            const width = track.getBoundingClientRect().width;
            track.style.transform = `translateX(-${currentIndex * width}px)`;
        };

        const nextSlide = () => {
            currentIndex = (currentIndex + 1) % slides.length;
            updateCarousel();
        };

        const prevSlide = () => {
            currentIndex = (currentIndex - 1 + slides.length) % slides.length;
            updateCarousel();
        };

        nextBtn.addEventListener('click', nextSlide);
        prevBtn.addEventListener('click', prevSlide);

        // Resize observer for robust width updates
        const resizeObserver = new ResizeObserver(() => {
            // Disable transition temporarily to prevent jumping during resize
            track.style.transition = 'none';
            updateCarousel();
            // Re-enable transition after a small delay
            setTimeout(() => {
                track.style.transition = 'transform 0.5s cubic-bezier(0.25, 1, 0.5, 1)';
            }, 50);
        });

        resizeObserver.observe(track);

        // === SWIPE SUPPORT ===
        track.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        track.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, { passive: true });

        const handleSwipe = () => {
            const threshold = 50; // Minimum distance for swipe
            if (touchStartX - touchEndX > threshold) {
                nextSlide(); // Swiped Left
            }
            if (touchEndX - touchStartX > threshold) {
                prevSlide(); // Swiped Right
            }
        };
    }
});
