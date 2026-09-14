"""Evaluasi PeDaS: cocokkan ID, validasi data, lalu hitung Macro-F1.

Jalankan: python evaluate.py
Dependensi: pip install scikit-learn
CSV contoh dalam paket ini sepenuhnya imitasi.
"""
import argparse
import csv
import json
import unicodedata
from collections import Counter
from pathlib import Path

from sklearn.metrics import f1_score


# Kosakata dari kategori sumber PANDI setelah normalisasi kapitalisasi.
# Salah ketik seperti "phising" tidak otomatis diubah menjadi "phishing".
VALID_CATEGORIES = {
    "online gambling", "phishing", "other", "spam", "malware",
    "brand", "fakeshop", "violence", "piiexposure",
}


def normalize_category(value):
    """Samakan Unicode, kapitalisasi, dan spasi; tidak menebak salah ketik."""
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(value.split())


def read_csv(path):
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, strict=True)
        header = next(reader, [])
        if len(header) != 2 or set(header) != {"id", "category"}:
            raise ValueError(f"{path}: header wajib tepat id dan category.")
        for number, values in enumerate(reader, start=1):
            if len(values) != 2:
                rows.append({"row": number, "id": "", "category": "",
                             "errors": ["jumlah kolom tidak sesuai"]})
                continue
            record = dict(zip(header, values))
            rows.append({"row": number, "id": record["id"].strip(),
                         "category": normalize_category(record["category"]),
                         "errors": []})
    return rows


def validate_rows(rows, expected_ids=None):
    counts = Counter(row["id"] for row in rows if row["id"])
    for row in rows:
        if row["errors"]:  # Struktur record sudah invalid.
            continue
        if not row["id"]:
            row["errors"].append("id kosong")
        elif counts[row["id"]] > 1:
            row["errors"].append("id duplikat")  # Semua kemunculan invalid.
        if not row["category"]:
            row["errors"].append("category kosong")
        elif row["category"] not in VALID_CATEGORIES:
            row["errors"].append("category tidak dikenal")
        if expected_ids is not None and row["id"] and row["id"] not in expected_ids:
            row["errors"].append("id tidak ada di ground truth")


def summarize(rows):
    invalid = sum(bool(row["errors"]) for row in rows)
    return {
        "read": len(rows), "valid": len(rows) - invalid, "invalid": invalid,
        "invalid_rows": [{"data_row": row["row"], "reasons": row["errors"]}
                         for row in rows if row["errors"]],
    }


def evaluate(prediction_path, truth_path):
    truth = read_csv(truth_path)
    prediction = read_csv(prediction_path)
    validate_rows(truth)
    expected_ids = {row["id"] for row in truth if row["id"]}
    validate_rows(prediction, expected_ids)
    valid_truth = {row["id"]: row["category"] for row in truth if not row["errors"]}
    valid_prediction = {row["id"]: row["category"] for row in prediction if not row["errors"]}
    submitted_ids = {row["id"] for row in prediction if row["id"]}
    matched = set(valid_truth) & set(valid_prediction)
    report = {
        "prediction": summarize(prediction), "ground_truth": summarize(truth),
        "missing_prediction_ids": len(expected_ids - submitted_ids),
        "valid_matched_pairs": len(matched),
        "status": "INVALID", "macro_f1": None, "scoring_classes": [],
    }
    # Jangan menilai hanya subset valid: menghilangkan baris sulit bisa menaikkan skor.
    if (not truth or not prediction or report["ground_truth"]["invalid"]
            or report["prediction"]["invalid"] or report["missing_prediction_ids"]):
        return report

    ids = list(valid_truth)
    y_true = [valid_truth[key] for key in ids]
    y_pred = [valid_prediction[key] for key in ids]
    # Daftar ini tetap untuk satu ground truth dan tidak ditentukan isi submission.
    # Kelas tanpa contoh di ground truth tidak masuk rata-rata.
    scoring_classes = sorted(set(y_true))
    score = f1_score(y_true, y_pred, labels=scoring_classes,
                     average="macro", zero_division=0)
    report.update(status="VALID", macro_f1=float(score), scoring_classes=scoring_classes)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediction", default="data/submission-template.csv")
    parser.add_argument("--ground-truth", default="data/ground_truth.csv")
    parser.add_argument("--report", help="Opsional: simpan laporan JSON ke lokasi ini.")
    args = parser.parse_args()
    try:
        report = evaluate(args.prediction, args.ground_truth)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"GAGAL MEMBACA: {error}")
        print("Macro-F1 tidak dihitung. Jumlah baris lengkap tidak dapat dipastikan.")
        return 2

    for key, title in [("prediction", "Prediksi"), ("ground_truth", "Ground truth")]:
        item = report[key]
        print(f"{title}: terbaca={item['read']}, valid={item['valid']}, invalid={item['invalid']}")
        for row in item["invalid_rows"][:10]:
            print(f"  Baris data {row['data_row']}: {', '.join(row['reasons'])}")
        if item["invalid"] > 10:
            print("  Rincian lainnya tersedia melalui opsi --report.")
    print(f"ID ground truth tanpa baris prediksi: {report['missing_prediction_ids']}")
    print(f"Pasangan valid berdasarkan ID: {report['valid_matched_pairs']}")
    print(f"Status evaluasi: {report['status']}")
    if report["status"] == "VALID":
        print("Kelas yang dirata-ratakan: " + ", ".join(report["scoring_classes"]))
        print(f"Macro-F1: {report['macro_f1']:.8f}")
    else:
        print("Macro-F1 tidak dihitung. Perbaiki data invalid, kosong, atau ID yang belum lengkap.")
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if report["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
