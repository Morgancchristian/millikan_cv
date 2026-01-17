# M.A.S.E. - Millikan Automated System for Education

## Demo 

https://github.com/user-attachments/assets/f3848bab-aa09-47fe-98b3-fcb8a3cb2903

### Why M.A.S.E.?

The traditional Millikan experiment is time-consuming, error-prone, and requires significant setup. M.A.S.E. addresses these limitations by:
- **Automating data collection** through video annotation
- **Reducing computational errors** with physics calculations
- **Improving accessibility** for modern lab settings
- **Increasing efficiency** by automating manual velocity calculations

## Features

- **Video Playback & Navigation** - Play, pause, frame-step, and fast-forward through experiment videos
- **Interactive Annotation** - Mark droplet positions directly on video frames
- **Real-time Data Visualization** - Charts and gauges displaying droplet velocities and measurements
- **Automatic Calculations** - Computes charge values and elementary charge multiples
- **Physics Engine** - Corrected viscosity, radius, mass, and charge calculations

## Technical Approach

The application uses:
- **OpenCV** for video processing and frame extraction
- **Tkinter** for the GUI interface
- **NumPy & SciPy** for physics calculations and data analysis
- **Matplotlib** for real-time charting

## Requirements

- **Python 3.12.1** or higher
- See `requirements.txt` for all dependencies

## Installation & Setup

### 1. Clone the Repository

```sh
git clone https://github.com/yourusername/millikan-cv.git
cd millikan-cv
```

### 2. Create Virtual Environment

```sh
python -m venv venv
```

### 3. Activate Virtual Environment

**macOS/Linux:**
```sh
source venv/bin/activate
```

**Windows (PowerShell):**
```sh
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```sh
venv\Scripts\activate.bat
```

### 4. Install Dependencies

```sh
pip install -r requirements.txt
```

### 5. Run the Application

```sh
python main.py
```

## Data Setup

The application requires video recordings of the Millikan experiment. You can:

1. **Reach out to me personally for more droplet videos, I have ~ 200:**

2. **Use your own videos:**
   - Place video files (MP4, AVI, MOV, etc.) in the `sample_data/` folder
   - They will automatically appear in the application's video selector

## Project Structure

```
millikan-cv/
├── main.py                  # Main application entry point
├── util.py                  # Video processing utilities
├── requirements.txt         # Python dependencies
├── LICENSE                  # MIT License
├── README.md                # This file
├── components/
│   ├── __init__.py
│   └── ChargeCalculator.py  # Physics calculations 
└── sample_data/             # Place experiment videos here

```

## Usage Guide

1. **Load Videos:** Launch the application and select a video from the `sample_data/` folder
2. **Play Video:** Use the playback controls to navigate through the footage
3. **Annotate:** Click and drag on the video frames to mark droplet positions
4. **Track Data:** The system records positions and calculates velocities in real-time
5. **View Results:** Charts and gauges update automatically with calculated values

## Physics Calculations

The application implements physics formulas for the Millikan experiment:

- **Air Viscosity Correction:** Adjusted for atmospheric pressure and temperature (Millikan's correction formula)
- **Droplet Radius:** r = √[(9ηv_d)/(2ρg)]
- **Droplet Mass:** m = (4/3)πr³ρ
- **Electric Charge:** q = (mg + 6πηrv_u)/E
- **Elementary Charge Multiples:** n = q/e (where e = 1.602176634 × 10⁻¹⁹ C)

### Calibration Parameters

The default calibration values are:
- Pixel-to-mm conversion: 414.20 px/mm
- Electric field: 500 V (at 4.902 mm plate separation)
- Room temperature: 20°C
- Oil density: 0.861 g/cm³

These can be adjusted in `components/ChargeCalculator.py` for different experimental setups.

## Published Research

This application and the associated MillikanCV dataset are presented in the peer-reviewed paper:

**"Modernizing the Millikan Oil-Drop Experiment: A Computer Vision and HCI Approach to Physics Education"**

The paper demonstrates that M.A.S.E. provides substantial improvements over traditional methodologies:
- **Usability:** Significant enhancement in user experience metrics
- **Accuracy:** Reduced error rates in charge measurements relative to the accepted electron value
- **Efficiency:** Substantially faster analysis time per particle

The study employed a comparative user evaluation using the Usability Metric for User Experience (UMUX) scale and Wilcoxon Signed-Rank Tests to validate these improvements.

**Read the full paper:** https://link.springer.com/chapter/10.1007/978-3-031-93965-5_11

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Caleb Christian**

## Contributing

Contributions are welcome! Feel free to open issues for bugs or feature suggestions.
