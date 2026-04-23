// Tiny theme manager. Loads BEFORE any page content renders so we never see
// a flash of the wrong theme (FOUC).
(function() {
    const STORAGE_KEY = 'nwety-theme';

    function getSavedTheme() {
        try {
            return localStorage.getItem(STORAGE_KEY);
        } catch { return null; }
    }

    function getSystemPreference() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        // Keep the mobile browser chrome bar matching the theme
        const meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', theme === 'dark' ? '#1A1816' : '#FAF7F2');
    }

    function saveTheme(theme) {
        try { localStorage.setItem(STORAGE_KEY, theme); } catch {}
    }

    // Resolve initial theme: saved > system > light
    const initial = getSavedTheme() || getSystemPreference();
    applyTheme(initial);

    // Expose a tiny API for the UI toggle
    window.Theme = {
        get current() {
            return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
        },
        toggle() {
            const next = this.current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            saveTheme(next);
            return next;
        },
        set(theme) {
            applyTheme(theme);
            saveTheme(theme);
        },
    };
})();