/* Project specific Javascript goes here. */

document.addEventListener('DOMContentLoaded', () => {
  const themeSwitcher = document.getElementById('theme-switcher');
  if (themeSwitcher) {
    themeSwitcher.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      updateThemeIcon(newTheme);
    });

    // Sync icon on load
    const savedTheme = document.documentElement.getAttribute('data-theme');
    updateThemeIcon(savedTheme);
  }

  function updateThemeIcon(theme) {
    const icon = themeSwitcher.querySelector('i');
    if (icon) {
      // Trigger animation
      icon.classList.remove('theme-animate-in');
      void icon.offsetWidth; // Trigger reflow
      icon.classList.add('theme-animate-in');

      if (theme === 'dark') {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
      } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
      }
    }
    // Also update text if needed, but here we just use the button title or icon
    const text = themeSwitcher.querySelector('.theme-text');
    if (text) {
        text.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    }
  }
});
