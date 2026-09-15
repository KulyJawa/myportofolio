from django.forms import ModelForm, TextInput, Textarea
from main.models import Education

class EducationForm(ModelForm):
    class Meta:
        model = Education
        fields = ["institution", "degree", "start_year", "end_year", "description"]
        labels = {
            "institution": "Nama Institusi / Sekolah",
            "degree": "Jenjang / Jurusan",
            "start_year": "Tahun Mulai",
            "end_year": "Tahun Selesai",
            "description": "Deskripsi / Catatan Tambahan",
        }
        widgets = {
            "institution": TextInput(attrs={"placeholder": "misal: Universitas Indonesia"}),
            "degree": TextInput(attrs={"placeholder": "misal: S1 Sistem Informasi"}),
            "start_year": TextInput(attrs={"placeholder": "misal: 2025"}),
            "end_year": TextInput(attrs={"placeholder": "misal: 2029 atau Present"}),
            "description": Textarea(attrs={"placeholder": "Tuliskan fokus studi atau pencapaian...", "rows": 3}),
        }