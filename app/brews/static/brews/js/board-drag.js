// Dashboard board: drag a batch to another status column (SortableJS).
//
// The card moves straight away; the server is told in the background and
// sends back the re-rendered card. If saving fails, the card goes back where
// it came from and an error is shown. On phones (board-tabs.js) a card can
// also be dropped onto a status tab. The "Move to …" button on each card is
// the non-drag way to do the same thing.
(function () {
    const board = document.querySelector('.board');
    if (!board || typeof Sortable === 'undefined') return;

    const live = document.getElementById('board-live');
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    const csrfToken = csrfInput ? csrfInput.value : '';

    function cardsIn(list) {
        return list.querySelectorAll(':scope > .brew-card');
    }

    function refreshCounts() {
        board.querySelectorAll('.board-column').forEach(function (column) {
            const list = column.querySelector('.board-cards');
            const count = cardsIn(list).length;
            column.querySelector('.board-column-header .count').textContent = count;
            list.querySelector('.board-empty').hidden = count > 0;
            const tabCount = document.querySelector('#tab-' + column.dataset.status + ' .count');
            if (tabCount) tabCount.textContent = count;
        });
    }

    function announce(text) {
        if (live) live.textContent = text;
    }

    function showError(text) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.setAttribute('role', 'alert');
        alert.textContent = text;
        const close = document.createElement('button');
        close.type = 'button';
        close.className = 'btn-close';
        close.setAttribute('data-bs-dismiss', 'alert');
        close.setAttribute('aria-label', 'Close');
        alert.appendChild(close);
        document.querySelector('main').prepend(alert);
    }

    // The attention list describes the old status, so drop the moved batch.
    function clearAttention(sessionId) {
        const item = document.querySelector('.attention-list li[data-session="' + sessionId + '"]');
        if (!item) return;
        const list = item.parentElement;
        item.remove();
        if (!list.children.length) list.closest('.attention-card').remove();
    }

    function save(card, from, oldIndex, to) {
        const name = card.querySelector('.card-title').textContent.trim();
        refreshCounts();
        fetch(card.dataset.statusUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json', 'X-CSRFToken': csrfToken },
            body: new URLSearchParams({ status: to.dataset.status }),
        })
            .then(function (response) {
                if (!response.ok) throw new Error(response.status);
                return response.json();
            })
            .then(function (data) {
                // Swap in the server's card: new "Move to" button and day counts.
                const fresh = document.createElement('div');
                fresh.innerHTML = data.card.trim();
                card.replaceWith(fresh.firstElementChild);
                clearAttention(card.dataset.session);
                announce(data.message);
            })
            .catch(function () {
                from.insertBefore(card, cardsIn(from)[oldIndex] || from.querySelector('.board-empty'));
                refreshCounts();
                showError('Couldn’t move ' + name + '. Check your connection and try again.');
                announce('Move failed. ' + name + ' is back where it was.');
            });
    }

    // Letting go of a dragged card also counts as a click on it, which would
    // follow the card's link and open the batch. Swallow that one click.
    let swallowClick = false;
    document.addEventListener('click', function (event) {
        if (!swallowClick) return;
        swallowClick = false;
        event.preventDefault();
        event.stopPropagation();
    }, true);

    const shared = {
        group: 'board',
        fallbackTolerance: 5,       // a drag starts after 5px of movement, so clicks stay clicks
        onStart: function () { swallowClick = false; },
        onEnd: function () {
            swallowClick = true;
            // Taps on phones send their click a moment later; after that, clicks are real again.
            setTimeout(function () { swallowClick = false; }, 400);
        },
        sort: false,                // columns are ordered by brew date, not by hand
        draggable: '.brew-card',
        filter: '.brew-card-actions',
        preventOnFilter: false,     // keep the "Move to" button clickable
        forceFallback: true,        // same mouse/touch dragging everywhere; links don't get dragged
        fallbackOnBody: true,
        delay: 200,
        delayOnTouchOnly: true,     // on phones, a short press starts a drag so scrolling still works
        animation: 150,
        ghostClass: 'brew-card-ghost',
        chosenClass: 'brew-card-chosen',
        dragClass: 'brew-card-dragging',
    };

    board.querySelectorAll('.board-cards').forEach(function (list) {
        Sortable.create(list, Object.assign({}, shared, {
            onAdd: function (event) { save(event.item, event.from, event.oldIndex, list); },
        }));
    });

    // Phone tabs accept drops too: the card moves into that tab's column.
    document.querySelectorAll('.board-tab').forEach(function (tab) {
        Sortable.create(tab, Object.assign({}, shared, {
            group: { name: 'board', pull: false, put: true },
            onAdd: function (event) {
                const list = document.querySelector('#column-' + tab.dataset.status + ' .board-cards');
                list.prepend(event.item);
                save(event.item, event.from, event.oldIndex, list);
            },
        }));
    });
})();
