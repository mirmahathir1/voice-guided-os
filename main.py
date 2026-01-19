#!/usr/bin/env python3
"""
Main entry point for the text-guided desktop controller.
Integrates all modules and implements the main control loop.
"""

import time
import config
from modules.screenshot import capture_full_screen
from modules.llm_client import LLMClient
from modules.grid_processor import (
    overlay_3x3_grid,
    get_cell_bounds, get_cell_center, crop_cell
)
from modules.action_executor import click_at, right_click_at, double_click_at, type_text, press_button
from modules.execution_logger import ExecutionLogger


class DesktopController:
    """Main controller class that orchestrates all components."""

    def __init__(self):
        """Initialize all components."""
        self.llm_client = LLMClient()
        self.logger = ExecutionLogger()
        self.stop_flag = False
        self.is_running = False

    def run_action_loop(self, command):
        """
        Main action loop that processes the user command.

        Args:
            command (str): User's text command
        """
        self.is_running = True
        self.stop_flag = False
        iteration_count = 0

        try:
            # Create execution folder and save command
            self.logger.create_execution_folder()
            self.logger.save_command(command)

            # Reset LLM conversation history
            self.llm_client.reset_conversation()

            # Main loop
            while iteration_count < config.MAX_ITERATIONS:
                # Check if stop was requested
                if self.stop_flag:
                    print(f"Execution stopped by user after {iteration_count} iterations")
                    break

                iteration_count += 1
                print(f"\n--- Iteration {iteration_count} ---")

                try:
                    # Step 1: Capture screenshot
                    print("Capturing screenshot...")
                    screenshot = capture_full_screen()
                    self.logger.save_screenshot(screenshot, step=iteration_count)

                    # Step 2: Get action from LLM
                    print("Querying LLM for action...")

                    # Create a temporary logger that saves with the current step
                    class StepLogger:
                        def __init__(self, logger, step):
                            self.logger = logger
                            self.step = step

                        def save_prompt(self, prompt):
                            self.logger.save_prompt(prompt, step=self.step)

                        def save_response(self, response):
                            self.logger.save_response(response, step=self.step)

                    step_logger = StepLogger(self.logger, iteration_count)
                    action_response = self.llm_client.get_action_plan(
                        screenshot, command, logger=step_logger
                    )

                    action = action_response.get("action", "")
                    target = action_response.get("target", "")
                    text = action_response.get("text", "")
                    button = action_response.get("button", "")
                    print(f"Action determined: {action}" + (f" - {target}" if target else "") + (f" - text: {text}" if text else "") + (f" - button: {button}" if button else ""))

                    # Step 3: Handle different action types
                    if action == "COMPLETE":
                        print("Task completed successfully!")
                        # Generate PDF for this step
                        try:
                            pdf_path = self.logger.generate_step_pdf(iteration_count)
                            if pdf_path:
                                print(f"Generated step PDF: {pdf_path}")
                        except Exception as e:
                            print(f"Warning: Could not generate step PDF: {e}")
                        break

                    elif action == "ERROR":
                        reason = action_response.get("reason", "Unknown error")
                        print(f"Error: {reason}")
                        # Generate PDF for this step
                        try:
                            pdf_path = self.logger.generate_step_pdf(iteration_count)
                            if pdf_path:
                                print(f"Generated step PDF: {pdf_path}")
                        except Exception as e:
                            print(f"Warning: Could not generate step PDF: {e}")
                        break

                    elif action == "KEYBOARD_TYPE":
                        # Handle keyboard typing action
                        if not text:
                            print("Warning: KEYBOARD_TYPE action specified but no text provided")
                            continue
                        
                        print(f"Typing text: {text}")
                        type_text(text)
                        
                        # Add action to history
                        self.llm_client.add_action(action, text)
                        
                        # Capture final screenshot after typing
                        final_screenshot = capture_full_screen()
                        self.logger.save_final_screenshot(final_screenshot, None, None, step=iteration_count)
                        
                        print(f"Text typed: {text}")
                        
                        # Generate PDF for this step after all files are saved
                        try:
                            pdf_path = self.logger.generate_step_pdf(iteration_count)
                            if pdf_path:
                                print(f"Generated step PDF: {pdf_path}")
                        except Exception as e:
                            print(f"Warning: Could not generate step PDF: {e}")
                        
                        # Continue to next iteration
                        continue

                    elif action == "KEYBOARD_BUTTON_PRESS":
                        # Handle keyboard button press action
                        if not button:
                            print("Warning: KEYBOARD_BUTTON_PRESS action specified but no button provided")
                            continue
                        
                        print(f"Pressing button: {button}")
                        try:
                            press_button(button)
                        except ValueError as e:
                            print(f"Error: {str(e)}")
                            continue
                        
                        # Add action to history
                        self.llm_client.add_action(action, button)
                        
                        # Capture final screenshot after button press
                        final_screenshot = capture_full_screen()
                        self.logger.save_final_screenshot(final_screenshot, None, None, step=iteration_count)
                        
                        print(f"Button pressed: {button}")
                        
                        # Generate PDF for this step after all files are saved
                        try:
                            pdf_path = self.logger.generate_step_pdf(iteration_count)
                            if pdf_path:
                                print(f"Generated step PDF: {pdf_path}")
                        except Exception as e:
                            print(f"Warning: Could not generate step PDF: {e}")
                        
                        # Continue to next iteration
                        continue

                    elif action == "MOUSE_LEFT_CLICK" or action == "MOUSE_RIGHT_CLICK" or action == "MOUSE_DOUBLE_CLICK":
                        # Action requires a click - perform grid selection flow
                        print("Performing grid selection flow...")
                        
                        # Use target if available, otherwise use action description
                        action_description = target if target else action
                        click_x, click_y = self.perform_grid_selection(
                            screenshot, action_description, iteration_count
                        )

                        # Execute the appropriate click type
                        if action == "MOUSE_LEFT_CLICK":
                            print(f"Executing left click at ({click_x}, {click_y})...")
                            click_at(click_x, click_y)
                            click_type = "Left click"
                        elif action == "MOUSE_RIGHT_CLICK":
                            print(f"Executing right click at ({click_x}, {click_y})...")
                            right_click_at(click_x, click_y)
                            click_type = "Right click"
                        elif action == "MOUSE_DOUBLE_CLICK":
                            print(f"Executing double click at ({click_x}, {click_y})...")
                            double_click_at(click_x, click_y)
                            click_type = "Double click"

                        # Add action to history
                        self.llm_client.add_action(action, target if target else action_description)

                        # Capture final screenshot after action
                        final_screenshot = capture_full_screen()
                        self.logger.save_final_screenshot(final_screenshot, click_x, click_y, step=iteration_count)

                        print(f"{click_type} executed at ({click_x}, {click_y})")

                        # Generate PDF for this step after all files are saved
                        try:
                            pdf_path = self.logger.generate_step_pdf(iteration_count)
                            if pdf_path:
                                print(f"Generated step PDF: {pdf_path}")
                        except Exception as e:
                            print(f"Warning: Could not generate step PDF: {e}")

                        # Continue to next iteration
                        continue

                    else:
                        # Unknown action type
                        print(f"Warning: Unknown action type '{action}'. Skipping...")
                        continue

                except ValueError as e:
                    # Handle click outside bounds or invalid coordinates
                    print(f"Error: {str(e)}")
                    continue

                except Exception as e:
                    # Handle other errors
                    print(f"Error during iteration: {str(e)}")
                    break

            # Check if we hit max iterations
            if iteration_count >= config.MAX_ITERATIONS:
                print(f"Reached maximum iterations ({config.MAX_ITERATIONS}). Stopping to prevent infinite loop.")

        except Exception as e:
            print(f"Fatal error in action loop: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            # Reset running state
            self.is_running = False
            print("\nExecution complete. Ready for next command.\n")

    def perform_grid_selection(self, screenshot, action_description, step):
        """
        Perform the three-stage 3x3 grid selection flow to determine click coordinates.

        Args:
            screenshot (PIL.Image): Full screen screenshot
            action_description (str): Description of the action to perform
            step (int): Current step number for logging

        Returns:
            tuple: (x, y) click coordinates
        """
        # Helper class for logging different stages
        class StepLogger:
            def __init__(self, logger, step, stage_num):
                self.logger = logger
                self.step = step
                self.stage_num = stage_num

            def save_prompt(self, prompt):
                if self.stage_num == 1:
                    self.logger.save_grid_prompt(prompt, self.step)
                elif self.stage_num == 2:
                    self.logger.save_refinement_prompt(prompt, self.step, stage=2)
                elif self.stage_num == 3:
                    self.logger.save_refinement_prompt(prompt, self.step, stage=3)

            def save_response(self, response):
                if self.stage_num == 1:
                    self.logger.save_grid_response(response, self.step)
                elif self.stage_num == 2:
                    self.logger.save_refinement_response(response, self.step, stage=2)
                elif self.stage_num == 3:
                    self.logger.save_refinement_response(response, self.step, stage=3)

        # Stage 1: Overlay 3x3 grid on full screen
        print("  - Stage 1: Overlaying 3x3 grid on full screen...")
        gridded_screenshot = overlay_3x3_grid(screenshot)
        self.logger.save_screenshot(gridded_screenshot, step=step, suffix="grid_stage1")

        # Get stage 1 selection from LLM
        print("  - Querying LLM for stage 1 (3x3) grid cell...")
        stage1_logger = StepLogger(self.logger, step, 1)
        stage1_selection = self.llm_client.select_grid_cell(
            gridded_screenshot, action_description, logger=stage1_logger, stage=1
        )

        x_cell1 = stage1_selection["X"]
        y_cell1 = stage1_selection["Y"]
        print(f"  - Stage 1 selected cell: {y_cell1}{x_cell1}")

        # Get cell bounds and crop for stage 1
        cell_bounds1 = get_cell_bounds(stage1_selection, screenshot.size)
        cropped_cell1 = crop_cell(screenshot, cell_bounds1)

        # Stage 2: Overlay 3x3 grid on stage 1 selected cell
        print("  - Stage 2: Overlaying 3x3 grid on stage 1 cell...")
        gridded_cell1 = overlay_3x3_grid(cropped_cell1)
        self.logger.save_screenshot(gridded_cell1, step=step, suffix="grid_stage2")

        # Get stage 2 selection from LLM
        print("  - Querying LLM for stage 2 (3x3) grid cell...")
        stage2_logger = StepLogger(self.logger, step, 2)
        stage2_selection = self.llm_client.select_grid_cell(
            gridded_cell1, action_description, logger=stage2_logger, stage=2
        )

        x_cell2 = stage2_selection["X"]
        y_cell2 = stage2_selection["Y"]
        print(f"  - Stage 2 selected cell: {y_cell2}{x_cell2}")

        # Get cell bounds and crop for stage 2 (relative to cropped_cell1)
        cell_bounds2 = get_cell_bounds(stage2_selection, cropped_cell1.size)
        cropped_cell2 = crop_cell(cropped_cell1, cell_bounds2)

        # Stage 3: Overlay 3x3 grid on stage 2 selected cell
        print("  - Stage 3: Overlaying 3x3 grid on stage 2 cell...")
        gridded_cell2 = overlay_3x3_grid(cropped_cell2)
        self.logger.save_screenshot(gridded_cell2, step=step, suffix="grid_stage3")

        # Get stage 3 selection from LLM
        print("  - Querying LLM for stage 3 (3x3) grid cell...")
        stage3_logger = StepLogger(self.logger, step, 3)
        stage3_selection = self.llm_client.select_grid_cell(
            gridded_cell2, action_description, logger=stage3_logger, stage=3
        )

        x_cell3 = stage3_selection["X"]
        y_cell3 = stage3_selection["Y"]
        print(f"  - Stage 3 selected cell: {y_cell3}{x_cell3}")

        # Calculate final click coordinates
        # Get the bounds of stage 3 cell (relative to cropped_cell2)
        cell_bounds3 = get_cell_bounds(stage3_selection, cropped_cell2.size)

        # Get center of stage 3 cell (relative to cropped_cell2)
        stage3_center = get_cell_center(cell_bounds3)

        # Convert stage 3 center to cropped_cell1 coordinates
        stage2_relative_x = cell_bounds2[0] + stage3_center[0]
        stage2_relative_y = cell_bounds2[1] + stage3_center[1]

        # Convert to absolute screen coordinates
        click_x = cell_bounds1[0] + stage2_relative_x
        click_y = cell_bounds1[1] + stage2_relative_y

        return (click_x, click_y)

    def run(self):
        """Start the desktop controller application."""
        print("=" * 60)
        print("TEXT-GUIDED DESKTOP CONTROLLER")
        print("=" * 60)
        print(f"LLM Model: {config.LLM_MODEL}")
        print(f"Max iterations per command: {config.MAX_ITERATIONS}")
        print(f"Execution logs saved to: {config.EXECUTION_LOG_DIR}/")
        print("=" * 60)
        print("\nEnter commands at the prompt. Press Ctrl+C to exit.\n")

        # Main terminal loop
        while True:
            try:
                # Get command from terminal
                command = input("Enter command: ").strip()
                
                # Skip empty commands
                if not command:
                    continue
                
                # Prevent multiple simultaneous runs
                if self.is_running:
                    print("Already running a command. Please wait...")
                    continue
                
                # Run the action loop
                self.run_action_loop(command)
                
            except KeyboardInterrupt:
                print("\n\nShutting down...")
                break
            except EOFError:
                print("\n\nShutting down...")
                break


def main():
    """Main entry point."""
    try:
        controller = DesktopController()
        controller.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
