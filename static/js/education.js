// Halaman Education: AJAX, debouncing, modal, dan star tanpa reload.
(() => {
    const root = document.getElementById('education');
    if (!root) return;
    const config = root.dataset;
    const grid = document.getElementById('grid');
    const searchInput = document.getElementById('search-input');
    const searchForm = document.getElementById('education-search-form');
    const educationForm = document.getElementById('education-form');
    const formErrors = document.getElementById('education-form-errors');
    const states = ['loading', 'error', 'empty', 'grid'];
    const uuidPlaceholder = '00000000-0000-0000-0000-000000000000';
    let controller;
    let requestNumber = 0;
    let debounceTimer;

    function showState(active) {
        states.forEach(id => document.getElementById(id).classList.toggle('hide', id !== active));
        grid.setAttribute('aria-busy', String(active === 'loading'));
    }

    function escapeHtml(value) {
        return String(value ?? '')
            .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;').replaceAll("'", '&#39;');
    }

    function actionUrl(template, id) {
        return template.replace(uuidPlaceholder, encodeURIComponent(id));
    }

    function csrfToken() {
        return root.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    function toast(title, message, type = 'error') {
        // showToast memakai textContent, sehingga pesan server tidak dianggap HTML.
        showToast(title, message, type, type === 'error' ? 6000 : 3000);
    }

    async function readJson(response) {
        if (!(response.headers.get('Content-Type') || '').includes('application/json')) {
            throw new Error(response.status === 403
                ? 'Permintaan ditolak. Muat ulang halaman, lalu coba lagi.'
                : `Respons server tidak dapat dibaca (HTTP ${response.status}).`);
        }
        return response.json();
    }

    function validationMessage(data) {
        const errors = Object.entries(data.errors || {}).flatMap(([field, items]) => {
            const input = educationForm?.elements.namedItem(field);
            const label = input?.labels?.[0]?.textContent || field;
            return items.map(error => `${label}: ${error.message}`);
        });
        return errors.join(' ') || data.message || 'Data gagal disimpan. Silakan coba lagi.';
    }

    function buildCard(item) {
        const edu = item.fields;
        const article = document.createElement('article');
        article.className = 'education-card';
        // Semua nilai dinamis yang masuk innerHTML harus di-escape, termasuk atribut.
        article.innerHTML = `
            <span class="education-year">${escapeHtml(edu.start_year)} &ndash; ${escapeHtml(edu.end_year)}</span>
            <h2>${escapeHtml(edu.institution)}</h2>
            <p class="education-degree">${escapeHtml(edu.degree)}</p>
            ${edu.description ? `<p class="education-desc">${escapeHtml(edu.description)}</p>` : ''}
            <div class="education-card-actions" style="flex-wrap: wrap;"></div>`;
        const actions = article.querySelector('.education-card-actions');
        if (config.authenticated === 'true') {
            const starButton = document.createElement('button');
            starButton.type = 'button';
            starButton.className = 'button button-star';
            function updateStar(starred, count) {
                starButton.classList.toggle('is-starred', starred);
                starButton.setAttribute('aria-pressed', String(starred));
                starButton.textContent = `★ ${starred ? 'Unstar' : 'Star'} (${count})`;
            }
            updateStar(edu.is_starred, edu.star_count);
            starButton.addEventListener('click', async () => {
                starButton.disabled = true;
                try {
                    const response = await fetch(actionUrl(config.starUrl, item.pk), {
                        method: 'POST',
                        headers: { 'Accept': 'application/json', 'X-CSRFToken': csrfToken() },
                    });
                    const data = await readJson(response);
                    if (!response.ok) throw new Error(data.message || 'Gagal memperbarui star.');
                    updateStar(data.is_starred, data.star_count);
                    toast('Berhasil', data.message, 'success');
                } catch (error) {
                    toast('Star gagal diperbarui', error.message);
                } finally {
                    starButton.disabled = false;
                }
            });
            actions.appendChild(starButton);
        } else {
            const starLink = document.createElement('a');
            starLink.className = 'button button-star';
            starLink.href = config.loginUrl;
            starLink.textContent = `★ ${edu.star_count} · Login untuk memberi star`;
            actions.appendChild(starLink);
        }
        if (config.superuser === 'true' || config.editor === 'true') {
            const editLink = document.createElement('a');
            editLink.href = actionUrl(config.editUrl, item.pk);
            editLink.className = 'button button-secondary button-edit';
            editLink.textContent = 'Edit';
            actions.appendChild(editLink);
        }
        if (config.superuser === 'true') {
            // Pertahankan fitur hapus Tugas 4: POST biasa dengan CSRF dan konfirmasi.
            const deleteForm = document.createElement('form');
            deleteForm.method = 'post';
            deleteForm.action = actionUrl(config.deleteUrl, item.pk);
            const token = document.createElement('input');
            token.type = 'hidden';
            token.name = 'csrfmiddlewaretoken';
            token.value = csrfToken();
            const deleteButton = document.createElement('button');
            deleteButton.type = 'submit';
            deleteButton.className = 'button button-danger';
            deleteButton.textContent = 'Hapus';
            deleteForm.append(token, deleteButton);
            deleteForm.addEventListener('submit', event => {
                if (!window.confirm(`Hapus pendidikan ${edu.institution}?`)) event.preventDefault();
            });
            actions.appendChild(deleteForm);
        }
        return article;
    }

    async function fetchEducation() {
        controller?.abort();
        controller = new AbortController();
        const currentRequest = ++requestNumber;
        showState('loading');
        const url = new URL(config.listUrl, window.location.origin);
        const query = searchInput.value.trim();
        if (query) url.searchParams.set('q', query);
        try {
            const response = await fetch(url, {
                headers: { 'Accept': 'application/json' }, signal: controller.signal,
            });
            if (!response.ok) throw new Error(`Gagal mengambil data (HTTP ${response.status}).`);
            const data = await readJson(response);
            // Respons pencarian lama tidak boleh menimpa hasil pencarian terbaru.
            if (currentRequest !== requestNumber) return;
            if (!Array.isArray(data)) throw new Error('Format daftar pendidikan tidak valid.');
            grid.replaceChildren(...data.map(buildCard));
            showState(data.length ? 'grid' : 'empty');
        } catch (error) {
            if (error.name === 'AbortError' || currentRequest !== requestNumber) return;
            showState('error');
            toast('Gagal memuat pendidikan', error.message);
        }
    }

    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        controller?.abort();
        requestNumber++;
        debounceTimer = setTimeout(fetchEducation, 300);
    });
    searchForm.addEventListener('submit', event => {
        event.preventDefault();
        clearTimeout(debounceTimer);
        fetchEducation();
    });
    document.getElementById('retry-education').addEventListener('click', () => {
        clearTimeout(debounceTimer);
        fetchEducation();
    });

    // Modal hanya ada untuk superuser. Pengunjung dan Editor tetap bisa memuat daftar.
    if (educationForm) {
        educationForm.addEventListener('submit', async event => {
            event.preventDefault();
            const submitButton = educationForm.querySelector('[type=submit]');
            if (submitButton.disabled) return;
            submitButton.disabled = true;
            submitButton.textContent = 'Menyimpan...';
            formErrors.hidden = true;
            formErrors.textContent = '';
            try {
                const response = await fetch(config.createUrl, {
                    method: 'POST', headers: { 'Accept': 'application/json' },
                    // FormData sudah membawa csrfmiddlewaretoken dari {% csrf_token %}.
                    body: new FormData(educationForm),
                });
                const data = await readJson(response);
                if (!response.ok) throw new Error(validationMessage(data));
                educationForm.reset();
                const modal = document.getElementById('add-education-modal');
                if (modal.matches(':popover-open')) modal.hidePopover();
                toast('Berhasil', data.message, 'success');
                clearTimeout(debounceTimer);
                await fetchEducation(); // Pertahankan kata pencarian yang terlihat di input.
            } catch (error) {
                formErrors.textContent = error.message;
                formErrors.hidden = false;
                toast('Gagal menambahkan pendidikan', error.message);
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = 'Tambah Pendidikan';
            }
        });
    }
    fetchEducation();
})();
