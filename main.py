import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Robot Operating System - Medical Robot"
    )
    
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="Run in fullscreen mode"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--no-arduino",
        action="store_true",
        help="Skip Arduino connection (use simulation mode)"
    )
    
    parser.add_argument(
        "--width",
        type=int,
        default=None,
        help="Window width"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="Window height"
    )
    
    return parser.parse_args()


def check_dependencies():
    required = [
        ("customtkinter", "customtkinter"),
        ("PIL", "pillow"),
        ("google.generativeai", "google-generativeai"),
        ("pygame", "pygame"),
        ("serial", "pyserial"),
        ("requests", "requests"),
        ("cv2", "opencv-python"),
        ("dotenv", "python-dotenv"),
    ]
    
    missing = []
    
    for module_name, package_name in required:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        return False
    
    return True


def main():
    args = parse_args()
    
    if not check_dependencies():
        sys.exit(1)
    
    from config import config
    
    if args.fullscreen:
        config.APP_FULLSCREEN = True
    
    if args.debug:
        config.DEBUG_MODE = True
    
    if args.width:
        config.SCREEN_WIDTH = args.width
    
    if args.height:
        config.SCREEN_HEIGHT = args.height
    
    if not config.validate():
        sys.exit(1)
    
    try:
        from gui.main_window import run_app
        run_app()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
