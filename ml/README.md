# SmartHealth — Production Machine Learning & Deep Learning Pipelines

This directory contains the production-quality, reproducible Machine Learning (ML) and Deep Learning (DL) pipelines powering the **SmartHealth Intelligent Healthcare Platform**.

The pipelines are architected with zero data leakage, automated data validation suites, stratified cross-validation, exhaustive hyperparameter tuning, model interpretability, error analysis, and synchronized serialization with the FastAPI backend.

---

## 📁 ML Directory Architecture

```text
ml/
├── notebooks/
│   ├── 01_diabetes_pipeline.ipynb          # End-to-end Tabular Pipeline for Diabetes Risk (Pima Indians)
│   ├── 02_heart_disease_pipeline.ipynb     # End-to-end Tabular Pipeline for Coronary Heart Disease (UCI)
│   └── 03_chest_xray_pipeline.ipynb        # Deep Learning Transfer Learning Pipeline (DenseNet121 CXR)
│
├── artifacts/                              # Serialized Production Artifacts & Metadata
│   ├── diabetes/
│   │   ├── best_model.joblib               # Full Preprocessing + Logistic Regression Pipeline
│   │   ├── model.pkl                       # Trained Logistic Regression Estimator
│   │   ├── scaler.pkl                      # Fitted StandardScaler Transformer
│   │   ├── metrics.json                    # Final Hold-Out Test Set Metrics
│   │   ├── feature_metadata.json           # Biomarker Schema & Imputation Rules
│   │   ├── training_metadata.json          # Training Environment & Hyperparameters
│   │   ├── confusion_matrix.png            # Diagnostic Confusion Matrix Plot
│   │   ├── roc_curve.png                   # Receiver Operating Characteristic (ROC) Curve
│   │   └── feature_importance.png         # Feature Odds-Ratios / Log-Odds Plot
│   │
│   ├── heart_disease/
│   │   ├── best_model.joblib               # Full Preprocessing + Random Forest Pipeline
│   │   ├── model.pkl                       # Trained Random Forest Estimator
│   │   ├── metrics.json                    # Final Hold-Out Test Set Metrics
│   │   ├── feature_metadata.json           # Clinical Feature Definitions & Cardinality
│   │   ├── training_metadata.json          # Selected Hyperparameters & CV Metrics
│   │   ├── confusion_matrix.png            # Confusion Matrix Plot
│   │   ├── roc_curve.png                   # ROC Curve Plot
│   │   └── feature_importance.png         # Gini Feature Importance Plot
│   │
│   └── chest_xray/
│       ├── model.h5                        # DenseNet121 Keras Model Weights & Architecture
│       ├── labels.json                     # Class Index Mapping (COVID, NORMAL, PNEUMONIA)
│       ├── metrics.json                    # Multi-Class Evaluation Metrics
│       ├── training_metadata.json          # Architecture Configuration & History
│       ├── confusion_matrix.png            # 3x3 Radiography Confusion Matrix
│       ├── roc_curve.png                   # One-vs-Rest ROC Curves
│       └── training_history.png            # Epoch Accuracy & Loss Convergence Curves
│
├── data/                                   # Datasets with Versioned Partitions
│   ├── raw/
│   │   ├── diabetes.csv                    # Raw Pima Indians Diabetes Dataset
│   │   ├── heart.csv                       # Raw UCI Heart Disease Dataset
│   │   └── xray_data/                      # Partitioned Chest Radiography Images
│   │       ├── train/ (COVID, NORMAL, PNEUMONIA)
│   │       ├── val/   (COVID, NORMAL, PNEUMONIA)
│   │       └── test/  (COVID, NORMAL, PNEUMONIA)
│   ├── processed/
│   └── validated/
│
└── README.md                               # ML Engineering Documentation
```

---

## 🔬 Pipeline 1: Diabetes Risk Prediction

### 1. Dataset & Clinical Context
- **Dataset:** Pima Indians Diabetes Database (National Institute of Diabetes and Digestive and Kidney Diseases).
- **Dimensions:** 768 patient records, 8 clinical biomarkers.
- **Target:** `Outcome` (0 = Non-Diabetic, 1 = Diabetic; Positive class ratio: 34.9%).

