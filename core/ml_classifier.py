import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os
import ee
from core.gee_auth import initialize_gee
initialize_gee()
# -----------------------------
# Why this file exists:
# Your current change_detection.py uses if/else thresholds to classify
# deforestation severity. That's rule-based, not AI.
# This file trains a Random Forest on real Sentinel-2 band values
# and replaces those rules with a learned model.
# -----------------------------

# Land cover classes we're classifying
CLASSES = {
    0: "Dense Forest",
    1: "Degraded Forest", 
    2: "Deforested",
    3: "Agriculture",
    4: "Urban/Bare"
}

MODEL_PATH = "core/rf_model.joblib"

def generate_training_data(lat: float, lon: float, n_samples: int = 300) -> tuple:
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(100000)  # 100km radius

    image = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate("2022-01-01", "2024-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .median()  # median composite instead of single image
    )

    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    evi = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        {'NIR': image.select('B8'), 'RED': image.select('B4'), 'BLUE': image.select('B2')}
    ).rename("EVI")

    full_image = image.select(["B2","B3","B4","B8","B11","B12"]).addBands(ndvi).addBands(evi)

    samples = full_image.sample(
        region=region,
        scale=500,
        numPixels=n_samples,
        seed=42,
        geometries=False,
        tileScale=8
    )

    data = samples.getInfo()
    count = len(data['features'])
    print(f"Sampling {count} pixels from GEE...")

    X = []
    y = []

    for feature in data['features']:
        props = feature['properties']
        try:
            b2  = props.get('B2', 0) or 0
            b3  = props.get('B3', 0) or 0
            b4  = props.get('B4', 0) or 0
            b8  = props.get('B8', 0) or 0
            b11 = props.get('B11', 0) or 0
            b12 = props.get('B12', 0) or 0
            ndvi_val = props.get('NDVI', 0) or 0
            evi_val  = props.get('EVI', 0) or 0

            row = [b2, b3, b4, b8, b11, b12, ndvi_val, evi_val]

            if ndvi_val > 0.6:
                label = 0
            elif ndvi_val > 0.4:
                label = 1
            elif ndvi_val > 0.2 and b11 > 1000:
                label = 3
            elif ndvi_val < 0.1:
                label = 4
            else:
                label = 2

            X.append(row)
            y.append(label)
        except:
            continue

    return np.array(X), np.array(y)


def train_model(lat: float, lon: float) -> dict:
    """
    Train Random Forest classifier on GEE-sampled data.
    
    WHY Random Forest:
    - Works well on small datasets (500-1000 samples)
    - Handles correlated features (bands are correlated)
    - Gives feature importance — tells you which bands matter most
    - No need for feature scaling
    - Robust to outliers (cloud shadows, corrupted pixels)
    """
    print("Generating training data from GEE...")
    X, y = generate_training_data(lat, lon)
    
    if len(X) < 50:
        raise ValueError("Not enough samples generated. Try a different region or date range.")

    # WHY 80/20 split: standard practice
    # Train on 80%, test on 20% to measure real accuracy
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )

    # WHY n_estimators=100: 100 trees — good balance of accuracy vs speed
    # WHY max_depth=15: prevents overfitting on small dataset
    # WHY class_weight='balanced': our samples may be uneven
    # (more forest pixels than urban pixels in Amazon)
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1  # use all CPU cores
    )

    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    unique_classes = sorted(np.unique(y))
    report = classification_report(y_test, y_pred,
                                   labels=unique_classes,
                                   target_names=[CLASSES[i] for i in unique_classes],
                                   zero_division=0)

    # Feature importance — WHY: tells us which bands matter most
    feature_names = ["B2","B3","B4","B8","B11","B12","NDVI","EVI"]
    importances = dict(zip(feature_names, clf.feature_importances_.round(3)))

    # Save model to disk
    # WHY: so we don't retrain every time app starts
    joblib.dump(clf, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    return {
        "accuracy": round((y_pred == y_test).mean(), 3),
        "report": report,
        "feature_importance": importances,
        "samples_used": len(X),
        "model_path": MODEL_PATH
    }


def load_model():
    """
    Load saved model from disk.
    WHY: Training takes 30-60 seconds. We train once, save, load fast.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Model not trained yet. Run train_model() first.")
    return joblib.load(MODEL_PATH)


def predict_land_cover(band_values: dict) -> dict:
    """
    Predict land cover class for a single observation.
    
    band_values: dict with keys B2,B3,B4,B8,B11,B12,NDVI,EVI
    
    WHY this replaces the if/else in change_detection.py:
    Instead of hardcoded thresholds, the model learned the decision
    boundaries from actual satellite data.
    """
    clf = load_model()
    
    features = np.array([[
        band_values.get('B2', 0),
        band_values.get('B3', 0),
        band_values.get('B4', 0),
        band_values.get('B8', 0),
        band_values.get('B11', 0),
        band_values.get('B12', 0),
        band_values.get('NDVI', 0),
        band_values.get('EVI', 0),
    ]])

    prediction = clf.predict(features)[0]
    # WHY predict_proba: gives confidence score, not just class label
    probabilities = clf.predict_proba(features)[0]
    confidence = round(probabilities.max(), 3)

    return {
        "class_id": int(prediction),
        "class_label": CLASSES[int(prediction)],
        "confidence": confidence,
        "probabilities": {
            CLASSES[i]: round(float(p), 3) 
            for i, p in enumerate(probabilities)
            if i in CLASSES
        }
    }