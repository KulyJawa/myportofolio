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



 ### Tugas 3

 1.Karena dengan ModelForm, saya bisa secara otomatis mengubah atribut pada model menjadi input form HTML sesuai tipe data, contoh nya batas maksimum karakter dan jenis inputnya. Lalu untuk kewajiban {% csrf_token %} ini gunanya untuk memastikan kalau permintaan POST itu asalnya dari form resmi dari situs saya sendiri. Hal ini dapat mencegah permintaan palsu dari pihak lain untuk mengubah atau memanipulasi data tanpa izin.

2.Mengapa JSON lebih disukai dalam pengembangan aplikasi web modern dibandingkan XML? itu karena JSON formatnya lebih ringkas (tidak memerlukan tag pembuka dan penutup), tidak seperti XML. Ini membuat ukuran datanya lebih kecil, dan proses pengiriman data bisa lebih cepat. Struktur key value nya JSON juga lebih mudah dibaca dan dipahami.

3.Alur pengembalian data portofolio dalam bentuk JSON dan alasan kenapa perlu proses serialization:
    jadi yang pertama itu dari klien yang mengirim permintaan HTTP GET ke endpoint /api/education/. Django lalu mencocokan URL nya dan menjalankan view get_education_json. View akan mengambil data pendidikan dari basis data lewat Django ORM dengan Education.object.all(). Data itu akan diubah menjadi format JSON melalui serializers.serialize('json', educations) dan dikirim ke klien dengan HttpResponse.
    Untuk proses serialization ini diperlukan karena objek model django adalah objek Python yang kompleks dan tidak bisa dikirim secara langsung lewat HTTP. 

AI Disclosure:
Dalam tugas 3 ini, saya menggunakan bantuan AI (Gemini) untuk bertanya terkait menyelesaikan tugas ini.
    - Meminta bantuan AI untuk mengecek ulang code yang sudah kubuat
    - Meminta AI untuk meyakinkan apakah yang sudah kubuat ini sudah sesuai dengan perintah untuk menyesuaikannya.



### Tugas 4
AI Disclosure:
Dalam tugas 3 ini, saya menggunakan bantuan AI (Gemini) untuk bertanya terkait menyelesaikan tugas ini.
    - Meminta AI untuk membantu memahami maksud dari permintaan soal nya ("Bantu aku untuk memahami permintaan tugas 4 ini, dan arahkan alur pengerjaanya").


### Tugas 5
1. Apa itu debouncing dan mengapa penting untuk pencarian AJAX? 
    - Debouncing adalah teknik menunda pemanggilan fungsi sampai pengguna berhenti melakukan suatu aktivitas selama waktu tertentu. Pada pencarian Education, permintaan `fetch()` baru dikirim setelah pengguna berhenti mengetik selama 300 milidetik. Setiap kali ada ketikan baru, timer sebelumnya dibatalkan dan dimulai lagi. Contohnya, ketika mengetik "Indonesia" dengan cepat, aplikasi tidak harus mengirim satu permintaan untuk setiap huruf. Ini mengurangi permintaan ke server dan pekerjaan pencarian di database. Selain debounce, `AbortController` membatalkan fetch sebelumnya dan nomor permintaan memastikan respons lama tidak menimpa hasil pencarian terbaru.
2. Apa fungsi `await` ketika menggunakan `fetch()`? Apa yang terjadi tanpa `await`?
    - `fetch()` mengembalikan sebuah Promise, yaitu objek yang mewakili hasil operasi yang belum tentu selesai. `await fetch(url)` menunda kelanjutan fungsi `async` tersebut sampai Promise berhasil atau gagal, tanpa menghentikan interaksi seluruh halaman. Setelah berhasil, hasilnya adalah objek `Response`. Kita masih perlu `await response.json()` karena pembacaan dan pengubahan isi respons menjadi data JavaScript juga bersifat asinkron. Jika menulis `const response = fetch(url)` tanpa `await`, variabel `response` berisi Promise, sehingga tidak bisa langsung diperlakukan sebagai objek Response, misalnya dengan memanggil `response.json()`. Tanpa `await`, operasi tetap dapat berjalan jika hasilnya ditangani dengan `.then()` dan `.catch()`. Status HTTP seperti 400 dan 403 juga harus diperiksa lewat `response.ok` atau `response.status`, karena `fetch()` tidak otomatis menolak Promise hanya karena status HTTP error.
3. Apa itu XSS dan mengapa penampilan data melalui JavaScript perlu perhatian khusus?
    - XSS (Cross-Site Scripting) terjadi ketika input yang tidak tepercaya diproses sebagai kode aktif oleh browser. Misalnya, `<img src="x" onerror="alert('XSS!')">` dapat menjalankan JavaScript jika dimasukkan langsung ke `innerHTML`. Template Django secara default melakukan autoescaping pada variabel HTML. Perlindungan itu tidak otomatis diterapkan ketika JavaScript merakit HTML dari respons JSON. Jadi, AJAX sendiri bukan penyebab XSS; risikonya muncul dari cara data dimasukkan ke halaman. Pada halaman Education, nilai teks dalam HTML kartu melewati `escapeHtml()`, sedangkan label tombol, pesan error, dan toast memakai `textContent`. Di server, `EducationForm` membersihkan input memakai `strip_tags()` pada method `clean_<field>`. Field wajib yang menjadi kosong setelah pembersihan ditolak. Pembersihan server adalah lapisan tambahan, bukan pengganti escaping saat menampilkan data, termasuk data lama di database.

AI Disclosure:
Dalam tugas 5 ini, saya menggunakan bantuan AI (Gemini) untuk bertanya terkait penyelesaian tugas ini.
    - memberikan konteks dari permintaan soal, lalu meminta untuk memberikan materi tentang tutorial 5 dan tugas 5, kemudian meminta untuk memberitahu cara mengimplementasikannya.
    - meminta untuk memperbaiki code yang error saat sedang debugging. ("tolong fix bagian yang salah dan sesuaikan dengan code lainnya")