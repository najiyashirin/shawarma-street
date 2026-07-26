document.addEventListener("DOMContentLoaded", () => {
    const menuButton = document.querySelector(".menu-button");
    const navigation = document.querySelector(".site-header nav");

    if (menuButton && navigation) {
        menuButton.setAttribute("aria-expanded", "false");

        menuButton.addEventListener("click", () => {
            const isOpen = navigation.classList.toggle("is-open");
            menuButton.setAttribute("aria-expanded", String(isOpen));
            menuButton.setAttribute("aria-label", isOpen ? "Close menu" : "Open menu");
            menuButton.textContent = isOpen ? "×" : "☰";
        });

        navigation.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                navigation.classList.remove("is-open");
                menuButton.setAttribute("aria-expanded", "false");
                menuButton.setAttribute("aria-label", "Open menu");
                menuButton.textContent = "☰";
            });
        });

        document.addEventListener("click", event => {
            if (
                navigation.classList.contains("is-open") &&
                !navigation.contains(event.target) &&
                !menuButton.contains(event.target)
            ) {
                navigation.classList.remove("is-open");
                menuButton.setAttribute("aria-expanded", "false");
                menuButton.setAttribute("aria-label", "Open menu");
                menuButton.textContent = "☰";
            }
        });
    }

    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener("click", event => {
            const targetId = link.getAttribute("href");
            if (!targetId || targetId === "#") return;

            const target = document.querySelector(targetId);
            if (target) {
                event.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });
});
