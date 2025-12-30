import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import cv2
import os
from util import extract_video_properties, find_slopes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from scipy.signal import find_peaks
from components import ChargeCalculator
from tkinter.ttk import Progressbar

class MillikanExperimentApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Millikan Experiment")
        self.current_page = 0 
        self.charge_calculator = ChargeCalculator()

        # Video and Tracker Variables
        self.video = None
        self.tracker = cv2.TrackerCSRT_create()
        self.current_frame = 0
        self.total_frames = 0
        self.frame_width = 0
        self.frame_height = 0
        self.display_width = 512 
        self.display_height = 512

        self.roi_selection = False
        self.bbox = None
        self.bbox_history = {}
        self.start_x = self.start_y = self.end_x = self.end_y = 0

        self.paused = True
        self.video_path = None
        self.output_path = None
        self.canvas_image = None
        self.video_directory = "input" 

        self.y_centers = []
        self.charge_integer_pairs = []

        # Batch size for updates
        self.batch_size = 50
        self.batch_y_centers = []

        # GUI Layout

        # Progress Bar Frame
        self.progress_frame = tk.Frame(root, bg="white")  # Create a new frame for the progress bar
        self.progress_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)  # Pack it at the top of the root window

        self.progress_bar = Progressbar(self.progress_frame, orient=tk.HORIZONTAL, mode='determinate', length=self.display_width)
        self.progress_bar.pack(fill=tk.X, pady=5) 

        # Left Frame for loading videos
        self.left_frame = tk.Frame(root, width=200, bg="lightgray")
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.video_listbox = tk.Listbox(self.left_frame, width=30)
        self.video_listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.load_videos_button = tk.Button(self.left_frame, text="Load Videos", command=self.load_videos)
        self.load_videos_button.pack(pady=5)

        self.select_video_button = tk.Button(self.left_frame, text="Select Video", command=self.select_video)
        self.select_video_button.pack(pady=5)

        # Right Frame for the 2x2 grid
        self.right_frame = tk.Frame(root)
        self.right_frame.pack(side=tk.TOP, fill=tk.BOTH)

        # Video display and controls (Top Left)
        self.video_container = tk.Frame(self.right_frame)
        self.video_container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Video Canvas
        self.video_canvas = tk.Canvas(self.video_container, width=self.display_width, height=self.display_height)
        self.video_canvas.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Controls Frame
        self.controls_frame = tk.Frame(self.video_container)
        self.controls_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ns")

        # Video Control Buttons (stacked vertically in the controls frame)
        self.play_button = tk.Button(self.controls_frame, text="Play", command=self.play_video, state=tk.DISABLED)
        self.play_button.pack(fill=tk.X, pady=5)

        self.pause_button = tk.Button(self.controls_frame, text="Pause", command=self.pause_video, state=tk.DISABLED)
        self.pause_button.pack(fill=tk.X, pady=5)

        self.forward_button = tk.Button(self.controls_frame, text="Forward", command=self.move_forward, state=tk.DISABLED)
        self.forward_button.pack(fill=tk.X, pady=5)

        self.backward_button = tk.Button(self.controls_frame, text="Backward", command=self.move_backward, state=tk.DISABLED)
        self.backward_button.pack(fill=tk.X, pady=5)

        self.fast_forward_button = tk.Button(self.controls_frame, text="Fast Forward", command=self.move_fast_forward, state=tk.DISABLED)
        self.fast_forward_button.pack(fill=tk.X, pady=5)

        self.fast_backward_button = tk.Button(self.controls_frame, text="Fast Backward", command=self.move_fast_backward, state=tk.DISABLED)
        self.fast_backward_button.pack(fill=tk.X, pady=5)

        # Slider for video scrubbing
        self.slider = tk.Scale(
            self.video_container,
            from_=0,
            to=0,  # This will be updated when a video is loaded
            orient=tk.HORIZONTAL,
            length=self.display_width,
            command=self.on_slider_update
        )
        self.slider.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")




        ##################################################
        # Instructions Frame (Container for instructions and buttons)
        self.instructions_frame = tk.Frame(self.right_frame, bg="white")
        self.instructions_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Configure the layout for instructions_frame
        self.instructions_frame.grid_rowconfigure(0, weight=1)  # Instructions text
        self.instructions_frame.grid_rowconfigure(1, weight=1)  # Image row
        self.instructions_frame.grid_rowconfigure(2, weight=0)  # Empty row for padding (optional)
        self.instructions_frame.grid_rowconfigure(3, weight=0)  # Buttons row
        self.instructions_frame.grid_columnconfigure(0, weight=1)  # For centering elements
        self.instructions_frame.grid_columnconfigure(1, weight=1)  # To position "Next" properly

        # Instructions Label
        self.instructions_label = tk.Label(
            self.instructions_frame,
            text="Instructions: \n1. Load videos\n2. Select a video\n3. Play or analyze",
            bg="white",
            anchor="nw",
            justify="left",
            wraplength=600 # Adjust for better text wrapping
        )
        self.instructions_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        
        ###########################
        # Add visual element (Image)
        self.add_visual_element()
        self.add_visual_element2()
        # Add eq 1
        self.add_equation_widget()
        # Add eq 2 
        self.add_equation_widget2()
        # Add eq 3
        self.add_equation_widget3()
        # Add eq 4
        self.add_equation_widget4()
        # Add eq 5
        self.add_equation_widget5()
        ###########################

        # Back Button (bottom-left of instructions grid)
        self.back_button = tk.Button(self.instructions_frame, text="Back", command=self.back_action, state=tk.DISABLED)
        self.back_button.grid(row=3, column=0, sticky="w", padx=5, pady=5)

        # Next Button (bottom-right of instructions grid)
        self.next_button = tk.Button(self.instructions_frame, text="Next", command=self.next_action)
        self.next_button.grid(row=3, column=1, sticky="e", padx=5, pady=5)
        
        # Page content
        self.pages = [
            "Welcome! This application is designed to help predict the electrical charge of particles.\n\n"
            "In 1909, Robert A. Millikan conducted the famous Oil Drop Experiment, a groundbreaking study that measured the charge of an electron. Millikan achieved this by suspending tiny, charged oil droplets in an electric field and analyzing their motion.\n\n"
            "The diagram below shows an apparatus similar to the one used by Millikan. By carefully controlling the electric field, he was able to make the droplets rise, fall, or remain stationary depending on the balance of forces acting on them.\n\n"
            "Oil droplets are sprayed into a chamber between two closely spaced horizontal plates. These plates, connected to a voltage source, create an electric field. This field can counteract the force of gravity, allowing the charged droplets to be held in place for analysis.\n\n"
            "Click the Next button to Continue.",
            
            "These tiny oil-dropleps viewed through a microscope are under the influence different forces when rising or falling.\n\n"
            "1) Forces Acting on the droplet. \n\n"
            "When the droplet is falling, the forces acting on it can be balanced as follows: \n\n\n\n\n\n\n\n"
            "Where: V(t) is the terminal velocity of the falling droplet, r is the radius of the droplet, η is the viscosity of air, ρ oil density of the oil, ρ air is the density of the air, and g is gravity.\n\n"
            "The radius of the droplet is calculated using: \n\n\n\n\n\n\n\n\n\n\n\n"
            "Click the Next button to Continue.",
            
            "2) Forces During the Droplets Ascent\n\n"
            "When the droplet rises under the influence of the electric field, the forces balance differently. The electric force must overcome both gravity and drag: \n\n\n\n\n\n\n"
            "Where: V(u) is the rising velocity of the droplet, and E is the electric field strength.\n\n"
            
            
            "Using the relationship E = V / d, this becomes:\n\n\n\n\n\n\n\n\n"
            "From this, the charge q is determined:\n\n\n\n\n\n\n\n\n"
            "Click the Next button to Continue.",
            
            "R.A. Millikan measured the charge (q) of many different particles. As he plotted this data, he noticed something interesting…\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
            "Millikan observed that the difference in electric charge between individual particles was consistently a multiple of a specific fundamental value, suggesting that electric charge is quantized.\n\n"
            "Millikan determined that electrons carry a discrete, fundamental unit of electric charge, which he measured as e ≈ 1.602e-19. This discovery confirmed that electric charge is quantized.\n\n"
            "Click the Next button to Continue.",
            
            "Computing Electrical Charge.\n\n"
            "As noted in the final equation, several variables must be considered to calculate  q , the charge of an oil droplet in Coulombs.\n\n"
            "This application is designed to work with the MillikanCV dataset, providing nearly all the variables required to calculate the electrical charge: \n"
            "Voltage (V) = 500 volts\n\n"
            "Distance (d) = 4.902e-3 m \n"
            "Viscosity of air (η) = 1.81801e-5 Pas\n\n"
            "Density of oil (ρₒᵢₗ) = 0.861e3 kg/m³\n\n"
            "Density of air (ρₐᵢᵣ) = 1.01 kg/m³\n\n"
            "Upward Velocity (vᵤ) = ?\n\n"
            "Terminal Velocity (vₐ) = ?\n\n"
            "As shown above, we have all the necessary variables to calculate the electrical charge of a particle, except for the upward velocity (when the particle is rising due to electric charge) and the terminal velocity (when the particle is falling due to gravity).\n\n"
            "That's where you come in!\n\n\n\n\n\n\n"
            "Click the Next button to Continue.",
            
            "General Instructions.\n\n"
            "This application is designed to help students accurately find the upward velocity (vᵤ) and Terminal Velocity (vₐ) of oil droplets using the MillikanCV dataset. \n"
            "By tracking a particle’s motion in the video, the application calculates the electrical charge (q) of the droplet. Follow the steps below to analyze the videos and record the results.\n\n"
            "Lets begin: \n"
            "Step 1:Click the ‘Load Videos’ button in the left-hand corner. If the videos do not appear in the list immediately, navigate to the folder containing the MillikanCV videos and load them.\n\n"
            "Step 2: Select a video from the list by clicking on it, then click the ‘Select Video’ button.\n\n"
            "Step 3: Use the slider below the video to play it and locate the particle you wish to track. Identify the particle that remains in the frame for the entire video duration, moving up and down consistently.\n\n"
            "Step 4: Once the particle is identified, click and drag the cursor to draw a bounding box around it.\n\n"
            "Step 5: Press the ‘Play’ button to start tracking the particle. The bounding box should follow the particle.\n\n"
            "Step 6: Observe the particle’s motion as it falls and rises. A graph will display the Y-coordinate of the particle over time. Once sufficient data is collected, the charge (q) will be displayed in the bottom-right corner.\n\n"
            "Step 7: Wait for the video to complete. The progress bar at the top of the application indicates the video’s duration.\n\n"
            "Step 8: Record the video name, the displayed charge (q), and the value q/e shown below. Round q/e to the nearest integer.\n\n"
        ]

        # Initialize the first page
        self.update_page()
        
        # Configure the layout for instructions_frame
        self.instructions_frame.grid_rowconfigure(0, weight=1)  # Instructions text
        self.instructions_frame.grid_rowconfigure(1, weight=0)  # Buttons row
        self.instructions_frame.grid_columnconfigure(0, weight=1)  # Back button
        self.instructions_frame.grid_columnconfigure(1, weight=1)  # Next button

        ##################################################
        

        # Chart (Bottom Left)
        self.chart_frame = tk.Frame(self.right_frame)
        self.chart_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.figure = Figure(figsize=(4, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.figure, self.chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Charge Prediction Frame
        self.prediction_frame = tk.Frame(self.right_frame, bg="white")
        self.prediction_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Placeholder label for "Gathering more data..."
        self.placeholder_label = tk.Label(
            self.prediction_frame, 
            text="Gathering more data...", 
            bg="white", 
            font=("Arial", 14), 
            fg="blue"
        )
        self.placeholder_label.pack(fill=tk.BOTH, expand=True)

        # Sub Frame
        self.prediction_sub_frame = tk.Frame(self.prediction_frame, bg="white")
        # self.prediction_sub_frame.pack(fill=tk.BOTH, expand=True)

        # Vertical Gauge for Charge
        self.gauge_figure = Figure(figsize=(2.5, 3), dpi=100)
        self.gauge_ax = self.gauge_figure.add_subplot(111)
        self.gauge_chart_canvas = FigureCanvasTkAgg(self.gauge_figure, self.prediction_sub_frame)
        self.gauge_chart_canvas.get_tk_widget().pack(
            side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=False,
        )

        # Integer Scatter Plot Chart
        self.integer_figure = Figure(figsize=(3, 1), dpi=100) 
        self.integer_ax = self.integer_figure.add_subplot(111)
        self.integer_chart_canvas = FigureCanvasTkAgg(self.integer_figure, self.prediction_sub_frame)
        self.integer_chart_canvas.get_tk_widget().pack(
            side=tk.RIGHT, padx=5, pady=5, fill=tk.BOTH, expand=False 
        )

        # Configure row and column weights for dynamic resizing
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(1, weight=1)

        # Configure the layout for dynamic resizing
        self.video_container.grid_rowconfigure(0, weight=1)  # Video canvas and controls
        self.video_container.grid_rowconfigure(1, weight=0)  # Slider
        self.video_container.grid_columnconfigure(0, weight=1)  # Video canvas
        self.video_container.grid_columnconfigure(1, weight=0)  # Controls frame

    def load_videos(self):
        """Load video files from a user-selected directory into the Listbox."""
        self.highlight_button(self.load_videos_button)
        self.video_listbox.delete(0, tk.END)

        # Open a dialog for the user to select a folder
        selected_directory = filedialog.askdirectory(title="Select Video Directory")
        if not selected_directory:  # If the user cancels the dialog
            return

        self.video_directory = selected_directory

        # List videos in the selected directory
        videos = [f for f in os.listdir(self.video_directory) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
        if not videos:
            messagebox.showinfo("No Videos Found", "No video files were found in the selected directory.")
            return

        for video in videos:
            self.video_listbox.insert(tk.END, video)

    def select_video(self):
        """Handle video selection from the Listbox."""
        self.highlight_button(self.select_video_button)
        selected_index = self.video_listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "No video selected.")
            return
        
        # Reset states
        self.reset_states()

        selected_video = self.video_listbox.get(selected_index)
        self.video_path = os.path.join(self.video_directory, selected_video)

        # Set up video properties
        self.video = cv2.VideoCapture(self.video_path)
        if not self.video.isOpened():
            messagebox.showerror("Error", f"Could not open video {self.video_path}")
            return

        # Extract video properties
        self.total_frames, self.frame_width, self.frame_height = extract_video_properties(self.video)

        # Prepare output directory
        base_name = os.path.basename(self.video_path).split('.')[0]
        self.output_path = os.path.join('output', base_name)
        os.makedirs(self.output_path, exist_ok=True)

        # Enable controls
        self.play_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.NORMAL)
        self.forward_button.config(state=tk.NORMAL)
        self.backward_button.config(state=tk.NORMAL)
        self.fast_forward_button.config(state=tk.NORMAL)
        self.fast_backward_button.config(state=tk.NORMAL)

        # Read the first frame
        ret, self.frame = self.video.read()
        if ret:
            self.current_frame = 0
            self.frame = cv2.resize(self.frame, (self.display_width, self.display_height))
            self.display_frame(self.frame)

            if self.slider is not None:
                self.slider.config(to=self.total_frames - 1)  # Set slider range
                self.slider.set(self.current_frame)

            # Bind Mouse Event Listeners to Canvas
            self.video_canvas.bind("<ButtonPress-1>", self.on_mouse_down)
            self.video_canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.video_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        else:
            messagebox.showerror("Error", "Could not read the first frame of the video")
    
    def update_page(self):
        """Update the instructions label and buttons based on the current page."""
        # Set the text for the current page
        self.instructions_label.config(text=self.pages[self.current_page])

        # Show or hide the image depending on the page
        if self.current_page == 0:
            self.image_label.grid()  # Show the image on the first page
        else:
            self.image_label.grid_remove()  # Hide the image on other pages
        
        if self.current_page == 3:
            self.image_label2.grid()  # Show the image on the first page
        else:
            self.image_label2.grid_remove()  # Hide the image on other pages
        
        # Show/hide equation
        if self.current_page == 1: 
            # Example: On page 1, display the equation
            self.set_equation_text(r"$6 \pi \eta r v_t = \frac{4}{3} \pi r^3 (\rho_{\text{oil}} - \rho_{\text{air}}) \cdot g$")
            self.equation_widget.grid()
            
            self.set_equation_text2(r"$r = \sqrt{\frac{9 \eta v_t}{2 g (\rho_{\text{oil}} - \rho_{\text{air}})}}$") 
            self.equation_widget2.grid()
        else:
            self.equation_widget.grid_remove()
            self.equation_widget2.grid_remove()
        
        if self.current_page == 2:
            self.set_equation_text3(r"$q \cdot E = 6 \pi \eta r v_u + \frac{4}{3} \pi r^3 (\rho_{\text{oil}} - \rho_{\text{air}}) \cdot g$")
            self.equation_widget3.grid()
            
            self.set_equation_text4(r"$q \cdot \frac{V}{d} = 6 \pi \eta r v_u + \frac{4}{3} \pi r^3 (\rho_{\text{oil}} - \rho_{\text{air}}) \cdot g$")
            self.equation_widget4.grid()
            
            self.set_equation_text5(r"$q = \frac{6 \pi \eta r v_u + \frac{4}{3} \pi r^3 (\rho_{\text{oil}} - \rho_{\text{air}}) \cdot g}{\left(\frac{V}{d}\right)}$")
            self.equation_widget5.grid()
            
        else:
            self.equation_widget3.grid_remove()
            self.equation_widget4.grid_remove()
            self.equation_widget5.grid_remove()
           
            
            
        # Enable or disable buttons based on the current page
        if self.current_page == 0:
            self.back_button.config(state=tk.DISABLED)  # Disable back on the first page
        else:
            self.back_button.config(state=tk.NORMAL)

        if self.current_page == len(self.pages) - 1:
            self.next_button.config(state=tk.DISABLED)  # Disable next on the last page
        else:
            self.next_button.config(state=tk.NORMAL)
        
    def back_action(self):
        """Handle the Back button click."""
        if self.current_page > 0:
            self.highlight_button(self.back_button)
            self.current_page -= 1
            self.update_page()

    def next_action(self):
        """Handle the Next button click."""
        if self.current_page < len(self.pages) - 1:
            self.highlight_button(self.next_button)
            self.current_page += 1
            self.update_page()
            
    def add_visual_element(self):
        """Add an image to the instructions frame."""
        image_path = os.path.join('media', 'millikanApparatus.png')
        image = Image.open(image_path).resize((400, 300), Image.Resampling.LANCZOS)  # Resize image
        self.image_tk = ImageTk.PhotoImage(image)  # Keep a reference to avoid garbage collection

        # Create a label for the image
        self.image_label = tk.Label(self.instructions_frame, image=self.image_tk, bg="white")
        self.image_label.grid(row=1, column=0, columnspan=2, pady=10, sticky="n")  # Center image horizontally
        
    def add_visual_element2(self):
        """Add a second image to the instructions frame."""
        image_path = os.path.join('media', 'Charge_vs_Integer_Multiple.png')
        image2 = Image.open(image_path).resize((500, 400), Image.Resampling.LANCZOS)  # Resize image
        self.image_tk2 = ImageTk.PhotoImage(image2)  # Keep a separate reference to avoid garbage collection

        # Create a label for the second image
        self.image_label2 = tk.Label(self.instructions_frame, image=self.image_tk2, bg="white")
        self.image_label2.grid(row=0, column=0, columnspan=2, pady=(60, 80), sticky="n")  # Position it in a new row
        
        

    def add_equation_widget(self):
        """Create the matplotlib figure to display a LaTeX equation, then hide it initially."""
        self.equation_figure = Figure(figsize=(3, 1), dpi=100) #(Width, Height)
        self.equation_ax = self.equation_figure.add_subplot(111)
        self.equation_ax.axis('off')  # Hide axes for a cleaner look

        self.equation_canvas = FigureCanvasTkAgg(self.equation_figure, self.instructions_frame)
        self.equation_widget = self.equation_canvas.get_tk_widget()
        
        # Position in grid, but hide initially
        self.equation_widget.grid(row=0, column=0, columnspan=2, pady=(130,80), sticky="n")
        self.equation_widget.grid_remove() # Hide for now   
        
    def set_equation_text(self, latex_equation: str):
        """Render the LaTeX equation text in the existing matplotlib figure."""
        # Clear old text
        self.equation_ax.clear()
        self.equation_ax.axis('off')

        # Render the new LaTeX equation
        self.equation_ax.text(
            0.5, 0.5,
            latex_equation,
            fontsize=16,
            ha='center',
            va='center',
            transform=self.equation_ax.transAxes
        )
        self.equation_canvas.draw()
        
    def add_equation_widget2(self):
        """Create a second matplotlib figure to display another LaTeX equation, then hide it initially."""
        self.equation_figure2 = Figure(figsize=(3, 1), dpi=100)
        self.equation_ax2 = self.equation_figure2.add_subplot(111)
        self.equation_ax2.axis('off')  # Hide axes for a cleaner look

        self.equation_canvas2 = FigureCanvasTkAgg(self.equation_figure2, self.instructions_frame)
        self.equation_widget2 = self.equation_canvas2.get_tk_widget()
        
        # Position in the grid but hide for now
        # Adjust row/column to your liking (e.g., row=2 or row=3)
        self.equation_widget2.grid(row=0, column=0, columnspan=2, pady=(330, 80), sticky="n")
        self.equation_widget2.grid_remove()  # Hide initially
    
    def set_equation_text2(self, latex_equation: str):
        """Render the LaTeX equation text in the second matplotlib figure."""
        self.equation_ax2.clear()
        self.equation_ax2.axis('off')

        self.equation_ax2.text(
            0.5, 0.5,
            latex_equation,
            fontsize=16,
            ha='center',
            va='center',
            transform=self.equation_ax2.transAxes
        )
        self.equation_canvas2.draw() 
        
    def add_equation_widget3(self):
        """Create a second matplotlib figure to display another LaTeX equation, then hide it initially."""
        self.equation_figure3 = Figure(figsize=(5, 1), dpi=100)
        self.equation_ax3 = self.equation_figure3.add_subplot(111)
        self.equation_ax3.axis('off')  # Hide axes for a cleaner look

        self.equation_canvas3 = FigureCanvasTkAgg(self.equation_figure3, self.instructions_frame)
        self.equation_widget3 = self.equation_canvas3.get_tk_widget()
        
        # Position in the grid but hide for now
        # Adjust row/column to your liking (e.g., row=2 or row=3)
        self.equation_widget3.grid(row=0, column=0, columnspan=2, pady=(80, 80), sticky="n")
        self.equation_widget3.grid_remove()  # Hide initially
    
    def set_equation_text3(self, latex_equation: str):
        """Render the LaTeX equation text in the second matplotlib figure."""
        self.equation_ax3.clear()
        self.equation_ax3.axis('off')

        self.equation_ax3.text(
            0.5, 0.5,
            latex_equation,
            fontsize=16,
            ha='center',
            va='center',
            transform=self.equation_ax3.transAxes
        )
        self.equation_canvas3.draw() 
    
    def add_equation_widget4(self):
        """Create a second matplotlib figure to display another LaTeX equation, then hide it initially."""
        self.equation_figure4 = Figure(figsize=(5, 1), dpi=100)
        self.equation_ax4 = self.equation_figure4.add_subplot(111)
        self.equation_ax4.axis('off')  # Hide axes for a cleaner look

        self.equation_canvas4 = FigureCanvasTkAgg(self.equation_figure4, self.instructions_frame)
        self.equation_widget4 = self.equation_canvas4.get_tk_widget()
        
        # Position in the grid but hide for now
        # Adjust row/column to your liking (e.g., row=2 or row=3)
        self.equation_widget4.grid(row=0, column=0, columnspan=2, pady=(250, 200), sticky="n")
        self.equation_widget4.grid_remove()  # Hide initially
    
    def set_equation_text4(self, latex_equation: str):
        """Render the LaTeX equation text in the second matplotlib figure."""
        self.equation_ax4.clear()
        self.equation_ax4.axis('off')

        self.equation_ax4.text(
            0.5, 0.5,
            latex_equation,
            fontsize=16,
            ha='center',
            va='center',
            transform=self.equation_ax4.transAxes
        )
        self.equation_canvas4.draw() 
    
    def add_equation_widget5(self):
        """Create a second matplotlib figure to display another LaTeX equation, then hide it initially."""
        self.equation_figure5 = Figure(figsize=(3, 1), dpi=100)
        self.equation_ax5 = self.equation_figure5.add_subplot(111)
        self.equation_ax5.axis('off')  # Hide axes for a cleaner look

        self.equation_canvas5 = FigureCanvasTkAgg(self.equation_figure5, self.instructions_frame)
        self.equation_widget5 = self.equation_canvas5.get_tk_widget()
        
        # Position in the grid but hide for now
        # Adjust row/column to your liking (e.g., row=2 or row=3)
        self.equation_widget5.grid(row=0, column=0, columnspan=2, pady=(380, 50), sticky="n")
        self.equation_widget5.grid_remove()  # Hide initially
    
    def set_equation_text5(self, latex_equation: str):
        """Render the LaTeX equation text in the second matplotlib figure."""
        self.equation_ax5.clear()
        self.equation_ax5.axis('off')

        self.equation_ax5.text(
            0.5, 0.5,
            latex_equation,
            fontsize=16,
            ha='center',
            va='center',
            transform=self.equation_ax5.transAxes
        )
        self.equation_canvas5.draw() 
    
    def reset_states(self):
        """Reset all states to their initial values."""
        # Reset variables
        self.video = None
        self.tracker = cv2.TrackerCSRT_create()
        self.current_frame = 0
        self.total_frames = 0
        self.frame_width = 0
        self.frame_height = 0
        self.bbox = None
        self.bbox_history = {}
        self.y_centers = []
        self.charge_integer_pairs = []
        self.batch_y_centers = []
        self.paused = True

        # Reset UI components
        self.video_canvas.delete("all")
        self.canvas_image = None
        self.progress_bar['value'] = 0
        self.ax.clear()
        self.chart_canvas.draw()
        self.gauge_ax.clear()
        self.gauge_chart_canvas.draw()
        self.integer_ax.clear()
        self.integer_chart_canvas.draw()
        self.placeholder_label.pack(fill=tk.BOTH, expand=True) 
        self.prediction_sub_frame.pack_forget()
    

        print('Reset Called')

        if self.slider is None:

            self.slider = tk.Scale(
                self.video_container,
                from_=0,
                to=0,
                orient=tk.HORIZONTAL,
                length=self.display_width,
                command=self.on_slider_update
            )
            self.slider.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
            

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.roi_selection = True

    def on_mouse_drag(self, event):
        if self.roi_selection:
            self.end_x = event.x
            self.end_y = event.y
            self.video_canvas.delete("roi")
            self.video_canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline="blue", tag="roi")

    def on_mouse_up(self, event):
        if self.roi_selection:
            self.end_x = event.x
            self.end_y = event.y
            self.roi_selection = False
            self.bbox = (self.start_x, self.start_y, self.end_x - self.start_x, self.end_y - self.start_y)
            self.bbox
            self.tracker.init(self.frame, self.bbox)
            self.bbox_history[self.current_frame] = self.bbox

        # Safely remove the slider
        if self.slider is not None:
            self.slider.pack_forget()
            self.slider.destroy()
            self.slider = None

    def play_video(self):
        if self.paused:
            self.highlight_button(self.play_button)
            self.video_canvas.delete("roi")
            self.paused = False
            self.update_video_frame()
            self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.ACTIVE)
            self.forward_button.config(state=tk.DISABLED)
            self.backward_button.config(state=tk.DISABLED)
            self.fast_forward_button.config(state=tk.DISABLED)
            self.fast_backward_button.config(state=tk.DISABLED)

    def pause_video(self):
        if not self.paused:
            self.highlight_button(self.pause_button)
            self.paused = True
            self.play_button.config(state=tk.ACTIVE)
            self.pause_button.config(state=tk.DISABLED)
            self.forward_button.config(state=tk.ACTIVE)
            self.backward_button.config(state=tk.ACTIVE)
            self.fast_forward_button.config(state=tk.ACTIVE)
            self.fast_backward_button.config(state=tk.ACTIVE)

    def update_video_frame(self):
        if not self.bbox:
            messagebox.showinfo("Missed Step","Must select an area on the video first.")
            return

        if self.paused or not self.video.isOpened():
            return

        ret, self.frame = self.video.read()
        if not ret:
            messagebox.showinfo("End of Video", "Video playback completed")
            return

        self.frame = cv2.resize(self.frame, (self.display_width, self.display_height))
        self.current_frame += 1
        ret, bbox = self.tracker.update(self.frame)
        if ret:
            self.bbox_history[self.current_frame] = bbox
            self.batch_y_centers.append((self.current_frame, bbox[1] + bbox[3] / 2))
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(self.frame, p1, p2, (255, 0, 0), 2, 1)

        # Update the batch when batch size is reached
        if len(self.batch_y_centers) >= self.batch_size:
            self.process_batch_data()
            self.batch_y_centers = [] 

        
        self.display_frame(self.frame)

        # Update the progress bar
        progress = (self.current_frame / self.total_frames) * 100
        self.progress_bar['value'] = progress

        self.root.after(10, self.update_video_frame)

    def process_batch_data(self):
        """Process batch data using numpy for efficient computation."""
        if len(self.batch_y_centers) == 0:
            return

        batch_array = np.array(self.batch_y_centers)
        normalized_y_centers = batch_array[:, 1] / self.display_height
        self.y_centers.extend(normalized_y_centers.tolist())
        self.update_chart()

    def update_chart(self):
        """Find and plot peaks and troughs in y-center data, ensuring the first and last data points are treated as specified."""
        y = np.array(self.y_centers) * 512  # Scale to pixel values
        t = np.arange(len(self.y_centers))  # Time indices

        # Use numpy functions to find peaks and troughs
        peaks, _ = find_peaks(y, distance=100, prominence=100)
        troughs, _ = find_peaks(-y, distance=100, prominence=100)

        # Enforce the first and last frame conditions
        if 0 not in troughs:
            troughs = np.append([0], troughs)
        if len(peaks) > 0 and len(troughs) > 0:
            if peaks[-1] > troughs[-1]:
                if len(y) - 1 not in troughs:
                    troughs = np.append(troughs, [len(y) - 1])
            else:
                if len(y) - 1 not in peaks:
                    peaks = np.append(peaks, [len(y) - 1])

        # Create lists of tuples for peaks and troughs
        peak_points = [(t[index], y[index]) for index in peaks]
        trough_points = [(t[index], y[index]) for index in troughs]

        try:
            vu, vd = find_slopes(peak_points, trough_points)
            charge, integer = self.charge_calculator.find_charge_and_integer(vu, vd)
            self.update_prediction_display(charge, integer)
        except ValueError as e:
            pass

        # Plotting
        self.ax.clear()
        self.ax.set_title('Detected Peaks and Troughs in Y-Center Data')
        self.ax.set_xlabel('Frame Index')
        self.ax.set_ylabel('Y-Center Value')
        self.ax.grid(True)
        self.ax.plot(t, y, label='Y-Center Data', color='black')
        self.ax.plot(t[peaks], y[peaks], 'x', label='Peaks', color='blue')
        self.ax.plot(t[troughs], y[troughs], 'bo', label='Troughs')
        self.ax.invert_yaxis()
        self.ax.legend()
        self.chart_canvas.draw()

    def display_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        if self.canvas_image is None:
            self.canvas_image = self.video_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        else:
            self.video_canvas.itemconfig(self.canvas_image, image=imgtk)
        self.video_canvas.image = imgtk

    def move_forward(self):
        if self.current_frame < self.total_frames - 1:
            self.highlight_button(self.forward_button)
            self.current_frame += 1
            self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = self.video.read()
            if ret:
                frame = cv2.resize(frame, (self.display_width, self.display_height))
                bbox = self.bbox_history.get(self.current_frame, None)
                if bbox:
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                self.display_frame(frame)

    def move_backward(self):
        if self.current_frame > 0:
            self.highlight_button(self.backward_button)
            self.current_frame -= 1
            self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = self.video.read()
            if ret:
                frame = cv2.resize(frame, (self.display_width, self.display_height))
                bbox = self.bbox_history.get(self.current_frame, None)
                if bbox:
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                self.display_frame(frame)
                
                # Handle data removal
                if len(self.batch_y_centers) > 0:
                    # Remove the last element from the batch
                    self.batch_y_centers.pop()
                elif len(self.y_centers) > 0:
                    # Remove from y_centers if batch is empty
                    self.y_centers.pop()
                    # Remove from charge_interval_pairs only if we've gone backward by more than a batch
                    if self.current_frame % self.batch_size == 0 and len(self.charge_integer_pairs) > 0:
                        self.charge_integer_pairs.pop()
                
                # Update bbox history
                if self.current_frame in self.bbox_history:
                    del self.bbox_history[self.current_frame]


    def move_fast_forward(self):
        if self.current_frame < self.total_frames - 1:
            self.highlight_button(self.fast_backward_button)
            self.current_frame += 10
            self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = self.video.read()
            if ret:
                frame = cv2.resize(frame, (self.display_width, self.display_height))
                bbox = self.bbox_history.get(self.current_frame, None)
                if bbox:
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                self.display_frame(frame)

    def move_fast_backward(self):
        if self.current_frame > 0:
            self.highlight_button(self.fast_backward_button)
            frames_to_skip = 10  # Define how many frames to skip backward
            self.current_frame = max(0, self.current_frame - frames_to_skip)
            self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = self.video.read()
            if ret:
                frame = cv2.resize(frame, (self.display_width, self.display_height))
                bbox = self.bbox_history.get(self.current_frame, None)
                if bbox:
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                self.display_frame(frame)
            
            # Handle data removal
            for _ in range(frames_to_skip):
                if len(self.batch_y_centers) > 0:
                    # Remove the last element from the batch
                    self.batch_y_centers.pop()
                elif len(self.y_centers) > 0:
                    # Remove from y_centers if batch is empty
                    self.y_centers.pop()
                    # Remove from charge_interval_pairs if backward movement crosses batch boundaries
                    if self.current_frame % self.batch_size == 0 and len(self.charge_integer_pairs) > 0:
                        self.charge_integer_pairs.pop()
            
            # Update bbox history
            for frame_idx in range(self.current_frame, self.current_frame + frames_to_skip):
                if frame_idx in self.bbox_history:
                    del self.bbox_history[frame_idx]

    def highlight_button(self, button):
        # Reset all buttons to their default style
        buttons = [
            self.play_button,
            self.pause_button,
            self.forward_button,
            self.backward_button,
            self.fast_forward_button,
            self.fast_backward_button,
        ]
        for btn in buttons:
            btn.config(bg="SystemButtonFace", fg="black")  

        # Highlight the selected button
        button.config(bg="blue", fg="white")

        self.root.after(150, lambda: button.config(bg="SystemButtonFace", fg="black"))

    def on_slider_update(self, value):
        if not self.slider:
            return 
        
        if self.video and not self.paused:  # Pause video if it's playing
            self.paused = True

        self.current_frame = int(value)
        self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.video.read()
        if ret:
            frame = cv2.resize(frame, (self.display_width, self.display_height))
            bbox = self.bbox_history.get(self.current_frame, None)
            if bbox:
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
            self.display_frame(frame)

    def update_prediction_display(self, charge, integer):
        """Update the gauge and bar chart with new prediction values or switch from placeholder."""
        if not charge or not integer:
            self.placeholder_label.pack(fill=tk.BOTH, expand=True)  
            self.prediction_sub_frame.pack_forget()  
            return  

        self.placeholder_label.pack_forget()  
        self.prediction_sub_frame.pack(fill=tk.BOTH, expand=True)  

        # Update the gauge and integer chart
        self.update_gauge(charge)
        self.update_integer_chart(charge, integer)

    def update_gauge(self, charge):
        """Update the vertical gauge using matplotlib."""
        max_charge = 1e-18  # Adjust maximum for better scaling
        normalized_charge = min(charge / max_charge, 1.0)

        # Clear the previous gauge
        self.gauge_ax.clear()

        # Plot the vertical bar
        self.gauge_ax.bar(
            [0],  
            [normalized_charge * max_charge],  
            width=0.4, color="blue", edgecolor="black"
        )

        # Add labels and formatting
        self.gauge_ax.set_ylim(0, max_charge)  
        self.gauge_ax.set_xlim(-1.0, 1.0)
        self.gauge_ax.set_xticks([]) 
        self.gauge_ax.set_ylabel("q = Charge (C)", fontsize=8)
        self.gauge_ax.tick_params(axis="y", labelsize=8)
        self.gauge_ax.grid(True, axis="y", linestyle="--", alpha=0.6)

        # Set a title with the charge value
        self.gauge_ax.set_title(
            f"q = {charge:.2e} C", fontsize=10, color="blue", pad=15
        )

        # Adjust layout to ensure no clipping
        self.gauge_figure.subplots_adjust(left=0.3, right=.95, top=0.8, bottom=0.1)

        # Redraw the gauge
        self.gauge_chart_canvas.draw()

    def update_integer_chart(self, charge, integer):
        """Update the histogram for integer observations."""
        self.integer_ax.clear()

        if integer is not None:
            self.charge_integer_pairs.append((charge, integer))

        # Convert integers to numpy array
        integers = np.array([pair[1] for pair in self.charge_integer_pairs])

        # Calculate histogram bins and counts using numpy
        bins = np.linspace(np.min(integers), np.max(integers), 11)
        counts, edges = np.histogram(integers, bins=bins)

        # Find the bin with the highest count (mode bin)
        max_count_index = np.argmax(counts)
        mode_bin = (edges[max_count_index] + edges[max_count_index + 1]) / 2  # Calculate bin center

        # Plot histogram
        self.integer_ax.bar(edges[:-1], counts, width=np.diff(edges), align="edge", color="blue", edgecolor="black", alpha=0.7)

        # Add line for the mode bin
        self.integer_ax.axvline(x=mode_bin, color="red", linestyle="--", linewidth=1)

        # Set titles and labels
        self.integer_ax.set_title("Histogram of Integers", fontsize=10)
        self.integer_ax.set_xlabel("q/e = Integer", fontsize=8)
        self.integer_ax.set_ylabel("Count", fontsize=8)
        self.integer_ax.grid(True)

        # Annotate the mode bin
        self.integer_ax.annotate(
            f"Electron Count: {round(mode_bin)}",
            xy=(0.5, 1.25), xycoords='axes fraction',
            fontsize=10, color="red", ha="center"
        )

        self.integer_figure.tight_layout()
        self.integer_ax.tick_params(axis='both', which='major', labelsize=8)
        self.integer_chart_canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = MillikanExperimentApp(root)
    root.mainloop()
