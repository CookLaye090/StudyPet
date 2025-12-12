# StudyPet

An AI-powered virtual pet study companion built with Python and Tkinter that helps you stay motivated while studying!

## Features

### Pet Evolution System
- **Auto-Evolution**: Pets automatically evolve when mastery reaches the limit
- **mastery Reset**: mastery resets to 0 upon evolution, starting a new journey
- **Progressive Limits**: 
  - Stages 1-4 (Egg → Baby → Child → Grown): 200 mastery limit
  - Stage 5 (Battle-fit): 1000 mastery limit (final stage)

### Study Tools
- **Smart Study Timer**: Pomodoro-style timer
- **Progress Tracking**: Monitor your study time
- **Study Scheduler**: Plan and organize your study sessions

### AI-Powered Chat
- **Built-in chatbot**: Chat with your pet using built-in generative AI
- **Original Responses**: Pet responds using unique sentences
- **Emotion Recognition**: Your pet responds based on your mood and context
- **Conversation Memory**: Persistent chat history and relationship building

### Focus Features
- **Background Music**: Play your favorite study music with built-in player
- **Multiple Formats**: Supports MP3, WAV, OGG, and M4A files

### Customization
- **Responsive UI**: Interface scales with window size for optimal viewing
- **Font Scaling**: Text automatically adjusts based on window dimensions

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Installation
1. Clone the repository:
```bash
git clone https://github.com/CookLaye/StudyPet.git
cd StudyPet
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python StudyPet.py
```

### AI Chat Features
Your pet uses a built-in local language generation system:
- No external API keys required
- Completely offline functionality
- Creates original responses based on pet personality and conversation context

## Recent Updates

### Latest Updates
- **Unified Egg Positioning**: All pet eggs now appear at the exact same ground level (height - 320)
- **Enhanced Icon Persistence**: Advanced restart detection prevents icon loss after data reset
- **Horizontal Preview Layout**: Pet selection now uses side-by-side layout (text left, egg right) to prevent cropping
- **Responsive Design**: Preview area adapts to window size with optimal egg container sizing

### Background Images
- **Axolotl**: Has dedicated background image (`img/Background/Axolotl.png`)
- **Other Pets**: Currently use default grayscale backgrounds (background images needed for cat, dog, raccoon, penguin)
- **Color Theme**: Uses clean black/white/gray color scheme for optimal readability

### App Icon
- **Persistent Icon**: Fixed app icon disappearing after data reset
- **Multiple Formats**: Supports both `.ico` and `.png` icon formats with fallback options


### How to Use

1. **Start Your Journey**: Launch the app and watch your pet hatch from an egg
2. **Study Together**: Use the study timer or take quick quizzes to help your pet grow
3. **Build mastery**: Earn mastery points through studying - reach 200 to evolve!
4. **Auto-Evolution**: Your pet automatically evolves when mastery hits the limit and resets to 0
5. **Final Stage**: Reach Battle-fit stage with 1000 mastery for the ultimate companion

### Project Structure

```
StudyPet/
├── src/
│   ├── screens/          # UI screens and layouts
│   ├── data/             # Pet data models and state management
│   ├── graphics/         # Pet graphics and visual elements
│   ├── ai/               # AI chat integration
│   ├── database/         # Data persistence
│   └── utils/            # Utility functions and helpers
├── bgm/                  # Background music files
├── data/                 # Static data files
└── StudyPet.py           # Main application entry point
```

### Technologies Used

- **Python 3.7+**: Core programming language
- **Tkinter**: Cross-platform GUI framework
- **Local AI Model**: Built-in generative language system
- **SQLite**: Local data storage
- **Pygame**: Audio playback functionality
- **JSON**: Configuration and data serialization

### Contributing

Contributions are welcome! Here are ways you can help:

1. **Report Bugs**: Create issues for any bugs you encounter
2. **Feature Requests**: Suggest new features or improvements
3. **Code Contributions**: Submit pull requests with bug fixes or new features
4. **Documentation**: Help improve documentation and guides

### Support 

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/CookLaye090/StudyPet/issues) page
2. Create a new issue if your problem isn't already reported
3. Include detailed information about your system and the issue

---

**Happy studying with your new pet companion!**
