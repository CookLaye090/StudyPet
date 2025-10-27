# StudyPet Machine Learning Models

This directory contains trained machine learning models for StudyPet features.

## 📁 Directory Structure

```
models/
├── your_model_name/          # Model directory (if SavedModel format)
│   ├── saved_model.pb        # Model definition
│   ├── variables/            # Model weights
│   └── assets/               # Additional assets
├── your_model.h5             # Keras model file (if .h5 format)
└── model_integration_example.py  # Example code for using models
```

## 🚀 Getting Started with Your Model

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Load Your Model
```python
from src.models.model_integration_example import ModelPredictor

# Replace 'your_model_name' with your actual model directory/file name
predictor = ModelPredictor("models/your_model_name")
```

### 3. Make Predictions
```python
# For image classification
result = predictor.predict("path/to/your/image.jpg")
print(f"Predicted: {result['class_name']} (Confidence: {result['confidence']:.2%})")
```

## 📖 Teachable Machine Model Formats

### Option 1: Keras Format (.h5 file)
- **Single file**: `model.h5`
- **Easy to use**: Simple load with `tf.keras.models.load_model()`
- **File location**: `models/model.h5`

### Option 2: SavedModel Format (Directory)
- **Multiple files**: Directory with `.pb` files and `variables/` folder
- **More flexible**: Can handle complex models
- **File location**: `models/model_directory/`

### Option 3: TensorFlow Lite (.tflite)
- **For mobile/embedded**: Optimized for edge devices
- **Single file**: `model.tflite`
- **File location**: `models/model.tflite`

## 🔧 Integration Examples

### Pet Emotion Recognition
```python
from src.models.model_integration_example import PetEmotionPredictor

# Initialize predictor
emotion_predictor = PetEmotionPredictor()

# Predict from pet image
emotion, confidence = emotion_predictor.predict_pet_emotion("img/pet_screenshot.png")

# Use in pet system
if confidence > 0.7:  # High confidence threshold
    # Update pet emotion based on prediction
    pass
```

### Custom Model Integration
```python
# For any classification task
predictor = ModelPredictor("models/custom_model")

# Define your class names
predictor.class_names = ["class1", "class2", "class3"]

# Make prediction
result = predictor.predict("test_image.jpg")
```

## 🎯 Common Use Cases

### 1. Pet Emotion Detection
- Train model to recognize pet emotions from screenshots
- Integrate with pet care system
- Adjust pet behavior based on detected emotions

### 2. Study Activity Recognition
- Detect when user is studying vs distracted
- Track study time automatically
- Provide insights on study habits

### 3. Environment Analysis
- Recognize study environment quality
- Detect distractions
- Suggest improvements for better focus

## 🛠️ Model Development Workflow

1. **Train Model**: Use Teachable Machine (teachablemachine.withgoogle.com)
2. **Export Model**: Download as TensorFlow/Keras format
3. **Unzip Files**: Extract to `models/your_model_name/` directory
4. **Test Model**: Use the example code to verify it works
5. **Integrate**: Add prediction logic to StudyPet features
6. **Deploy**: Test in the full application

## 📋 Best Practices

- **Model Naming**: Use descriptive names (e.g., `pet_emotion_model`, `study_activity_detector`)
- **Version Control**: Consider model versioning for updates
- **Documentation**: Add README files for complex models
- **Testing**: Always test models before integration
- **Performance**: Monitor model size and inference speed

## 🔍 Troubleshooting

### Model Not Loading
- Check if model path is correct
- Verify TensorFlow version compatibility
- Ensure all model files are present

### Poor Predictions
- Check input image preprocessing (size, normalization)
- Verify class names match training data
- Consider confidence thresholds

### Performance Issues
- Consider using TensorFlow Lite for faster inference
- Optimize input image size
- Use GPU if available

## 📚 Resources

- [TensorFlow Documentation](https://www.tensorflow.org/)
- [Teachable Machine](https://teachablemachine.withgoogle.com/)
- [Keras Documentation](https://keras.io/)
- [Computer Vision with TensorFlow](https://www.tensorflow.org/tutorials/images/classification)

## 🤝 Contributing

When adding new models:
1. Create a new directory in `models/`
2. Add model files and documentation
3. Update this README
4. Test integration thoroughly
