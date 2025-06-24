class PresciaConfig:
    astock_history_script = "astock/store_history.py"
    astock_config = "astock/config.yaml"

    database = [
        {"astock": "astock/history"}
    ]

    models = [
        {
            "bottoming": {
                "model_path": "models/bottoming_model/model.py",
                "model_config": "models/bottoming_model/config.yaml"
            }
        }
    ]


class PresciaInput:
    def __init__(self, database: str, model: str):
        self.database = database  # e.g. "astock"
        self.model = model        # e.g. "bottoming"

    def get_database_path(self):
        db = next((item[self.database] for item in PresciaConfig.database if self.database in item), None)
        if db is None:
            raise ValueError(f"Database '{self.database}' not found in config.")
        return db

    def get_model_config(self):
        model_dict = next((item[self.model] for item in PresciaConfig.models if self.model in item), None)
        if model_dict is None:
            raise ValueError(f"Model '{self.model}' not found in config.")
        return model_dict

prescia_input = PresciaInput(
    "astock",
    "bottoming"
)