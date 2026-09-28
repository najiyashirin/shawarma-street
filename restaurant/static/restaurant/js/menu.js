(() => {
    const links = [...document.querySelectorAll('.menu-categories a')];
    const sections = [...document.querySelectorAll('.full-menu-category')];
    const activate = id => links.forEach(link => {
        if (link.hash === '#' + id) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
    });
    links.forEach(link => link.addEventListener('click', () => activate(link.hash.slice(1))));
    if (location.hash) activate(location.hash.slice(1));
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(entries => {
            const visible = entries.filter(entry => entry.isIntersecting);
            if (visible.length) activate(visible[0].target.id);
        }, { rootMargin: '-110px 0px -55% 0px', threshold: 0 });
        sections.forEach(section => observer.observe(section));
    }
})();
