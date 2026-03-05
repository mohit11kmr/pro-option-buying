"""
Model Registry - ML Model Persistence and Versioning
====================================================
Manages saving, loading, and versioning of ML models.
"""

import os
import json
import pickle
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd


class ModelRegistry:
    """Model registry for saving, loading, and versioning ML models."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.registry_file = self.models_dir / "registry.json"
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Load model registry from file."""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {"models": [], "versions": {}}
    
    def _save_registry(self) -> None:
        """Save model registry to file."""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def _compute_hash(self, data: Any) -> str:
        """Compute hash of model data."""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        elif hasattr(data, 'predict'):
            data = str(type(data).__name__)
        return hashlib.md5(str(data).encode()).hexdigest()[:8]
    
    def register_model(
        self,
        name: str,
        model: Any,
        metadata: Dict,
        version: Optional[str] = None
    ) -> str:
        """Register a new model."""
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        model_hash = self._compute_hash(model)
        
        model_info = {
            "name": name,
            "version": version,
            "hash": model_hash,
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        model_filename = f"{name}_{version}.pkl"
        model_path = self.models_dir / model_filename
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        if name not in self.registry["versions"]:
            self.registry["versions"][name] = []
        
        self.registry["versions"][name].append(model_info)
        self.registry["models"].append(model_info)
        self._save_registry()
        
        return version
    
    def load_model(self, name: str, version: Optional[str] = None) -> Optional[Any]:
        """Load a model from registry."""
        versions = self.registry.get("versions", {}).get(name, [])
        
        if not versions:
            return None
        
        if version is None:
            version = versions[-1]["version"]
        
        for model_info in versions:
            if model_info["version"] == version:
                model_filename = f"{name}_{version}.pkl"
                model_path = self.models_dir / model_filename
                
                if model_path.exists():
                    with open(model_path, 'rb') as f:
                        return pickle.load(f)
        
        return None
    
    def list_models(self) -> List[Dict]:
        """List all registered models."""
        return self.registry.get("models", [])
    
    def list_versions(self, name: str) -> List[Dict]:
        """List all versions of a specific model."""
        return self.registry.get("versions", {}).get(name, [])
    
    def get_latest_version(self, name: str) -> Optional[str]:
        """Get the latest version of a model."""
        versions = self.registry.get("versions", {}).get(name, [])
        if versions:
            return versions[-1]["version"]
        return None
    
    def delete_model(self, name: str, version: str) -> bool:
        """Delete a specific model version."""
        versions = self.registry.get("versions", {}).get(name, [])
        
        for i, model_info in enumerate(versions):
            if model_info["version"] == version:
                model_filename = f"{name}_{version}.pkl"
                model_path = self.models_dir / model_filename
                
                if model_path.exists():
                    os.remove(model_path)
                
                del versions[i]
                self.registry["models"] = [
                    m for m in self.registry["models"]
                    if not (m["name"] == name and m["version"] == version)
                ]
                self._save_registry()
                return True
        
        return False
    
    def export_metadata(self, name: str, output_file: str) -> bool:
        """Export model metadata to JSON file."""
        versions = self.list_versions(name)
        
        if not versions:
            return False
        
        with open(output_file, 'w') as f:
            json.dump({
                "name": name,
                "versions": versions,
                "latest_version": versions[-1]["version"]
            }, f, indent=2)
        
        return True


class ModelTrainer:
    """Train and register ML models."""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
    
    def train_price_predictor(self, df: pd.DataFrame, params: Dict = None) -> Any:
        """Train a simple price prediction model."""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.preprocessing import StandardScaler
        
        params = params or {}
        
        df = df.dropna()
        
        df['target'] = df['close'].shift(-1)
        df = df.dropna()
        
        features = ['open', 'high', 'low', 'close', 'volume']
        X = df[features].values
        y = df['target'].values
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = RandomForestRegressor(
            n_estimators=params.get('n_estimators', 100),
            max_depth=params.get('max_depth', 10),
            random_state=42
        )
        
        model.fit(X_scaled, y)
        
        metadata = {
            "type": "price_predictor",
            "features": features,
            "params": params,
            "training_samples": len(X),
            "accuracy": model.score(X_scaled, y)
        }
        
        version = self.registry.register_model("price_predictor", model, metadata)
        
        return model, version
    
    def train_pattern_classifier(self, df: pd.DataFrame, params: Dict = None) -> Any:
        """Train a pattern classification model."""
        from sklearn.ensemble import RandomForestClassifier
        
        params = params or {}
        
        df = df.dropna()
        
        df['pattern'] = (
            (df['close'] > df['open']).astype(int) +
            (df['close'].shift(1) > df['open'].shift(1)).astype(int) +
            (df['close'].shift(2) > df['open'].shift(2)).astype(int)
        )
        df['pattern'] = df['pattern'].clip(0, 3)
        df = df.dropna()
        
        features = ['open', 'high', 'low', 'close', 'volume']
        X = df[features].values
        y = df['pattern'].values
        
        model = RandomForestClassifier(
            n_estimators=params.get('n_estimators', 50),
            max_depth=params.get('max_depth', 5),
            random_state=42
        )
        
        model.fit(X, y)
        
        metadata = {
            "type": "pattern_classifier",
            "features": features,
            "params": params,
            "training_samples": len(X),
            "accuracy": model.score(X, y)
        }
        
        version = self.registry.register_model("pattern_classifier", model, metadata)
        
        return model, version


def demo_model_registry():
    """Demonstrate model registry functionality."""
    print("\n" + "="*60)
    print("MODEL REGISTRY DEMO")
    print("="*60)
    
    registry = ModelRegistry("models")
    
    sample_model = {"type": "dummy", "accuracy": 0.85}
    metadata = {"accuracy": 0.85, "dataset": "nifty_20yr"}
    
    version = registry.register_model("test_model", sample_model, metadata)
    print(f"Registered model: test_model version {version}")
    
    models = registry.list_models()
    print(f"\nRegistered models: {len(models)}")
    for m in models:
        print(f"  - {m['name']} v{m['version']}")
    
    loaded = registry.load_model("test_model")
    print(f"\nLoaded model: {loaded}")
    
    versions = registry.list_versions("test_model")
    print(f"Model versions: {versions}")


if __name__ == "__main__":
    demo_model_registry()
