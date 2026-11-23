// Add/remove rows for Django inline formsets.
//
// Markup contract (see recipe_form.html):
//   [data-formset="<prefix>"]   section wrapping one formset + its management form
//   [data-formset-rows]         container the rows live in
//   [data-formset-row]          one row (one form)
//   <template data-formset-empty>  formset.empty_form, using the "__prefix__" index
//   [data-formset-add]          button that appends a new row
//   [data-formset-remove]       button inside a row that removes it
//
// Removing a row ticks its hidden DELETE checkbox and hides it, rather than
// deleting the element, so Django sees the deletion and skips validating it.

(function () {
    function updateHopTimePlaceholder(row) {
        const use = row.querySelector('[data-hop-use]');
        const time = row.querySelector('[data-hop-time]');
        if (use && time) {
            time.placeholder = use.value === 'dry_hop' ? 'days' : 'min';
        }
    }

    function setUpFormset(section) {
        const prefix = section.dataset.formset;
        const totalForms = section.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);
        const rows = section.querySelector('[data-formset-rows]');
        const template = section.querySelector('template[data-formset-empty]');
        const addButton = section.querySelector('[data-formset-add]');

        section.addEventListener('click', function (event) {
            const removeButton = event.target.closest('[data-formset-remove]');
            if (!removeButton) return;
            const row = removeButton.closest('[data-formset-row]');
            const deleteBox = row.querySelector(`input[name$="-DELETE"]`);
            if (deleteBox) deleteBox.checked = true;
            row.classList.add('d-none');
        });

        section.addEventListener('change', function (event) {
            if (event.target.matches('[data-hop-use]')) {
                updateHopTimePlaceholder(event.target.closest('[data-formset-row]'));
            }
        });

        addButton.addEventListener('click', function () {
            const index = parseInt(totalForms.value, 10);
            const html = template.innerHTML.replace(/__prefix__/g, String(index));
            rows.insertAdjacentHTML('beforeend', html);
            totalForms.value = String(index + 1);
            const row = rows.lastElementChild;
            updateHopTimePlaceholder(row);
            const firstInput = row.querySelector('select, input:not([type="hidden"])');
            if (firstInput) firstInput.focus();
        });

        section.querySelectorAll('[data-formset-rows] [data-formset-row]').forEach(updateHopTimePlaceholder);
    }

    document.querySelectorAll('[data-formset]').forEach(setUpFormset);
})();
