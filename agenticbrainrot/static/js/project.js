/* Project specific Javascript goes here. */

/* Project specific Javascript goes here. */

document.addEventListener("DOMContentLoaded", () => {
    const themeSwitcher = document.getElementById("theme-switcher");
    if (themeSwitcher) {
        themeSwitcher.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("theme", newTheme);
            updateThemeIcon(newTheme);
        });

        // Sync icon + a11y labels on load
        const savedTheme = document.documentElement.getAttribute("data-theme");
        updateThemeIcon(savedTheme);
    }

    function updateThemeIcon(theme) {
        const icon = themeSwitcher.querySelector("i");
        if (icon) {
            // Trigger animation
            icon.classList.remove("theme-animate-in");
            void icon.offsetWidth; // Trigger reflow
            icon.classList.add("theme-animate-in");

            if (theme === "dark") {
                icon.classList.remove("fa-moon");
                icon.classList.add("fa-sun");
            } else {
                icon.classList.remove("fa-sun");
                icon.classList.add("fa-moon");
            }
        }

        // Icon-only button: keep an accessible name + tooltip, and expose toggle state
        const nextActionLabel = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
        themeSwitcher.setAttribute("aria-label", nextActionLabel);
        themeSwitcher.setAttribute("title", nextActionLabel);
        themeSwitcher.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");

        // ... existing code ...
    }
});
