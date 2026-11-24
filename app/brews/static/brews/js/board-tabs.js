// Dashboard board on phones: show one status column at a time behind tabs.
//
// The tabs only take effect below 640px (see .board-tabbed in app.css);
// wider screens keep all columns side by side. Without JavaScript the
// columns simply stack. The last chosen tab is remembered per browser.
(function () {
    const tabList = document.querySelector('.board-tabs');
    const board = document.querySelector('.board');
    if (!tabList || !board) return;

    const STORAGE_KEY = 'yeastmode.boardTab';
    const tabs = Array.from(tabList.querySelectorAll('[role="tab"]'));

    function remembered() {
        try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
    }

    function remember(status) {
        try { localStorage.setItem(STORAGE_KEY, status); } catch (e) { /* private mode */ }
    }

    function select(tab, moveFocus) {
        tabs.forEach(function (other) {
            const active = other === tab;
            other.setAttribute('aria-selected', active ? 'true' : 'false');
            other.tabIndex = active ? 0 : -1;
            document.getElementById(other.getAttribute('aria-controls'))
                .classList.toggle('is-active', active);
        });
        if (moveFocus) tab.focus();
        remember(tab.dataset.status);
    }

    tabs.forEach(function (tab, index) {
        tab.addEventListener('click', function () { select(tab, false); });
        // Arrow keys, Home and End move between tabs (WAI-ARIA tabs pattern).
        tab.addEventListener('keydown', function (event) {
            const last = tabs.length - 1;
            const target = {
                ArrowRight: index === last ? 0 : index + 1,
                ArrowLeft: index === 0 ? last : index - 1,
                Home: 0,
                End: last,
            }[event.key];
            if (target === undefined) return;
            event.preventDefault();
            select(tabs[target], true);
        });
    });

    // Start on the remembered tab, else the first one.
    const start = tabs.find(function (tab) { return tab.dataset.status === remembered(); }) || tabs[0];
    select(start, false);
    tabList.hidden = false;
    board.classList.add('board-tabbed');
})();
