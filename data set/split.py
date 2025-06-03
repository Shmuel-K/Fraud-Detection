import os
import pandas as pd
import numpy as np
import zipfile

# הגדרת הנתיב לקובץ המקורי (שנה את הנתיב בהתאם)
csv_path = "dataSet.csv"  # ודא שהקובץ נמצא באותה תיקייה או עדכן את הנתיב המלא

# קריאת הקובץ
df = pd.read_csv(csv_path)

# מספר החלקים הרצוי
num_parts = 20

# חלוקת הנתונים ל-20 חלקים
split_dfs = np.array_split(df, num_parts)

# יצירת תיקייה לשמירת הקבצים המחולקים
split_folder = "split_files"
os.makedirs(split_folder, exist_ok=True)

# שמירת החלקים
split_files = []
for i, split_df in enumerate(split_dfs):
    split_file_path = os.path.join(split_folder, f"dataSet_part_{i+1}.csv")
    split_df.to_csv(split_file_path, index=False)
    split_files.append(split_file_path)

# יצירת ZIP עם כל החלקים
zip_path = "split_dataSet.zip"
with zipfile.ZipFile(zip_path, 'w') as zipf:
    for file in split_files:
        zipf.write(file, os.path.basename(file))

print(f"✅ תהליך החלוקה הסתיים! הקבצים שמורים ב-{zip_path}")
