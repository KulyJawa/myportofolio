// Halaman Education menggunakan API Django REST Framework.
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
        states.forEach(id => {
            document.getElementById(id).classList.toggle('hide', id !== active);
        });
        grid.setAttribute('aria-busy', String(active === 'loading'));
    }

    function escapeHtml(value) {
        return String(value ?? '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    function actionUrl(template, id) {
        return template.replace(uuidPlaceholder, encodeURIComponent(id));
    }

    function csrfToken() {
        return root.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    function toast(title, message, type = 'error') {
        showToast(title, message, type, type === 'error' ? 6000 : 3000);
    }

    async function readJson(response) {
        // DELETE berhasil tidak memiliki isi respons.
        if (response.status === 204) return null;

        const contentType = response.headers.get('Content-Type') || '';
        if (!contentType.includes('application/json')) {
            throw new Error(
                `Respons server tidak dapat dibaca (HTTP ${response.status}).`
            );
        }

        return response.json();
    }

    function validationMessage(data) {
        // Error permission, autentikasi, atau objek tidak ditemukan.
        if (typeof data?.detail === 'string') {
            return data.detail;
        }

        // Error validasi DRF: {"institution": ["Pesan kesalahan"]}
        const messages = Object.entries(data || {}).flatMap(([field, errors]) => {
            const input = educationForm?.elements.namedItem(field);
            const label = input?.labels?.[0]?.textContent?.trim() || field;
            const items = Array.isArray(errors) ? errors : [errors];

            return items.map(message => `${label}: ${String(message)}`);
        });

        return messages.join(' ') || 'Permintaan gagal diproses.';
    }

    async function writeApi(url, method, payload) {
        const options = {
            method,
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
        };

        if (payload !== undefined) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(payload);
        }

        const response = await fetch(url, options);
        const data = await readJson(response);

        if (!response.ok) {
            throw new Error(validationMessage(data));
        }

        return data;
    }

    function buildCard(edu) {
        // Respons DRF langsung berisi field, tanpa pembungkus "fields".
        const article = document.createElement('article');
        article.className = 'education-card';

        article.innerHTML = `
            <span class="education-year">
                ${escapeHtml(edu.start_year)} &ndash; ${escapeHtml(edu.end_year)}
            </span>
            <h2>${escapeHtml(edu.institution)}</h2>
            <p class="education-degree">${escapeHtml(edu.degree)}</p>
            ${edu.description
                ? `<p class="education-desc">${escapeHtml(edu.description)}</p>`
                : ''}
            <div class="education-card-actions" style="flex-wrap: wrap;"></div>
        `;

        const actions = article.querySelector('.education-card-actions');

        if (config.authenticated === 'true') {
            const starButton = document.createElement('button');
            starButton.type = 'button';
            starButton.className = 'button button-star';
            starButton.classList.toggle('is-starred', edu.is_starred);
            starButton.setAttribute('aria-pressed', String(edu.is_starred));
            starButton.textContent =
                `★ ${edu.is_starred ? 'Unstar' : 'Star'} (${edu.star_count})`;

            starButton.addEventListener('click', async () => {
                if (starButton.disabled) return;
                starButton.disabled = true;

                try {
                    const data = await writeApi(
                        actionUrl(config.starUrl, edu.id),
                        'POST',
                        {}
                    );

                    toast(
                        'Berhasil',
                        data.is_starred ? 'Star ditambahkan.' : 'Star dibatalkan.',
                        'success'
                    );

                    clearTimeout(debounceTimer);
                    await fetchEducation();
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
            starLink.textContent =
                `★ ${edu.star_count} · Login untuk memberi star`;
            actions.appendChild(starLink);
        }

        if (config.superuser === 'true' || config.editor === 'true') {
            const editLink = document.createElement('a');
            editLink.href = actionUrl(config.editUrl, edu.id);
            editLink.className = 'button button-secondary button-edit';
            editLink.textContent = 'Edit';
            actions.appendChild(editLink);
        }

        if (config.superuser === 'true') {
            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'button button-danger';
            deleteButton.textContent = 'Hapus';

            deleteButton.addEventListener('click', async () => {
                if (deleteButton.disabled) return;
                if (!window.confirm(`Hapus pendidikan ${edu.institution}?`)) {
                    return;
                }

                deleteButton.disabled = true;

                try {
                    await writeApi(
                        actionUrl(config.deleteUrl, edu.id),
                        'DELETE'
                    );

                    toast('Berhasil', 'Pendidikan berhasil dihapus.', 'success');
                    clearTimeout(debounceTimer);
                    await fetchEducation();
                } catch (error) {
                    toast('Gagal menghapus pendidikan', error.message);
                } finally {
                    deleteButton.disabled = false;
                }
            });

            actions.appendChild(deleteButton);
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

        // Sesuai parameter pencarian pada education_list.
        if (query) {
            url.searchParams.set('institution', query);
        }

        try {
            const response = await fetch(url, {
                credentials: 'same-origin',
                headers: { 'Accept': 'application/json' },
                signal: controller.signal,
            });

            const data = await readJson(response);

            if (!response.ok) {
                throw new Error(validationMessage(data));
            }

            // Hasil pencarian lama tidak boleh menimpa hasil terbaru.
            if (currentRequest !== requestNumber) return;

            if (!Array.isArray(data)) {
                throw new Error('Format daftar pendidikan tidak valid.');
            }

            grid.replaceChildren(...data.map(buildCard));
            showState(data.length ? 'grid' : 'empty');
        } catch (error) {
            if (error.name === 'AbortError' || currentRequest !== requestNumber) {
                return;
            }

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

    // Form tambah hanya ditampilkan kepada superuser.
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
                const fields = new FormData(educationForm);
                const payload = {};

                for (const field of [
                    'institution',
                    'degree',
                    'start_year',
                    'end_year',
                    'description',
                ]) {
                    payload[field] = fields.get(field) ?? '';
                }

                await writeApi(config.createUrl, 'POST', payload);

                educationForm.reset();

                const modal = document.getElementById('add-education-modal');
                if (modal.matches(':popover-open')) {
                    modal.hidePopover();
                }

                toast(
                    'Berhasil',
                    'Pendidikan berhasil ditambahkan.',
                    'success'
                );

                clearTimeout(debounceTimer);
                await fetchEducation();
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