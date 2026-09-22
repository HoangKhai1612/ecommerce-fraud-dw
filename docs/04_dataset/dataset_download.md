# DATASET DOWNLOAD

**Nguồn:** IEEE-CIS Fraud Detection  
**Ngày tạo:** 02/09/2026  
**Status:** ✅ ĐÃ TẢI — Files có trong `data/raw/`

---

## 1. CÁCH TẢI DATASET (NẾU CẦN)

### Bước 1: Đăng ký Kaggle
1. Truy cập https://www.kaggle.com
2. Đăng ký tài khoản (hoặc đăng nhập nếu đã có)
3. Vào trang competition: https://www.kaggle.com/competitions/ieee-fraud-detection/data

### Bước 2: Tải file
1. Click nút "Download" ở góc trên bên phải
2. File ZIP sẽ được tải về máy (~768 MB)
3. Giải nén file ZIP

### Bước 3: Đặt file vào đúng thư mục
```bash
# Di chuyển file vào data/raw/
data/raw/
├── train_transaction.csv
├── train_identity.csv
├── test_transaction.csv
├── test_identity.csv
└── sample_submission.csv
```

---

## 2. CÁCH TẢI QUA KAGGLE CLI (TỰ ĐỘNG)

```bash
# 1. Cài kaggle CLI
pip install kaggle

# 2. Cấu hình API token
# Tải kaggle.json từ https://www.kaggle.com/~/account
# Đặt vào: ~/.kaggle/kaggle.json (Linux/Mac) hoặc %USERPROFILE%\.kaggle\kaggle.json (Windows)
chmod 600 ~/.kaggle/kaggle.json

# 3. Tải dataset
kaggle competitions download -c ieee-fraud-detection
unzip ieee-fraud-detection.zip -d data/raw/
```

---

## 3. CHECKSUM VERIFICATION

```bash
# Kiểm tra kích thước file (ước tính)
# train_transaction.csv: ~653 MB
# train_identity.csv:    ~26 MB
# test_transaction.csv:  ~585 MB
# test_identity.csv:     ~25 MB
# sample_submission.csv: ~6 MB

# Kiểm tra file tồn tại và đọc được
python -c "
import pandas as pd
df = pd.read_csv('data/raw/train_transaction.csv', nrows=5)
print('Shape:', df.shape)
print('Columns:', list(df.columns[:5]))
"
```

---

## 4. VERSION CONTROL CHO DATASET

- **Dataset version**: IEEE-CIS v1.0 (Kaggle 2019)
- **Local path**: `data/raw/`
- **Git tracking**: Dữ liệu CSV được .gitignore (không commit vào Git)
- **Documentation**: `docs/04_dataset/`
- **Backup**: Lưu trữ dataset trên ổ đĩa cục bộ (đã có sẵn)

---

## 5. DATASET IN PROJECT

| File | Size | Rows | Columns | Status |
|------|------|------|---------|--------|
| `data/raw/train_transaction.csv` | 653 MB | 590,540 | 394 | ✅ Đã có |
| `data/raw/train_identity.csv` | 26 MB | 144,233 | 41 | ✅ Đã có |
| `data/raw/test_transaction.csv` | 585 MB | ~506,691 | 393 | ✅ Đã có |
| `data/raw/test_identity.csv` | 25 MB | ~146,133 | 41 | ✅ Đã có |
| `data/raw/sample_submission.csv` | 6 MB | 506,691 | 2 | ✅ Đã có |

> **Lưu ý quan trọng:** Dự án chỉ sử dụng `train_*` files cho toàn bộ pipeline vì `test_*` không có nhãn `isFraud`.

---

## 6. TÀI LIỆU THAM KHẢO

- Kaggle CLI documentation: https://github.com/Kaggle/kaggle-api
- IEEE-CIS Fraud Detection: https://www.kaggle.com/competitions/ieee-fraud-detection/data

*Cập nhật: 02/09/2026 | Version: 1.0*
