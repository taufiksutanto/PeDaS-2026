# PeDAS 2026

Jika perlu, pasang dependensi: `python -m pip install -r requirements.txt`. Python yang dipakai saat penyusunan: 3.12.14.

# Evaluator PeDaS 2026

Kedua CSV dalam folder `data` adalah contoh imitasi 20 baris, bukan data atau
ground truth lomba. Template contoh sudah diisi prediksi dan urutannya dibalik
untuk memperlihatkan bahwa pencocokan menggunakan `id`.

```bash
pip install scikit-learn
python evaluate.py
python evaluate.py --report hasil_evaluasi.json
```

Untuk berkas lain:

```bash
python evaluate.py --prediction hasil_tim.csv --ground-truth ground_truth_panitia.csv
```

Contoh ini belum menangani PIN, kuota submission, atau scoreboard.

## Normalisasi dan validasi

`category` pada kedua berkas diproses sama: normalisasi Unicode NFKC, huruf kecil,
penghapusan spasi tepi, dan penggabungan spasi berulang. `Online Gambling` dan
` online   gambling ` menjadi `online gambling`. `Brand` dan `brand` menjadi
`brand`. Salah ketik seperti `phising` tetap invalid; evaluator tidak menebak label.
Kosakata kelas valid ada pada `VALID_CATEGORIES` dalam script, berdasarkan sembilan
kategori sumber setelah normalisasi. Jangan mengubahnya berdasarkan submission.

ID dibaca sebagai teks, hanya dipangkas spasi tepinya, tetap peka huruf besar/kecil.
Header wajib tepat `id` dan `category`; urutan kedua kolom boleh tertukar.
Baris data dihitung sebagai record CSV setelah header, termasuk record kosong
atau jumlah kolom salah. Record dengan kutipan multiline dihitung satu record.
Jika header/encoding/sintaks CSV rusak, proses berhenti dengan pesan kegagalan baca.

Baris invalid mencakup ID kosong, seluruh kemunculan ID duplikat, category kosong
atau tidak dikenal, dan jumlah kolom salah. Prediksi dengan ID di luar ground truth
juga invalid. Satu baris dengan beberapa masalah tetap dihitung satu baris invalid.
Valid tidak berarti prediksinya benar: label yang dikenal tetapi salah tetap valid
dan menurunkan Macro-F1. ID ground truth tanpa prediksi dilaporkan terpisah karena
tidak ada baris prediksi yang bisa dihitung sebagai invalid. Ground truth dinilai
validitas internalnya sendiri; barisnya tidak menjadi invalid karena peserta lupa ID.

Evaluator tidak menghitung skor jika ada baris invalid di salah satu file, file
kosong, atau ID ground truth belum lengkap. Baris bermasalah tidak dibuang diam-diam.
Status keluar: 0 = valid dan dinilai; 1 = data invalid/tidak lengkap; 2 = gagal baca.
Opsi `--report` menyimpan ringkasan dan semua nomor record invalid dalam JSON untuk
file yang berhasil dibaca; kesalahan baca dilaporkan melalui terminal.

## Macro-F1

Untuk setiap kelas k:

F1_k = 2 TP_k / (2 TP_k + FP_k + FN_k)

Macro-F1 = jumlah F1_k / jumlah kelas yang dinilai.

TP adalah prediksi benar untuk kelas tersebut, FP adalah prediksi kelas tersebut
padahal label sebenarnya berbeda, dan FN adalah contoh kelas tersebut yang
diprediksi sebagai kelas lain. Setiap kelas mendapat bobot sama sehingga kelas
mayoritas tidak mendominasi rata-rata. Penyebut nol ditangani dengan `zero_division=0`.

Kebijakan script: kelas yang dirata-ratakan adalah kategori unik dalam ground truth
setelah normalisasi. Daftar ini tetap untuk semua tim pada ground truth yang sama.
Kategori tanpa contoh ground truth tidak ikut rata-rata. Jika peserta memprediksi
kelas valid yang tidak muncul di ground truth, prediksi tersebut tetap menambah FN
pada kelas sebenarnya. Tetapkan kebijakan ini sebelum penilaian resmi; cakupan
kelas test dan validasi final dapat berbeda, sehingga skornya tidak langsung setara.

Pada contoh: F1 online gambling = 0,9; phishing = 0,8; malware = 1; spam = 1.
Macro-F1 = (0,9 + 0,8 + 1 + 1) / 4 = 0,925.
Kedua file terbaca 20 baris, 20 valid, 0 invalid; terdapat 20 pasangan ID valid.

Angka terminal dibulatkan menjadi delapan desimal. JSON menyimpan nilai float tanpa
pembulatan tambahan; gunakan nilai tersebut saat membandingkan skor untuk peringkat.