### 2. Clinical Biomarkers
| Feature | Clinical Description | Range |
|---|---|---|
| `Pregnancies` | Number of times pregnant | 0 – 17 |
| `Glucose` | Plasma glucose concentration (2 hours in OGTT) | 44 – 199 mg/dL |
| `BloodPressure` | Diastolic blood pressure | 24 – 122 mm Hg |
| `SkinThickness` | Triceps skin fold thickness | 7 – 99 mm |
| `Insulin` | 2-Hour serum insulin | 14 – 846 mu U/ml |
| `BMI` | Body Mass Index (weight in kg / (height in m)^2) | 18.2 – 67.1 kg/m² |
| `DiabetesPedigreeFunction` | Diabetes hereditary pedigree function | 0.078 – 2.42 |
| `Age` | Patient age in years | 21 – 81 |

### 3. Data Cleaning & Zero Leakage Preprocessing
- **Physiological Zero Replacement:** Converted biologically impossible zero measurements (`Glucose`, `BloodPressure`, `SkinThickness`, `Insulin`, `BMI`) to `NaN`. Genuine zero counts in `Pregnancies` are preserved.
- **Data Leakage Safeguard:** Transformations are fitted **strictly inside the training fold** during Cross-Validation using `scikit-learn.pipeline.Pipeline`.
- **Imputation & Standardization:** `SimpleImputer(strategy='median')` followed by `StandardScaler()`.

### 4. Cross-Validation & Model Selection
- **Validation Scheme:** 5-Fold Stratified K-Fold Cross Validation (`random_state=42`).
- **Primary Optimization Metric:** **ROC-AUC & Recall/Sensitivity** (minimizing False Negatives where diabetic patients might miss early clinical intervention).
- **Hyperparameter Tuning:** Systematic `GridSearchCV` on regularized `LogisticRegression` (`C=0.5, penalty='l2', solver='lbfgs'`).

### 5. Final Hold-Out Test Performance (Untouched 20% Split)
| Metric | Value |
|---|---|
| **Accuracy** | **70.78%** |
| **Precision** | **59.18%** |
| **Recall / Sensitivity** | **53.70%** |
| **Specificity** | **80.00%** |
| **F1-Score** | **0.5631** |
| **ROC-AUC** | **0.8081** |

---

## 🫀 Pipeline 2: Coronary Heart Disease Prediction

### 1. Dataset & Clinical Context
- **Dataset:** UCI Heart Disease Database (Cleveland / Comprehensive benchmark).
- **Dimensions:** 303 patient records, 13 clinical biomarkers.
- **Target:** `num` (Binarized: 0 = No Angiographic Disease, 1 = Coronary Heart Disease; Positive class ratio: 45.9%).

### 2. Clinical Biomarkers
| Feature | Description | Encoding / Unit |
|---|---|---|
| `age` | Age of the patient | Years (29 – 77) |
| `sex` | Biological sex | 0 = Female, 1 = Male |
| `cp` | Chest pain type | 0 = Typical, 1 = Atypical, 2 = Non-anginal, 3 = Asymptomatic |
| `trestbps` | Resting blood pressure on admission | mm Hg (94 – 200) |
| `chol` | Serum cholesterol | mg/dL (126 – 564) |
| `fbs` | Fasting blood sugar > 120 mg/dL | 0 = False, 1 = True |
| `restecg` | Resting electrocardiographic results | 0 = Normal, 1 = ST-T wave abnormality, 2 = Left ventricular hypertrophy |
| `thalach` | Maximum heart rate achieved during stress | bpm (71 – 202) |
| `exang` | Exercise-induced angina | 0 = No, 1 = Yes |
| `oldpeak` | ST depression induced by exercise relative to rest | mm (0.0 – 6.2) |
| `slope` | Slope of peak exercise ST segment | 0 = Upsloping, 1 = Flat, 2 = Downsloping |
| `ca` | Number of major vessels colored by fluoroscopy | 0 – 3 |
| `thal` | Thallium stress scintigraphy | 1 = Fixed defect, 2 = Normal, 3 = Reversible defect |

### 3. Cross-Validation & Hyperparameter Tuning
- **Preprocessors:** Median imputation encapsulated within scikit-learn Pipeline.
- **Baseline Models Tested:** Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, Extra Trees, Support Vector Machine.
- **Hyperparameter Grid Search:** Optimized `RandomForestClassifier` (`n_estimators=100, max_depth=6, min_samples_leaf=2, min_samples_split=5, max_features='sqrt'`).

### 4. Final Hold-Out Test Performance (Untouched 20% Split)
| Metric | Value |
|---|---|
| **Accuracy** | **90.16%** |
| **Precision** | **86.67%** |
| **Recall / Sensitivity** | **92.86%** |
| **Specificity** | **87.88%** |
| **F1-Score** | **0.8966** |
| **ROC-AUC** | **0.9610** |

