from dataclasses import dataclass


@dataclass
class ClassificationResult:
    stage: str
    confidence: float


class FermentationClassifier:

    def classify(self, brown_percentage: float) -> ClassificationResult:

        if brown_percentage < 20:
            stage = "Fresh Leaf"

        elif brown_percentage < 40:
            stage = "Withering"

        elif brown_percentage < 60:
            stage = "Early Fermentation"

        elif brown_percentage < 80:
            stage = "Optimum"

        else:
            stage = "Over Fermented"

        return ClassificationResult(
            stage=stage,
            confidence=100.0,
        )