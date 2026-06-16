import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append('d:/1/Ahmed/projects/mariam_pro/AI')
from modules.chatbot import chatbot
from modules.voice_command_processor import voice_command_processor

def test_chatbot():
    print("=== Testing Chatbot System Prompt ===")
    prompt = chatbot._get_system_prompt()
    print("System Prompt Contains general conversation instruction:")
    contains_gen = "general conversation" in prompt.lower() or "any topic" in prompt.lower()
    print(f"Result: {contains_gen}")
    assert contains_gen, "General conversation instructions not found in prompt!"

def test_command_processor():
    print("\n=== Testing Voice Command Processor ===")
    # Test Whisper hallucinations are filtered
    hallucinations = ["شكرا لك", "شكراً لك.", "بسم الله الرحمن الرحيم", "وبسم الله الرحمن الرحيم", "شكرا جزيلا لك"]
    for h in hallucinations:
        res = voice_command_processor.process_command(h)
        print(f"Hallucination '{h}' filtered: {res is None}")
        assert res is None, f"Hallucination '{h}' was not filtered!"

    # Test short valid words are NOT filtered
    valid_shorts = ["لا", "لأ", "تمام", "خروج", "سكر"]
    
    # We will register callbacks for both general_chat and command execution
    # to see which one gets called.
    general_reached = False
    exit_reached = False
    
    def dummy_chat_callback(t):
        nonlocal general_reached
        general_reached = True
        return "reached"
        
    def dummy_exit_callback():
        nonlocal exit_reached
        exit_reached = True
        return "exit_reached"
        
    voice_command_processor.set_callback("general_chat", dummy_chat_callback)
    voice_command_processor.set_callback("exit_app", dummy_exit_callback)
    
    for vs in valid_shorts:
        general_reached = False
        exit_reached = False
        
        voice_command_processor.process_command(vs)
        reached = general_reached or exit_reached
        print(f"Valid short command '{vs}' processed successfully (general_chat={general_reached}, exit_app={exit_reached}): {reached}")
        assert reached, f"Valid short command '{vs}' was filtered out or did not trigger any callback!"

if __name__ == "__main__":
    try:
        test_chatbot()
        test_command_processor()
        print("\nAll tests passed successfully!")
    except AssertionError as e:
        print("\nTEST FAILED:", e)
