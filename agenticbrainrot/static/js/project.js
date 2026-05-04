/* Project specific Javascript goes here. */

/* ── ACCESSIBILITY WIDGET ──────────────────────────────────────────────────── */
(function () {
  'use strict';

  const DEFAULTS = { theme: 'system', contrast: 'standard', text: 'standard', motion: 'standard' };
  const LS_KEY = 'a11yPrefs';
  const html = document.documentElement;

  function loadPrefs() {
    try {
      const stored = JSON.parse(localStorage.getItem(LS_KEY) || 'null');
      if (!stored) {
        // Migrate legacy 'theme' key
        const legacy = localStorage.getItem('theme');
        if (legacy === 'dark' || legacy === 'light') {
          const migrated = Object.assign({}, DEFAULTS, { theme: legacy });
          savePrefs(migrated);
          localStorage.removeItem('theme');
          return migrated;
        }
      }
      return Object.assign({}, DEFAULTS, stored || {});
    } catch (_) {
      return Object.assign({}, DEFAULTS);
    }
  }

  function savePrefs(prefs) {
    try { localStorage.setItem(LS_KEY, JSON.stringify(prefs)); } catch (_) {}
  }

  function resolveTheme(prefs) {
    if (prefs.theme === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return prefs.theme;
  }

  function applyPrefs(prefs) {
    html.setAttribute('data-theme', resolveTheme(prefs));
    if (prefs.contrast === 'standard') {
      html.removeAttribute('data-a11y-contrast');
    } else {
      html.setAttribute('data-a11y-contrast', prefs.contrast);
    }
    if (prefs.text === 'standard') {
      html.removeAttribute('data-a11y-text');
    } else {
      html.setAttribute('data-a11y-text', prefs.text);
    }
    if (prefs.motion === 'standard') {
      html.removeAttribute('data-a11y-motion');
    } else {
      html.setAttribute('data-a11y-motion', prefs.motion);
    }
  }

  function reflectPrefs(prefs) {
    ['theme', 'contrast', 'text', 'motion'].forEach(function (key) {
      const radio = document.querySelector('input[name="a11y-' + key + '"][value="' + prefs[key] + '"]');
      if (radio) radio.checked = true;
    });
  }

  // Apply immediately to prevent flash before DOMContentLoaded
  applyPrefs(loadPrefs());

  document.addEventListener('DOMContentLoaded', function () {
    const panel = document.getElementById('a11yPanel');
    const closeBtn = document.getElementById('a11yClose');
    const resetBtn = document.getElementById('a11yReset');

    if (!panel) return;

    let prefs = loadPrefs();
    let lastTrigger = null;

    reflectPrefs(prefs);

    function openPanel(triggerEl) {
      lastTrigger = triggerEl || null;
      panel.classList.add('is-open');
      document.querySelectorAll('.a11y-open-btn').forEach(function (b) {
        b.setAttribute('aria-expanded', 'true');
      });
      if (closeBtn) closeBtn.focus();
    }

    function closePanel() {
      panel.classList.remove('is-open');
      document.querySelectorAll('.a11y-open-btn').forEach(function (b) {
        b.setAttribute('aria-expanded', 'false');
      });
      if (lastTrigger) lastTrigger.focus();
    }

    document.querySelectorAll('.a11y-open-btn').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        panel.classList.contains('is-open') ? closePanel() : openPanel(btn);
      });
    });

    if (closeBtn) closeBtn.addEventListener('click', closePanel);

    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        prefs = Object.assign({}, DEFAULTS);
        savePrefs(prefs);
        applyPrefs(prefs);
        reflectPrefs(prefs);
      });
    }

    ['theme', 'contrast', 'text', 'motion'].forEach(function (key) {
      document.querySelectorAll('input[name="a11y-' + key + '"]').forEach(function (radio) {
        radio.addEventListener('change', function () {
          prefs[key] = radio.value;
          savePrefs(prefs);
          applyPrefs(prefs);
        });
      });
    });

    // Respond to OS theme changes when using system setting
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
        if (prefs.theme === 'system') applyPrefs(prefs);
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && panel.classList.contains('is-open')) closePanel();
    });

    document.addEventListener('click', function (e) {
      if (!panel.classList.contains('is-open')) return;
      if (!e.target.closest('.a11y-open-btn') && !panel.contains(e.target)) closePanel();
    });
  });
}());

// Stat-info tooltip click toggle
document.addEventListener("click", function (e) {
  var el = e.target.closest(".stat-info");
  if (el) {
    e.stopPropagation();
    el.classList.toggle("is-open");
    return;
  }
  // Click anywhere else closes all open tooltips
  document.querySelectorAll(".stat-info.is-open").forEach(function (t) {
    t.classList.remove("is-open");
  });
});
