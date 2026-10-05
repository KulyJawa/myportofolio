from django.forms import ModelForm, TextInput, Textarea
from main.models import Education
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

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

    def clean_institution(self):
        institution = strip_tags(self.cleaned_data.get("institution", "")).strip()
        if not institution:
            raise ValidationError("Nama institusi tidak boleh hanya berisi tag HTML.")
        return institution
    
    def clean_degree(self):
        degree = strip_tags(self.cleaned_data.get("degree", "")).strip()
        if not degree:
            raise ValidationError("Jenjang / jurusan tidak boleh kosong setelah tag HTML dibersihkan.")
        return degree
    
    def clean_start_year(self):
        start_year = strip_tags(self.cleaned_data.get("start_year", "")).strip()
        if not start_year:
            raise ValidationError("Tahun mulai tidak boleh kosong setelah tag HTML dibersihkan.")
        return start_year

    def clean_end_year(self):
        end_year = strip_tags(self.cleaned_data.get("end_year", "")).strip()
        if not end_year:
            raise ValidationError("Tahun selesai tidak boleh kosong setelah tag HTML dibersihkan.")
        return end_year

    def clean_description(self):
        return strip_tags(self.cleaned_data.get("description") or "").strip()
