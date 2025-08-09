#!/usr/bin/env python3
"""
Voice Assistant Main Entry Point
This is the main file that ties together voice input, the dispatcher, and voice output.
Place this file at: main.py (root level)
"""

import asyncio
import logging
from dispatcher import VoiceAssistantDispatcher, AssistantMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/assistant.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class VoiceAssistant:
    def __init__(self):
        self.dispatcher = VoiceAssistantDispatcher()
        self.running = False
        
    async def initialize(self):
        """Initialize the voice assistant"""
        logger.info("Initializing Voice Assistant...")
        
        # TODO: Initialize voice input (Whisper)
        # TODO: Initialize text-to-speech
        # TODO: Initialize any other required services
        
        logger.info(f"Assistant ready in {self.dispatcher.current_mode.value} mode")
        self.running = True
    
    async def process_voice_input(self, audio_data):
        """
        Process voice input through the pipeline:
        Audio → Whisper → Dispatcher → TTS Response
        """
        try:
            # TODO: Transcribe audio using Whisper
            # For now, we'll simulate this step
            transcribed_text = await self.transcribe_audio(audio_data)
            
            if not transcribed_text:
                return await self.speak("I didn't catch that. Could you repeat?")
            
            logger.info(f"Transcribed: '{transcribed_text}'")
            
            # Process through dispatcher
            result = await self.dispatcher.dispatch(transcribed_text)
            
            # Generate response
            if result.success:
                response = f"Done. {result.output}" if result.output else "Done."
            else:
                response = result.output or "Sorry, I couldn't complete that command."
                if result.error:
                    logger.error(f"Command error: {result.error}")
            
            # Speak the response
            await self.speak(response)
            
        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            await self.speak("Sorry, something went wrong.")
    
    async def transcribe_audio(self, audio_data):
        """
        Transcribe audio using Whisper
        TODO: Implement actual Whisper integration
        """
        # Placeholder - replace with actual Whisper implementation
        # This could be local Whisper or OpenAI API
        pass
    
    async def speak(self, text: str):
        """
        Convert text to speech and play
        TODO: Implement TTS
        """
        print(f"🔊 Assistant: {text}")
        # TODO: Implement actual TTS (Windows SAPI, Azure Speech, etc.)
    
    async def listen_for_wake_word(self):
        """
        Listen for wake word activation
        TODO: Implement wake word detection
        """
        # TODO: Implement wake word detection
        pass
    
    async def continuous_listening_mode(self):
        """
        Continuous listening mode for voice commands
        """
        print("Voice Assistant is listening... (Press Ctrl+C to stop)")
        
        try:
            while self.running:
                # TODO: Implement actual audio capture and voice activity detection
                # For testing, we'll use text input
                user_input = input("\n🎤 Say something (or 'quit' to exit): ")
                
                if user_input.lower() in ['quit', 'exit', 'stop']:
                    break
                
                if user_input.strip():
                    # Simulate audio processing
                    await self.process_text_input(user_input)
                
        except KeyboardInterrupt:
            logger.info("Stopping voice assistant...")
        finally:
            self.running = False
    
    async def process_text_input(self, text: str):
        """
        Process text input (for testing without voice)
        """
        try:
            logger.info(f"Processing: '{text}'")
            
            # Special commands
            if text.lower().startswith("switch to ") and "mode" in text.lower():
                await self.handle_mode_switch(text)
                return
            
            if text.lower() in ["help", "what can you do"]:
                await self.show_help()
                return
            
            if text.lower() == "status":
                await self.show_status()
                return
            
            # Process through dispatcher
            result = await self.dispatcher.dispatch(text)
            
            # Generate response
            if result.success:
                response = f"✅ {result.output}" if result.output else "✅ Done."
            else:
                response = f"❌ {result.output or 'Command failed.'}"
                if result.error:
                    print(f"   Error details: {result.error}")
            
            print(f"🔊 {response}")
            
        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            print(f"❌ Sorry, something went wrong: {e}")
    
    async def handle_mode_switch(self, text: str):
        """Handle mode switching commands"""
        text_lower = text.lower()
        
        if "coding" in text_lower:
            self.dispatcher.set_mode(AssistantMode.CODING)
            print("🔊 Switched to coding mode")
        elif "study" in text_lower:
            self.dispatcher.set_mode(AssistantMode.STUDY)
            print("🔊 Switched to study mode")
        elif "streaming" in text_lower:
            self.dispatcher.set_mode(AssistantMode.STREAMING)
            print("🔊 Switched to streaming mode")
        elif "general" in text_lower:
            self.dispatcher.set_mode(AssistantMode.GENERAL)
            print("🔊 Switched to general mode")
        else:
            print("🔊 Available modes: coding, study, streaming, general")
    
    async def show_help(self):
        """Show available commands"""
        commands = self.dispatcher.get_available_commands()
        
        print("\n📋 Available Commands:")
        print("=" * 50)
        
        # Group by category
        by_category = {}
        for cmd in commands:
            category = cmd.category.value
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(cmd)
        
        for category, cmd_list in by_category.items():
            print(f"\n{category.upper()}:")
            for cmd in cmd_list:
                keywords = ", ".join(cmd.keywords[:3])  # Show first 3 keywords
                print(f"  • {cmd.name}: {keywords}")
        
        print(f"\nCurrent mode: {self.dispatcher.current_mode.value}")
        print("Say 'switch to [mode] mode' to change modes")
    
    async def show_status(self):
        """Show system status"""
        stats = self.dispatcher.get_stats()
        
        print("\n📊 Assistant Status:")
        print("=" * 30)
        print(f"Current Mode: {stats['current_mode']}")
        print(f"Commands Executed: {stats['total_commands']}")
        print(f"Success Rate: {stats['success_rate']:.1%}")
        print(f"Session Start: {stats['session_start']}")
        
        # Show recent commands
        history = self.dispatcher.get_command_history(5)
        if history:
            print("\nRecent Commands:")
            for cmd in history[-3:]:  # Last 3
                status = "✅" if cmd.get('success') else "❌"
                print(f"  {status} {cmd['command']}")

async def main():
    """Main entry point"""
    assistant = VoiceAssistant()
    
    try:
        await assistant.initialize()
        await assistant.continuous_listening_mode()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        print("Voice Assistant stopped.")

if __name__ == "__main__":
    # Create required directories
    import os
    os.makedirs("logs", exist_ok=True)
    os.makedirs("state", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    os.makedirs("scripts/audio", exist_ok=True)
    
    # Run the assistant
    asyncio.run(main())