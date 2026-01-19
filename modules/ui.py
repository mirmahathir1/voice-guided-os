"""
Minimal UI module for text-guided desktop controller.
Provides a simple tkinter interface for command input and execution control.
"""

import tkinter as tk
from tkinter import ttk


class DesktopControllerUI:
    """Main UI class for the desktop controller."""
    
    def __init__(self, on_submit_callback=None, on_stop_callback=None):
        """
        Initialize the UI window.
        
        Args:
            on_submit_callback: Function to call when Run button is clicked or Enter is pressed
            on_stop_callback: Function to call when Stop button is clicked
        """
        self.on_submit_callback = on_submit_callback
        self.on_stop_callback = on_stop_callback
        self.api_call_count = 0
        self.is_running = False
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Desktop Controller")
        self.root.resizable(False, False)
        
        # Set window to stay on top
        self.root.attributes("-topmost", True)
        
        # Create UI elements
        self._create_widgets()
        
        # Bind Enter key to submit
        self.root.bind('<Return>', lambda event: self.on_submit())
        
    def _create_widgets(self):
        """Create and layout all UI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Input frame (text field and buttons)
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Text entry field
        self.command_entry = ttk.Entry(input_frame, width=40)
        self.command_entry.grid(row=0, column=0, padx=(0, 5))
        self.command_entry.insert(0, "Enter command...")
        self.command_entry.bind('<FocusIn>', self._on_entry_focus_in)
        
        # Run button
        self.run_button = ttk.Button(
            input_frame,
            text="Run",
            command=self.on_submit,
            state=tk.NORMAL
        )
        self.run_button.grid(row=0, column=1, padx=(0, 5))
        
        # Stop button
        self.stop_button = ttk.Button(
            input_frame,
            text="Stop",
            command=self.on_stop,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=2)
        
        # API call counter label
        self.api_counter_label = ttk.Label(
            main_frame,
            text="API Calls: 0"
        )
        self.api_counter_label.grid(row=1, column=0, sticky=tk.W)
        
    def _on_entry_focus_in(self, event):
        """Clear placeholder text when entry field is focused."""
        if self.command_entry.get() == "Enter command...":
            self.command_entry.delete(0, tk.END)
    
    def get_command(self):
        """
        Get the text from the input field.
        
        Returns:
            str: The command text, or empty string if placeholder is still shown
        """
        command = self.command_entry.get()
        if command == "Enter command...":
            return ""
        return command
    
    def on_submit(self):
        """Handle Run button click or Enter key press."""
        command = self.get_command()
        if not command:
            return  # Ignore empty commands
        
        # Reset API counter
        self.reset_api_counter()
        
        # Update button states
        self.set_running_state(True)
        
        # Clear the input field
        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, "Enter command...")
        
        # Call the callback if provided
        if self.on_submit_callback:
            self.on_submit_callback(command)
    
    def on_stop(self):
        """Handle Stop button click."""
        # Update button states
        self.set_running_state(False)
        
        # Call the stop callback if provided
        if self.on_stop_callback:
            self.on_stop_callback()
    
    def increment_api_counter(self):
        """Increment the API call counter and update the display."""
        self.api_call_count += 1
        self.api_counter_label.config(text=f"API Calls: {self.api_call_count}")
        self.root.update_idletasks()  # Update display immediately
    
    def reset_api_counter(self):
        """Reset the API call counter to 0."""
        self.api_call_count = 0
        self.api_counter_label.config(text="API Calls: 0")
        self.root.update_idletasks()
    
    def set_running_state(self, is_running):
        """
        Update button states based on running status.
        
        Args:
            is_running (bool): True if execution is running, False otherwise
        """
        self.is_running = is_running
        if is_running:
            self.run_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.run_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
    
    def minimize_window(self):
        """Minimize the window (for screenshot capture)."""
        self.root.iconify()
    
    def restore_window(self):
        """Restore the window from minimized state."""
        self.root.deiconify()
        self.root.attributes("-topmost", True)  # Re-apply topmost attribute
    
    def run(self):
        """Start the tkinter main loop."""
        self.root.mainloop()
    
    def destroy(self):
        """Destroy the window."""
        self.root.destroy()


def create_window(on_submit_callback=None, on_stop_callback=None):
    """
    Create and return a DesktopControllerUI instance.
    
    Args:
        on_submit_callback: Function to call when Run button is clicked or Enter is pressed
        on_stop_callback: Function to call when Stop button is clicked
    
    Returns:
        DesktopControllerUI: The UI instance
    """
    return DesktopControllerUI(on_submit_callback, on_stop_callback)
