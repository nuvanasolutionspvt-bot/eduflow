document.addEventListener('DOMContentLoaded', function () {
  const currentPath = document.body.dataset.currentPath || '';

  const sidebarLinks = document.querySelectorAll('.sidebar .nav-link[href]');
  const matchingLinks = Array.from(sidebarLinks).filter((link) => {
    try {
      const href = link.getAttribute('href') || '';
      if (!href || href === '#' || href.startsWith('javascript:')) return false;
      if (href === '/') return currentPath === '/';
      return currentPath.startsWith(href);
    } catch (e) {
      // ignore failures and keep link as-is
      return false;
    }
  });

  const activeLink = matchingLinks.sort((a, b) => {
    const hrefA = (a.getAttribute('href') || '').length;
    const hrefB = (b.getAttribute('href') || '').length;
    return hrefB - hrefA;
  })[0];

  if (activeLink) {
    activeLink.classList.add('active');
  }

  const deleteForms = document.querySelectorAll('.delete-form');
  deleteForms.forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (!confirm('Are you sure you want to delete this record?')) {
        event.preventDefault();
      }
    });
  });

  const searchInput = document.getElementById('searchInput');
  const table = document.getElementById('studentTable');

  if (searchInput && table) {
    searchInput.addEventListener('input', function () {
      const query = this.value.toLowerCase();
      const rows = table.querySelectorAll('tbody tr');
      rows.forEach(function (row) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    });
  }

  if (window.jQuery && jQuery.fn.select2) {
    jQuery('.select2').select2({ width: '100%' });
  }

  const importForm = document.querySelector('form[data-import-form="true"]');
  if (importForm) {
    const submitButton = importForm.querySelector('[data-import-submit="true"]');
    const submitText = importForm.querySelector('[data-import-submit-text="true"]');
    const submitIcon = importForm.querySelector('[data-import-submit-icon="true"]');
    const overlay = importForm.parentElement?.querySelector('[data-import-loading-overlay="true"]');

    importForm.addEventListener('submit', function () {
      if (submitButton) {
        submitButton.disabled = true;
      }
      if (submitIcon) {
        submitIcon.className = 'spinner-border spinner-border-sm me-2';
      }
      if (submitText) {
        submitText.textContent = 'Importing...';
      }
      if (overlay) {
        overlay.classList.remove('d-none');
        overlay.setAttribute('aria-hidden', 'false');
      }
    });
  }

  const studentForm = document.querySelector('form[data-student-form="true"]');
  if (studentForm) {
    const translationUrl = studentForm.dataset.transliterateUrl || '/students/transliterate/';
    const debounceMap = new Map();
    const requestState = new Map();
    const abortMap = new Map();
    const lastAutoValueMap = new Map();
    const csrfToken =
      studentForm.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
    const getTargetField = (source) => {
      const sourceName = source?.getAttribute('name') || '';
      if (!sourceName || sourceName.endsWith('_mr')) {
        return null;
      }
      return studentForm.querySelector(`[name="${sourceName}_mr"]`);
    };
    const translatableSources = Array.from(
      studentForm.querySelectorAll('input[type="text"][name], textarea[name]')
    ).filter((field) => getTargetField(field));

    const fetchTranslation = (value, signal) => {
      return fetch(translationUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
        signal,
        body: JSON.stringify({ text: value }),
      }).then((response) => {
        if (!response.ok) {
          throw new Error(`Translation failed with status ${response.status}`);
        }
        return response.json();
      });
    };

    translatableSources.forEach((source) => {
      const target = getTargetField(source);
      const targetKey = target.name;

      if (!target) {
        return;
      }

      target.addEventListener('input', () => {
        const targetValue = (target.value || '').trim();
        const sourceValue = (source.value || '').trim();
        const lastAutoValue = (lastAutoValueMap.get(targetKey) || '').trim();

        if (!targetValue || targetValue === sourceValue || targetValue === lastAutoValue) {
          delete target.dataset.autotranslateDisabled;
          return;
        }

        target.dataset.autotranslateDisabled = 'true';
      });

      const syncTarget = ({ force = false } = {}) => {
        const sourceValue = source.value || '';
        const targetValue = target.value || '';
        const lastAutoValue = lastAutoValueMap.get(targetKey) || '';

        if (
          !force &&
          target.dataset.autotranslateDisabled === 'true' &&
          targetValue.trim() !== sourceValue.trim() &&
          targetValue.trim() !== lastAutoValue.trim()
        ) {
          return;
        }

        if (!sourceValue.trim()) {
          target.value = '';
          lastAutoValueMap.set(targetKey, '');
          delete target.dataset.autotranslateDisabled;
          return;
        }

        if (debounceMap.has(targetKey)) {
          window.clearTimeout(debounceMap.get(targetKey));
        }

        if (abortMap.has(targetKey)) {
          abortMap.get(targetKey).abort();
        }

        debounceMap.set(
          targetKey,
          window.setTimeout(() => {
            const requestId = (requestState.get(targetKey) || 0) + 1;
            requestState.set(targetKey, requestId);
            const controller = new AbortController();
            abortMap.set(targetKey, controller);

            fetchTranslation(sourceValue, controller.signal)
              .then((payload) => {
                const currentTargetValue = target.value || '';
                const currentLastAutoValue = lastAutoValueMap.get(targetKey) || '';
                if (
                  !force &&
                  target.dataset.autotranslateDisabled === 'true' &&
                  currentTargetValue.trim() !== sourceValue.trim() &&
                  currentTargetValue.trim() !== currentLastAutoValue.trim()
                ) {
                  return;
                }
                if (requestState.get(targetKey) !== requestId) {
                  return;
                }
                const nextValue = payload.text || '';
                target.value = nextValue;
                lastAutoValueMap.set(targetKey, nextValue);
                delete target.dataset.autotranslateDisabled;
              })
              .catch((error) => {
                if (error && error.name === 'AbortError') {
                  return;
                }
                // Keep the field unchanged when translation service is unavailable.
              })
              .finally(() => {
                if (abortMap.get(targetKey) === controller) {
                  abortMap.delete(targetKey);
                }
              });
          }, 300)
        );
      };

      source.addEventListener('input', () => syncTarget());
      source.addEventListener('paste', () => syncTarget());
      source.addEventListener('change', () => syncTarget());
      syncTarget();
    });
  }
});
