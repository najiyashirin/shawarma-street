(() => {
    const restaurantToggle = document.querySelector('.restaurant-menu-button');
    const restaurantNavigation = document.getElementById('restaurant-navigation');
    const restaurantMobileLayout = window.matchMedia('(max-width: 760px)');

    function setRestaurantNavigation(expanded, restoreFocus = false) {
        restaurantNavigation.classList.toggle('restaurant-navigation-open', expanded);
        restaurantToggle.setAttribute('aria-expanded', String(expanded));
        restaurantToggle.setAttribute('aria-label', expanded ? 'Close navigation' : 'Open navigation');
        if (restoreFocus) restaurantToggle.focus();
    }

    if (restaurantToggle && restaurantNavigation) {
        restaurantToggle.addEventListener('click', () => {
            setRestaurantNavigation(restaurantToggle.getAttribute('aria-expanded') !== 'true');
        });
        restaurantNavigation.querySelectorAll('a').forEach(restaurantLink => {
            restaurantLink.addEventListener('click', () => setRestaurantNavigation(false));
        });
        document.addEventListener('keydown', restaurantEvent => {
            if (restaurantEvent.key === 'Escape' && restaurantToggle.getAttribute('aria-expanded') === 'true') {
                setRestaurantNavigation(false, true);
            }
        });
        document.addEventListener('click', restaurantEvent => {
            if (!restaurantNavigation.contains(restaurantEvent.target) && !restaurantToggle.contains(restaurantEvent.target)) {
                setRestaurantNavigation(false);
            }
        });
        restaurantMobileLayout.addEventListener('change', () => setRestaurantNavigation(false));
    }

    const restaurantMotionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (!('IntersectionObserver' in window) || restaurantMotionPreference.matches) return;

    const restaurantRevealObserver = new IntersectionObserver(restaurantEntries => {
        restaurantEntries.forEach(restaurantEntry => {
            if (restaurantEntry.isIntersecting) {
                restaurantEntry.target.classList.remove('restaurant-reveal-pending');
                restaurantRevealObserver.unobserve(restaurantEntry.target);
            }
        });
    }, { threshold: 0.12 });

    document.querySelectorAll('.restaurant-reveal').forEach(restaurantSection => {
        restaurantSection.classList.add('restaurant-reveal-pending');
        restaurantRevealObserver.observe(restaurantSection);
    });
})();
