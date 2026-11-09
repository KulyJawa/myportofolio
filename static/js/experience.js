(() => {
    const root = document.getElementById("experience");
    if (!root) return;

    const searchForm = document.getElementById(
        "experience-search-form"
    );
    const searchInput = document.getElementById("experience-search");
    const list = document.getElementById("experience-list");
    const feedback = document.getElementById("experience-feedback");

    let activeController = null;

    function setFeedback(message, isError = false) {
        feedback.textContent = message;
        feedback.dataset.error = String(isError);
    }

    function createTextElement(tag, className, text) {
        const element = document.createElement(tag);
        element.className = className;
        element.textContent = text ?? "";
        return element;
    }

    function createCard(experience) {
        const card = document.createElement("article");
        card.className = "experience-card";

        const category = createTextElement(
            "span",
            "experience-category",
            experience.category_display
        );

        const title = createTextElement(
            "h2",
            "experience-title",
            experience.title
        );

        const description = createTextElement(
            "p",
            "experience-description",
            experience.description
        );

        const status = createTextElement(
            "p",
            "experience-status",
            experience.is_ongoing
                ? "Sedang berlangsung"
                : "Selesai"
        );

        card.append(category, title, description, status);

        if (experience.starred_by_names) {
            const starredBy = createTextElement(
                "p",
                "experience-starred-by",
                `Diberi star oleh: ${experience.starred_by_names}`
            );

            card.append(starredBy);
        }

        const actions = document.createElement("div");
        actions.className = "experience-card-actions";

        const count = experience.star_count ?? 0;
        const busy = pendingExperiences.has(experience.id);

        if (isAuthenticated) {
            const starButton = document.createElement("button");
            starButton.type = "button";
            starButton.className = "experience-star-button";

            starButton.textContent = experience.is_starred
                ? `★ Batalkan star (${count})`
                : `☆ Beri star (${count})`;

            starButton.setAttribute(
                "aria-pressed",
                String(experience.is_starred)
            );

            starButton.disabled = busy;

            starButton.addEventListener("click", () => {
                const url = root.dataset.starUrl.replace(
                    "00000000-0000-0000-0000-000000000000",
                    experience.id
                );

                runExperienceAction(
                    experience.id,
                    card,
                    url,
                    "POST",
                    {},
                    "Status star berhasil diperbarui."
                );
            });

            actions.append(starButton);
        } else {
            const loginLink = document.createElement("a");
            loginLink.className = "experience-login-link";
            loginLink.href = root.dataset.loginUrl;
            loginLink.textContent = `★ ${count} · Login untuk memberi star`;

            actions.append(loginLink);
        }

        if (canEdit) {
            const editButton = document.createElement("button");
            editButton.type = "button";
            editButton.className = "experience-edit-button";
            editButton.textContent = "Edit";
            editButton.disabled = busy;

            editButton.addEventListener("click", () => {
                openExperienceForm(experience);
            });

            actions.append(editButton);
        }

        if (canDelete) {
            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "experience-delete-button";
            deleteButton.textContent = "Hapus";
            deleteButton.disabled = busy;

            deleteButton.addEventListener("click", () => {
                const confirmed = window.confirm(
                    `Hapus pengalaman "${experience.title}"?`
                );

                if (!confirmed) return;

                runExperienceAction(
                    experience.id,
                    card,
                    detailUrl(experience.id),
                    "DELETE",
                    undefined,
                    "Experience berhasil dihapus."
                );
            });

            actions.append(deleteButton);
        }

        card.append(actions);
        return card;
    }

    async function loadExperiences() {
        // Batalkan pencarian lama jika ada permintaan baru.
        if (activeController) {
            activeController.abort();
        }

        const controller = new AbortController();
        activeController = controller;

        const query = searchInput.value.trim();
        const url = new URL(root.dataset.listUrl, window.location.origin);

        if (query) {
            url.searchParams.set("title", query);
        }

        list.setAttribute("aria-busy", "true");
        list.replaceChildren();
        setFeedback("Memuat pengalaman...");

        try {
            const response = await fetch(url, {
                method: "GET",
                headers: {
                    Accept: "application/json",
                },
                credentials: "same-origin",
                signal: controller.signal,
            });

            if (!response.ok) {
                throw new Error(
                    `Gagal mengambil data (HTTP ${response.status}).`
                );
            }

            const experiences = await response.json();

            if (!Array.isArray(experiences)) {
                throw new Error("Format respons API tidak sesuai.");
            }

            // Respons pencarian lama tidak boleh menimpa hasil terbaru.
            if (activeController !== controller) return;

            const cards = experiences.map(createCard);
            list.replaceChildren(...cards);

            if (experiences.length === 0) {
                setFeedback(
                    query
                        ? "Tidak ada pengalaman yang cocok dengan pencarian."
                        : "Belum ada pengalaman yang ditambahkan."
                );
            } else {
                setFeedback(
                    `${experiences.length} pengalaman ditampilkan.`
                );
            }
        } catch (error) {
            if (
                error.name === "AbortError" ||
                activeController !== controller
            ) {
                return;
            }

            setFeedback(
                error.message || "Terjadi kesalahan saat memuat data.",
                true
            );
        } finally {
            if (activeController === controller) {
                list.setAttribute("aria-busy", "false");
            }
        }
    }

    const canEdit = root.dataset.canEdit === "true";
    const canDelete = root.dataset.canDelete === "true";
    const isAuthenticated = root.dataset.authenticated === "true";
    const pendingExperiences = new Set();

    const dialog = document.getElementById("experience-dialog");
    const experienceForm = document.getElementById("experience-form");
    const dialogTitle = document.getElementById("experience-dialog-title");
    const formError = document.getElementById("experience-form-error");
    const saveButton = document.getElementById("experience-save");
    const cancelButton = document.getElementById("experience-cancel");
    const addButton = document.getElementById("experience-add-button");
    const toast = document.getElementById("experience-toast");

    let editingExperience = null;
    let saving = false;
    let toastTimer = null;

    function notifyExperience(message, isError = false) {
        clearTimeout(toastTimer);

        toast.textContent = message;
        toast.dataset.error = String(isError);
        toast.hidden = false;

        toastTimer = setTimeout(() => {
            toast.hidden = true;
        }, 5000);
    }

    function detailUrl(id) {
        return root.dataset.detailUrl.replace(
            "00000000-0000-0000-0000-000000000000",
            id
        );
    }

    // Ubah waktu dari API menjadi waktu lokal untuk datetime-local.
    function toLocalInput(value) {
        if (!value) return "";

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) return "";

        const localDate = new Date(
            date.getTime() - date.getTimezoneOffset() * 60000
        );

        return localDate.toISOString().slice(0, 19);
    }

    function openExperienceForm(experience = null) {
        if (saving || !canEdit) return;

        editingExperience = experience;
        experienceForm.reset();
        formError.textContent = "";
        toast.hidden = true;

        dialogTitle.textContent = experience
            ? "Edit Experience"
            : "Tambah Experience";

        saveButton.textContent = experience
            ? "Simpan Perubahan"
            : "Tambah Experience";

        experienceForm.elements.namedItem("title").value =
            experience?.title ?? "";

        experienceForm.elements.namedItem("description").value =
            experience?.description ?? "";

        experienceForm.elements.namedItem("category").value =
            experience?.category ?? "full-time";

        experienceForm.elements.namedItem("thumbnail").value =
            experience?.thumbnail ?? "";

        experienceForm.elements.namedItem("ended_at").value =
            toLocalInput(experience?.ended_at);

        dialog.showModal();
        experienceForm.elements.namedItem("title").focus();
    }

    function formatApiErrors(data) {
        if (typeof data?.detail === "string") {
            return data.detail;
        }

        const labels = {
            title: "Judul",
            description: "Deskripsi",
            category: "Kategori",
            thumbnail: "URL gambar",
            ended_at: "Waktu selesai",
            non_field_errors: "Form",
        };

        return Object.entries(data)
            .map(([field, errors]) => {
                const message = Array.isArray(errors)
                    ? errors.join(" ")
                    : String(errors);

                return `${labels[field] ?? field}: ${message}`;
            })
            .join("\n");
    }

    async function writeExperience(url, method, payload) {
        const csrfToken = experienceForm.querySelector(
            "[name=csrfmiddlewaretoken]"
        ).value;

        const response = await fetch(url, {
            method,
            mode: "same-origin",
            credentials: "same-origin",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
            },
            body: JSON.stringify(payload),
        });

        if (response.status === 204) return null;

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error(
                `Respons server tidak dapat dibaca (HTTP ${response.status}).`
            );
        }

        if (!response.ok) {
            throw new Error(
                formatApiErrors(data) ||
                `Permintaan gagal (HTTP ${response.status}).`
            );
        }

        return data;
    }

    addButton?.addEventListener("click", () => {
        openExperienceForm();
    });

    cancelButton.addEventListener("click", () => {
        if (!saving) dialog.close();
    });

    // Cegah modal ditutup dengan Escape saat penyimpanan berjalan.
    dialog.addEventListener("cancel", (event) => {
        if (saving) event.preventDefault();
    });

    experienceForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (saving) return;

        saving = true;
        saveButton.disabled = true;
        cancelButton.disabled = true;
        formError.textContent = "";

        const previousLabel = saveButton.textContent;
        saveButton.textContent = "Menyimpan...";

        try {
            const fields = experienceForm.elements;
            const endedAt = fields.namedItem("ended_at").value;

            const payload = {
                title: fields.namedItem("title").value,
                description: fields.namedItem("description").value,
                category: fields.namedItem("category").value,
                thumbnail: fields.namedItem("thumbnail").value.trim(),
                ended_at: endedAt
                    ? new Date(endedAt).toISOString()
                    : null,
            };

            // Pertahankan waktu asli jika kolomnya tidak diubah.
            if (
                editingExperience &&
                endedAt === toLocalInput(editingExperience.ended_at)
            ) {
                payload.ended_at = editingExperience.ended_at;
            }

            const isEditing = editingExperience !== null;

            const url = isEditing
                ? detailUrl(editingExperience.id)
                : root.dataset.listUrl;

            const method = isEditing ? "PATCH" : "POST";

            await writeExperience(url, method, payload);

            dialog.close();

            notifyExperience(
                isEditing
                    ? "Experience berhasil diperbarui."
                    : "Experience berhasil ditambahkan."
            );

            await loadExperiences();
        } catch (error) {
            const message = error.message || "Gagal menyimpan Experience.";

            formError.textContent = message;

            // Diletakkan dalam dialog agar terlihat ketika modal terbuka.
            dialog.append(toast);
            notifyExperience(message, true);
        } finally {
            saving = false;
            saveButton.disabled = false;
            cancelButton.disabled = false;
            saveButton.textContent = previousLabel;
        }
    });

    // Kembalikan tempat notifikasi ketika modal ditutup.
    dialog.addEventListener("close", () => {
        document.body.append(toast);
    });

    async function runExperienceAction(
        id,
        card,
        url,
        method,
        payload,
        successMessage
    ) {
        if (pendingExperiences.has(id)) return;

        pendingExperiences.add(id);

        const buttons = card.querySelectorAll("button");
        buttons.forEach((button) => {
            button.disabled = true;
        });

        card.setAttribute("aria-busy", "true");

        try {
            await writeExperience(url, method, payload);

            pendingExperiences.delete(id);
            notifyExperience(successMessage);

            // Ambil ulang daftar dengan pencarian yang masih aktif.
            await loadExperiences();
        } catch (error) {
            notifyExperience(
                error.message || "Tindakan gagal. Silakan coba lagi.",
                true
            );
        } finally {
            pendingExperiences.delete(id);

            buttons.forEach((button) => {
                button.disabled = false;
            });

            card.setAttribute("aria-busy", "false");
        }
    }
    searchForm.addEventListener("submit", (event) => {
        event.preventDefault();
        loadExperiences();
    });

    loadExperiences();
})();