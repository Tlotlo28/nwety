// Wires up any element with id="theme-toggle" to switch theme on click.
// Call this from any page that includes a toggle button.
(function() {
    function setIcon(btn) {
        if (!window.Icons) return;
        btn.innerHTML = window.Theme.current === 'dark' ? Icons.sun : Icons.moon;
    }

    document.addEventListener('DOMContentLoaded', () => {
        const btn = document.getElementById('theme-toggle');
        if (!btn) return;

        setIcon(btn);
        btn.addEventListener('click', () => {
            window.Theme.toggle();
            setIcon(btn);
        });

        // Also react if the OS theme changes mid-session and user hasn't
        // explicitly chosen one
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
            setIcon(btn);
        });
    });
})();