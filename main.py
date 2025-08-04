import sys
import tkinter as tk
from config import setup_logging
from cli_interface import PDFCompressorCLI
from gui_interface import PDFCompressorGUI

def main():
    """Main function - determines whether to run GUI or CLI mode"""
    # Setup logging
    logger = setup_logging()
    
    try:
        if len(sys.argv) > 1:
            # CLI mode
            cli = PDFCompressorCLI()
            cli.run(sys.argv)
        else:
            # GUI mode
            try:
                print("🔧 Starting Enhanced PDF B&W Compressor...")
                print("📝 Log file: pdf_compressor.log")
                print("🖥️  GUI Mode - Opening interface...")
                
                root = tk.Tk()
                app = PDFCompressorGUI(root)
                root.mainloop()
                
            except Exception as e:
                print(f"❌ Failed to start GUI: {e}")
                print("📝 Try running in CLI mode: python main.py <path> [quality]")
                logger.error(f"GUI startup failed: {e}")
                
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        logger.info("Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}")

if __name__ == "__main__":
    main()