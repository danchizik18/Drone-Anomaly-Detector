import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Create dummy training data
# You can later replace this with real labeled data
X = pd.DataFrame({
    "velocity": [0, 50, 120, 300, 5, 90, 220, 40],
    "heading": [10, 180, 250, 80, 300, 170, 90, 5]
})

y = ["low", "medium", "high", "high", "low", "medium", "high", "low"]

# Train a RandomForest model
model = RandomForestClassifier(n_estimators=50, random_state=42)
model.fit(X, y)

# Save the model to a .pkl file
joblib.dump(model, "ml_model.pkl")
print("✅ Model trained and saved to ml_model.pkl")
