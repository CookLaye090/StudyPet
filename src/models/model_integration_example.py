"""
Example code for loading and using Teachable Machine models in StudyPet

This demonstrates how to integrate your trained model into the StudyPet application.
"""

import tensorflow as tf
import numpy as np
from PIL import Image
import os

class ModelPredictor:
    """Class to handle loading and using Teachable Machine models."""

    def __init__(self, model_path):
        """
        Initialize the model predictor.

        Args:
            model_path: Path to the model directory (for SavedModel) or .h5 file
        """
        self.model_path = model_path
        self.model = None
        self.class_names = []  # You can define these based on your training

        # Load the model based on format
        self._load_model()

    def _load_model(self):
        """Load the model based on its format."""
        try:
            # Check if it's a SavedModel directory or .h5 file
            if os.path.isdir(self.model_path):
                # SavedModel format (directory with .pb files)
                self.model = tf.saved_model.load(self.model_path)
                print(f"✅ Loaded SavedModel from: {self.model_path}")
            elif self.model_path.endswith('.h5'):
                # Keras format (single .h5 file)
                self.model = tf.keras.models.load_model(self.model_path)
                print(f"✅ Loaded Keras model from: {self.model_path}")
            else:
                raise ValueError("Unsupported model format")

        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None

    def predict(self, image_path):
        """
        Make a prediction on an image.

        Args:
            image_path: Path to the image file to classify

        Returns:
            dict: Prediction results with class names and confidence scores
        """
        if self.model is None:
            return {"error": "Model not loaded"}

        try:
            # Load and preprocess the image
            image = Image.open(image_path).convert('RGB')
            image = image.resize((224, 224))  # Standard input size for most models
            image_array = np.array(image) / 255.0  # Normalize to [0,1]
            image_array = np.expand_dims(image_array, axis=0)  # Add batch dimension

            # Make prediction
            if hasattr(self.model, 'signatures'):  # SavedModel format
                # Get the default signature
                signature = self.model.signatures['serving_default']
                predictions = signature(image_array)
                # Convert to numpy array
                predictions = predictions.numpy()
            else:  # Keras format
                predictions = self.model.predict(image_array)

            # Process results
            predicted_class = np.argmax(predictions, axis=1)[0]
            confidence = float(np.max(predictions))

            return {
                "predicted_class": predicted_class,
                "confidence": confidence,
                "class_name": self.class_names[predicted_class] if predicted_class < len(self.class_names) else f"Class_{predicted_class}",
                "all_predictions": predictions.tolist()
            }

        except Exception as e:
            return {"error": str(e)}

    def predict_from_array(self, image_array):
        """
        Make prediction from a numpy array.

        Args:
            image_array: Preprocessed image as numpy array

        Returns:
            dict: Prediction results
        """
        if self.model is None:
            return {"error": "Model not loaded"}

        try:
            # Ensure proper shape
            if len(image_array.shape) == 3:
                image_array = np.expand_dims(image_array, axis=0)

            # Make prediction
            if hasattr(self.model, 'signatures'):  # SavedModel format
                signature = self.model.signatures['serving_default']
                predictions = signature(image_array)
                predictions = predictions.numpy()
            else:  # Keras format
                predictions = self.model.predict(image_array)

            # Process results
            predicted_class = np.argmax(predictions, axis=1)[0]
            confidence = float(np.max(predictions))

            return {
                "predicted_class": predicted_class,
                "confidence": confidence,
                "class_name": self.class_names[predicted_class] if predicted_class < len(self.class_names) else f"Class_{predicted_class}",
                "all_predictions": predictions.tolist()
            }

        except Exception as e:
            return {"error": str(e)}

# Example usage in StudyPet:
def example_usage():
    """Example of how to use the model in StudyPet."""

    # Path to your model (adjust based on what you named it)
    model_path = "models/your_model_name"

    # Create predictor instance
    predictor = ModelPredictor(model_path)

    # Example: Classify an image
    result = predictor.predict("path/to/test/image.jpg")

    if "error" not in result:
        print(f"Prediction: {result['class_name']} (Confidence: {result['confidence']:.2%})")
    else:
        print(f"Error: {result['error']}")

    return predictor

# Integration example for StudyPet
class PetEmotionPredictor:
    """Example integration with StudyPet's pet system."""

    def __init__(self):
        self.model_path = "models/pet_emotion_model"  # Your model directory
        self.predictor = ModelPredictor(self.model_path)

        # Define class names based on your training
        self.class_names = ["happy", "sad", "curious", "sleepy", "hungry"]

        # Update predictor with class names
        self.predictor.class_names = self.class_names

    def predict_pet_emotion(self, pet_image_path):
        """Predict pet emotion from image."""
        result = self.predictor.predict(pet_image_path)

        if "error" not in result:
            emotion = result['class_name']
            confidence = result['confidence']

            print(f"🎭 Predicted emotion: {emotion} (Confidence: {confidence:.2%})")

            return emotion, confidence
        else:
            print(f"❌ Prediction error: {result['error']}")
            return None, 0.0

# Example of how to use in StudyPet screens
def integrate_with_pet_system():
    """Example integration with the pet system."""

    # This could be added to MainGameScreen or Pet class
    emotion_predictor = PetEmotionPredictor()

    # Example usage when pet interacts
    # emotion, confidence = emotion_predictor.predict_pet_emotion("img/pet_screenshot.png")

    # You could then update pet emotion based on prediction:
    # if confidence > 0.7:  # Only if confident enough
    #     current_pet.emotion = PetEmotion.from_string(emotion)

    return emotion_predictor
