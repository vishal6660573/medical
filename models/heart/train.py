import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Load dataset (use exact filename)
data = pd.read_csv("data/heart.csv")

# -----------------------------
# Drop non-useful columns
# -----------------------------
data = data.drop(columns=["id", "dataset"])

# -----------------------------
# Convert target to binary
# num: 0 = no disease, 1-4 = disease
# -----------------------------
data["num"] = data["num"].apply(lambda x: 1 if x > 0 else 0)

# -----------------------------
# Encode categorical columns
# -----------------------------
categorical_cols = data.select_dtypes(include=["object", "bool"]).columns

data[categorical_cols] = data[categorical_cols].apply(
    lambda col: col.astype("category").cat.codes
)

# -----------------------------
# Separate features and target
# -----------------------------
X = data.drop("num", axis=1)
y = data["num"]

# -----------------------------
# Handle missing values (NOW SAFE)
# -----------------------------
X = X.fillna(X.median())

# -----------------------------
# Train-test split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# Random Forest model
# -----------------------------
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# -----------------------------
# Evaluation
# -----------------------------
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# -----------------------------
# Save model
# -----------------------------
joblib.dump(model, "model.pkl")
print("Heart disease model saved successfully")
