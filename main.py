import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Robot Operating System - نظام تشغيل الروبوت الطبي الذكي"
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


def print_banner():
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🤖 AI ROBOT OPERATING SYSTEM                            ║
║        نظام تشغيل الروبوت الطبي الذكي                        ║
║                                                              ║
║     Version: 1.0.0                                           ║
║     Medical Robot for Patient Care                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    print("🔍 Checking dependencies...")
    
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
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name}")
            missing.append(package_name)
    
    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print("   Install with: pip install " + " ".join(missing))
        return False
    
    print("✅ All dependencies satisfied\n")
    return True


def main():
    print_banner()
    
    args = parse_args()
    
    if not check_dependencies():
        print("❌ Please install missing dependencies and try again.")
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
    
    config.print_config()
    
    if not config.validate():
        print("\n❌ Configuration validation failed!")
        print("   Please check your .env file and ensure all required values are set.")
        sys.exit(1)
    
    print("\n🚀 Starting AI Robot OS...")
    print("   Press ESC or F11 to toggle fullscreen")
    print("   Close window to exit\n")
    
    try:
        from gui.main_window import run_app
        run_app()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! تم إيقاف النظام")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
