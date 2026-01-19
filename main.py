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
    overlay_10x10_grid, overlay_2x2_grid,
    get_cell_bounds, get_cell_center, crop_cell
)
from modules.action_executor import click_at
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
                    print(f"Action determined: {action}" + (f" - {target}" if target else ""))

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

                    else:
                        # Action requires a click - perform grid selection flow
                        print("Performing grid selection flow...")
                        
                        # Use target if available, otherwise use action description
                        action_description = target if target else action
                        click_x, click_y = self.perform_grid_selection(
                            screenshot, action_description, iteration_count
                        )

                        # Execute the click
                        print(f"Executing click at ({click_x}, {click_y})...")
                        click_at(click_x, click_y)

                        # Add action to history
                        self.llm_client.add_action(action, target if target else action_description)

                        # Capture final screenshot after action
                        final_screenshot = capture_full_screen()
                        self.logger.save_final_screenshot(final_screenshot, click_x, click_y, step=iteration_count)

                        print(f"Click executed at ({click_x}, {click_y})")

                        # Generate PDF for this step after all files are saved
                        try:
                            pdf_path = self.logger.generate_step_pdf(iteration_count)
                            if pdf_path:
                                print(f"Generated step PDF: {pdf_path}")
                        except Exception as e:
                            print(f"Warning: Could not generate step PDF: {e}")

                        # Continue to next iteration
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
        Perform the grid selection flow to determine click coordinates.

        Args:
            screenshot (PIL.Image): Full screen screenshot
            action_description (str): Description of the action to perform
            step (int): Current step number for logging

        Returns:
            tuple: (x, y) click coordinates
        """
        # Step 1: Overlay 10x10 grid
        print("  - Overlaying 10x10 grid...")
        gridded_screenshot = overlay_10x10_grid(screenshot)
        self.logger.save_screenshot(gridded_screenshot, step=step, suffix="grid")

        # Step 2: Get grid cell selection from LLM
        print("  - Querying LLM for 10x10 grid cell...")

        class StepLogger:
            def __init__(self, logger, step, suffix="grid"):
                self.logger = logger
                self.step = step
                self.suffix = suffix

            def save_prompt(self, prompt):
                if self.suffix == "grid":
                    self.logger.save_grid_prompt(prompt, self.step)
                elif self.suffix == "refinement":
                    self.logger.save_refinement_prompt(prompt, self.step)

            def save_response(self, response):
                if self.suffix == "grid":
                    self.logger.save_grid_response(response, self.step)
                elif self.suffix == "refinement":
                    self.logger.save_refinement_response(response, self.step)

        grid_logger = StepLogger(self.logger, step, "grid")
        grid_selection = self.llm_client.select_grid_cell(
            gridded_screenshot, action_description, logger=grid_logger
        )

        x_cell = grid_selection["X"]
        y_cell = grid_selection["Y"]
        print(f"  - Selected cell: {y_cell}{x_cell}")

        # Step 3: Get cell bounds and crop
        cell_bounds = get_cell_bounds(grid_selection, screenshot.size)
        cropped_cell = crop_cell(screenshot, cell_bounds)

        # Step 4: Overlay 2x2 grid on cropped cell
        print("  - Overlaying 2x2 refinement grid...")
        cropped_2x2 = overlay_2x2_grid(cropped_cell)
        self.logger.save_screenshot(cropped_2x2, step=step, suffix="crop_2x2")

        # Step 5: Get 2x2 refinement selection from LLM
        print("  - Querying LLM for 2x2 refinement...")

        refinement_logger = StepLogger(self.logger, step, "refinement")
        refinement_selection = self.llm_client.refine_selection(
            screenshot, cropped_2x2, action_description, logger=refinement_logger
        )

        ref_x = refinement_selection["X"]
        ref_y = refinement_selection["Y"]
        print(f"  - Refinement cell: {ref_y}{ref_x}")

        # Step 6: Calculate final click coordinates
        # Get the bounds of the refinement cell within the cropped cell
        refinement_bounds = get_cell_bounds(
            refinement_selection,
            cropped_cell.size,
            grid_cols=config.REFINEMENT_COLS,
            grid_rows=config.REFINEMENT_ROWS
        )

        # Get center of refinement cell (relative to cropped cell)
        ref_center = get_cell_center(refinement_bounds)

        # Convert to absolute screen coordinates
        click_x = cell_bounds[0] + ref_center[0]
        click_y = cell_bounds[1] + ref_center[1]

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
