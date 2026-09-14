Nama : Emil Ananta Kautsar

NPM : 2506622121

Kelas : PBP A

Selamat Siang!



### Tugas 1

1.Ya saya menggunakan elemen-elemen semantik di html5, saya menggunakan '<header>', '<nav>', '<section>' dan juga '<article>'. Macam macam tag ini memberikan struktur yang jelas pada halaman website nya. Ini memudahkan saya saat nanti melakukan pemeliharaan kode, daripada hanya memakai tag '<div>' yang ditumpuk.

2.Tantangan yang saya jumpai yaitu pada tata letak utama pada penyesuaian grid asimetris di bagian *hero* dan card skills agar tetap proporsional di layar yang sempit seperti hp. Strategi evaluasi yang saya terapkan adalah:
-menerapkan 'repeat(auto-fit, minmax(260px, 1fr))' pada *grid* card skilss sehingga otomatis saat menyesuaikan tata letak layar tanpa ada elemen yang terpotong.

3.Batasan yang saya rasakan saat ini, tiap saya ada pembaruan skills atau informasi baru yang ingin dimasukkan ke porto. Saya harus mengedit dan mengoding ulang file HTML nya secara manual. Kedepannya, saya ingin membuat website portofolio saya ini bisa dikelola secara dinamis lewat panel admin, yang mungkin membutuhkan database dan arsitektur MVT django. 


AI Disclosure:
Dalam pengerjaan tugas 1 ini, saya menggunakan bantuan AI (gemini) untuk bertanya terkait pembuatan section di website ini. 
 -Bertanya bentuk section yang baik dan enak dilihat seperti apa.
 -bagaimana cara membuat tulisan yang seperti dibungkus dengan kotak (karena saya kepikiran design website saya untuk bagian skills seperti itu)
 



### Tugas 2

1.Alur yang terjadi saat membuka portofolio baru adalah, saat user membuka halaman 'education', Django menerima permintaan user dan mencari URL yang sesuai. Di dalam main/urls.py, ada "education/" yang sudah terhubung dengan fungsi show_education yang nanti saat alamat tersebut dibuka, django menjalankan fungsi show_education yang ada di bagian view. Lalu ada Education.objects.all() yang digunakan untuk mengambil semua data riwayat pendidikan yang disimpan di database. Setelah data nya tersedia, view menjalankan render(request, "education.html", context). education.html akan menggunakan data dari context tersebut untuk menampilkan setiap riwayat pendidikan. Hasilnya adalah halaman HTML yang dikirim ke browser dan dapat dilihat oleh user.

2.Karena dengan menyimpan data portofolio di model, membuat pengelolaan datanya menjadi lebih rapi. Template lebih fokus untuk menampilkan informasi yang diberikan, kalau model digunakan untuk menyimpan dan mengelola datanya. Cara yang seperti ini juga memudahkan kita karena misal ingin menambahkan informasi baru, kita hanya perlu menambahkan data lewat database atau Django Admin tanpa harus mengubah isi kodingan HTML nya.

3.Makemigration fungsi nya untuk membaca perubahan yang dibuat pada models.py. Sementara migrate fungsinya untuk menerapkan file migrasi nya ke database. jadi perubahan yang sebelumnya cuma tercatat dalam file migrasi benar benar diterapkan. Contoh nya saat bikin model Education yang punya atribut institution, degree, start_year, dan end_year, maka perlu menjalankan python manage.py makemigrations. Perintah ini akan membuat file migrasi baru, misal 01_education.py. Setalah itu, python manage.py migrate dijalankan.


AI Disclosure:
Dalam pengerjaan tugas 2 ini, saya menggunakan bantuan AI (gemini) untuk bertanya terkait menyelesaikan tugas ini.
 -Bertanya tentang styling css yang simple 
 -Meminta perbaikan/koreksi code saat menambahkan code hasil tutorial 2