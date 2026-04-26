from transformers import pipeline

class FoodVisionModel:

    def __init__(self):

        # Load food classification model
        self.classifier = pipeline(
            "image-classification",
            model="nateraw/food"
        )

    def predict_dish(self, image_path):

        try:
            results = self.classifier(image_path)

            # Top 3 predictions
            predictions = []

            for r in results[:3]:
                label = r["label"]
                label = label.replace("_", " ")
                predictions.append(label)

            # Return best prediction
            return predictions[0]

        except Exception as e:
            print("Vision Model Error:", e)
            return "food"