---

## 🩻 Pipeline 3: Chest X-Ray Deep Learning (DenseNet121)

### 1. Dataset & Clinical Context
- **Dataset:** Chest Radiography Dataset with balanced train, validation, and test partitions.
- **Classes:** 
  - `COVID` (Bilateral ground-glass opacities)
  - `NORMAL` (Clear lung fields, sharp costophrenic recesses)
  - `PNEUMONIA` (Focal/lobar consolidations and infiltrates)

### 2. Deep Learning Architecture
- **Backbone:** DenseNet121 pre-trained on ImageNet (frozen convolutional base).
- **Custom Classification Head:**
  - `GlobalAveragePooling2D()`
  - `Dense(128, activation='relu')`
  - `Dropout(0.2)`
  - `Dense(3, activation='softmax')`
- **Training Strategy:**
  - Optimizer: Adam (learning rate = 1e-4)
  - Loss: Categorical Cross-Entropy
  - Callbacks: `EarlyStopping(patience=3)`, `ReduceLROnPlateau(factor=0.5, patience=2)`, `ModelCheckpoint`
- **Data Augmentation:** Applied **strictly to training images** (rotation ±10°, zoom ±10%, horizontal flip). Validation and test sets are strictly unaugmented.

### 3. Final Hold-Out Test Performance
| Metric | Score |
|---|---|
| **Overall Accuracy** | **100.00%** |
| **Macro Precision** | **100.00%** |
| **Macro Recall** | **100.00%** |
| **Macro F1-Score** | **1.0000** |
| **One-vs-Rest ROC-AUC** | **1.0000** |

---

## 🔄 FastAPI Backend Integration Guide

The ML pipelines are fully synchronized with the FastAPI backend prediction services without requiring any modifications to the application codebase:

### 1. Diabetes Prediction Service (`services/diabetes_prediction_service.py`)
```python
import joblib
import numpy as np

model = joblib.load("models/diabetes/model.pkl")
scaler = joblib.load("models/diabetes/scaler.pkl")

# Arrange features: [pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, dpf, age]
features = np.array([[data.pregnancies, data.glucose, data.blood_pressure, data.skin_thickness, 
                      data.insulin, data.bmi, data.diabetes_pedigree_function, data.age]])
scaled = scaler.transform(features)
probability = model.predict_proba(scaled)[0][1]
```

### 2. Heart Disease Prediction Service (`services/heart_prediction_service.py`)
```python
import joblib
import numpy as np

model = joblib.load("models/heart/model.pkl")

# Arrange features: [age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal]
features = np.array([[data.age, data.sex, data.cp, data.trestbps, data.chol, data.fbs, 
                      data.restecg, data.thalach, data.exang, data.oldpeak, data.slope, data.ca, data.thal]])
probability = model.predict_proba(features)[0][1]
```

### 3. Chest X-Ray Prediction Service (`models/xray/prediction_service.py`)
```python
import tensorflow as tf
import numpy as np
from PIL import Image

model = tf.keras.models.load_model("models/xray/model.h5")

def preprocess_image(image: Image.Image) -> np.ndarray:
    image = image.resize((224, 224)).convert("RGB")
    arr = np.array(image, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)

img = preprocess_image(image)
preds = model.predict(img)[0]
class_id = int(np.argmax(preds))
```

---

## 🛠️ Reproduction Instructions

To execute all three notebooks end-to-end and regenerate all artifacts:

```bash
# 1. Activate the Python environment
conda activate dl

# 2. Execute the notebooks via nbclient/jupyter
jupyter nbconvert --to notebook --execute ml/notebooks/01_diabetes_pipeline.ipynb --inplace
jupyter nbconvert --to notebook --execute ml/notebooks/02_heart_disease_pipeline.ipynb --inplace
jupyter nbconvert --to notebook --execute ml/notebooks/03_chest_xray_pipeline.ipynb --inplace
```

---

## ⚖️ Clinical & Medical Prototype Disclaimer

> [!CAUTION]
> **Regulatory Disclaimer:** The machine learning and deep learning models in this repository are developed strictly for research, educational, and clinical decision-support prototyping. They are not cleared or certified by the FDA, EMA, or any healthcare regulatory authority for autonomous clinical diagnosis or treatment planning. All model outputs must be validated by qualified healthcare professionals alongside standard diagnostic workups.