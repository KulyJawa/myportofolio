from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPortfolioOwnerOrEditorOrReadOnly(BasePermission):
    message = "Kamu tidak memiliki izin untuk melakukan tindakan ini."

    def has_permission(self, request, view):
        # Semua pengunjung boleh membaca data.
        if request.method in SAFE_METHODS:
            return True

        # Tindakan perubahan membutuhkan pengguna yang sudah login.
        if not request.user.is_authenticated:
            return False

        # Pemilik portofolio (superuser) boleh mengelola seluruh data.
        if request.user.is_superuser:
            return True

        # Anggota grup Editor hanya boleh mengedit data.
        if request.method in ("PUT", "PATCH"):
            return request.user.groups.filter(name="Editor").exists()

        # Pengguna lainnya tidak boleh mengubah data.
        return False