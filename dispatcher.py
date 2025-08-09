import json
import os
import subprocess
import importlib.util
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExecutionEnvironment(Enum):
    PYTHON = "python"
    AUTOHOTKEY = "ahk"
    JAVA = "java"
    NODEJS = "nodejs"
    SYSTEM = "system"

class AssistantMode(Enum):
    GENERAL = "general"
    CODING = "coding"
    STUDY = "study"
    STREAMING = "streaming"

class CommandCategory(Enum):
    UTILITY = "utility"
    AUDIO = "audio"
    CODING = "coding"
    PRODUCTIVITY = "productivity"
    KNOWLEDGE = "knowledge"
    SYSTEM = "system"

@dataclass
class CommandResult:
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class Command:
    key: str
    name: str
    description: str
    keywords: List[str]
    category: CommandCategory
    environment: ExecutionEnvironment
    script_path: str
    args: List[str] = None
    modes: List[AssistantMode] = None
    requires_confirmation: bool = False
    ai_parsing: bool = False
    metadata: Dict[str, Any] = None

class StateManager:
    def __init__(self, state_file: str = "state/assistant_state.json"):
        self.state_file = state_file
        self.state = self._load_state()
        
    def _load_state(self) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "current_mode": AssistantMode.GENERAL.value,
                "last_commands": [],
                "user_preferences": {},
                "aliases": {},
                "session_start": datetime.now().isoformat()
            }
    
    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get(self, key: str, default=None):
        return self.state.get(key, default)
    
    def set(self, key: str, value: Any):
        self.state[key] = value
        self.save_state()
    
    def add_to_history(self, command_key: str, input_text: str, result: CommandResult):
        history = self.state.get("last_commands", [])
        history.append({
            "timestamp": datetime.now().isoformat(),
            "command": command_key,
            "input": input_text,
            "success": result.success,
            "output": result.output[:200] if result.output else None  # Truncate for storage
        })
        # Keep only last 50 commands
        self.state["last_commands"] = history[-50:]
        self.save_state()

class CommandRegistry:
    def __init__(self, registry_file: str = "config/commands.yaml"):
        self.registry_file = registry_file
        self.commands: Dict[str, Command] = {}
        self._load_commands()
    
    def _load_commands(self):
        try:
            with open(self.registry_file, 'r') as f:
                data = yaml.safe_load(f)
                for cmd_data in data.get('commands', []):
                    cmd = Command(
                        key=cmd_data['key'],
                        name=cmd_data['name'],
                        description=cmd_data['description'],
                        keywords=cmd_data['keywords'],
                        category=CommandCategory(cmd_data['category']),
                        environment=ExecutionEnvironment(cmd_data['environment']),
                        script_path=cmd_data['script_path'],
                        args=cmd_data.get('args', []),
                        modes=[AssistantMode(m) for m in cmd_data.get('modes', [])],
                        requires_confirmation=cmd_data.get('requires_confirmation', False),
                        ai_parsing=cmd_data.get('ai_parsing', False),
                        metadata=cmd_data.get('metadata', {})
                    )
                    self.commands[cmd.key] = cmd
        except FileNotFoundError:
            logger.warning(f"Command registry file {self.registry_file} not found. Creating default.")
            self._create_default_registry()
    
    def _create_default_registry(self):
        # Create a basic registry structure
        default_commands = {
            'commands': [
                {
                    'key': 'voicemeeter_control',
                    'name': 'Voicemeeter Audio Control',
                    'description': 'Control Voicemeeter audio routing and levels',
                    'keywords': ['patch', 'mute', 'unmute', 'volume', 'audio', 'strip', 'bus'],
                    'category': 'audio',
                    'environment': 'python',
                    'script_path': 'scripts/audio/voicemeeter_control.py',
                    'ai_parsing': True,
                    'modes': ['general', 'streaming']
                },
                {
                    'key': 'app_launcher',
                    'name': 'Application Launcher',
                    'description': 'Launch or close applications',
                    'keywords': ['open', 'launch', 'start', 'close', 'kill', 'app'],
                    'category': 'utility',
                    'environment': 'python',
                    'script_path': 'scripts/utility/app_launcher.py',
                    'modes': ['general', 'coding', 'study']
                }
            ]
        }
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        with open(self.registry_file, 'w') as f:
            yaml.dump(default_commands, f, default_flow_style=False)
        self._load_commands()
    
    def find_matches(self, user_input: str, current_mode: AssistantMode) -> List[Tuple[Command, float]]:
        """Find matching commands with confidence scores"""
        user_input_lower = user_input.lower()
        matches = []
        
        for cmd in self.commands.values():
            # Skip if command doesn't support current mode
            if cmd.modes and current_mode not in cmd.modes:
                continue
                
            score = 0.0
            for keyword in cmd.keywords:
                if keyword.lower() in user_input_lower:
                    # Higher score for exact matches, partial score for partial matches
                    if keyword.lower() == user_input_lower:
                        score += 1.0
                    elif user_input_lower.startswith(keyword.lower()):
                        score += 0.8
                    else:
                        score += 0.5
            
            if score > 0:
                matches.append((cmd, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

class ExecutionEngine:
    def __init__(self):
        self.python_path = self._find_python_executable()
        self.ahk_path = self._find_ahk_executable()
        self.java_path = self._find_java_executable()
        self.node_path = self._find_node_executable()
    
    def _find_python_executable(self) -> str:
        # Try to find Python executable
        for path in ["python", "python3", "py"]:
            try:
                subprocess.run([path, "--version"], capture_output=True, check=True)
                return path
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        return "python"  # Fallback
    
    def _find_ahk_executable(self) -> str:
        # Common AutoHotkey paths
        common_paths = [
            r"C:\Program Files\AutoHotkey\AutoHotkey.exe",
            r"C:\Program Files (x86)\AutoHotkey\AutoHotkey.exe",
            "autohotkey.exe",
            "ahk.exe"
        ]
        for path in common_paths:
            if os.path.exists(path) or self._command_exists(path):
                return path
        return "autohotkey.exe"  # Fallback
    
    def _find_java_executable(self) -> str:
        return "java"  # Assume java is in PATH
    
    def _find_node_executable(self) -> str:
        return "node"  # Assume node is in PATH
    
    def _command_exists(self, command: str) -> bool:
        try:
            subprocess.run([command], capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def execute_command(self, command: Command, parsed_args: Dict[str, Any] = None) -> CommandResult:
        start_time = datetime.now()
        
        try:
            if command.environment == ExecutionEnvironment.PYTHON:
                result = await self._execute_python(command, parsed_args)
            elif command.environment == ExecutionEnvironment.AUTOHOTKEY:
                result = await self._execute_ahk(command, parsed_args)
            elif command.environment == ExecutionEnvironment.JAVA:
                result = await self._execute_java(command, parsed_args)
            elif command.environment == ExecutionEnvironment.NODEJS:
                result = await self._execute_nodejs(command, parsed_args)
            elif command.environment == ExecutionEnvironment.SYSTEM:
                result = await self._execute_system(command, parsed_args)
            else:
                result = CommandResult(False, "", f"Unsupported execution environment: {command.environment}")
        
        except Exception as e:
            logger.error(f"Error executing command {command.key}: {e}")
            result = CommandResult(False, "", str(e))
        
        execution_time = (datetime.now() - start_time).total_seconds()
        result.execution_time = execution_time
        
        return result
    
    async def _execute_python(self, command: Command, parsed_args: Dict[str, Any] = None) -> CommandResult:
        args = [self.python_path, command.script_path]
        
        # Add command line arguments
        if command.args:
            args.extend(command.args)
        
        # If we have parsed arguments, pass them as JSON
        if parsed_args:
            args.extend(["--parsed-args", json.dumps(parsed_args)])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return CommandResult(True, stdout.decode().strip())
            else:
                return CommandResult(False, stdout.decode().strip(), stderr.decode().strip())
        
        except Exception as e:
            return CommandResult(False, "", str(e))
    
    async def _execute_ahk(self, command: Command, parsed_args: Dict[str, Any] = None) -> CommandResult:
        # For AHK scripts, we might need to create a temporary script with parameters
        args = [self.ahk_path, command.script_path]
        
        if command.args:
            args.extend(command.args)
            
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return CommandResult(True, stdout.decode().strip())
            else:
                return CommandResult(False, stdout.decode().strip(), stderr.decode().strip())
        
        except Exception as e:
            return CommandResult(False, "", str(e))
    
    async def _execute_java(self, command: Command, parsed_args: Dict[str, Any] = None) -> CommandResult:
        # Assume the script_path is a compiled Java class or jar
        if command.script_path.endswith('.jar'):
            args = [self.java_path, '-jar', command.script_path]
        else:
            args = [self.java_path, command.script_path]
            
        if command.args:
            args.extend(command.args)
            
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return CommandResult(True, stdout.decode().strip())
            else:
                return CommandResult(False, stdout.decode().strip(), stderr.decode().strip())
        
        except Exception as e:
            return CommandResult(False, "", str(e))
    
    async def _execute_nodejs(self, command: Command, parsed_args: Dict[str, Any] = None) -> CommandResult:
        args = [self.node_path, command.script_path]
        
        if command.args:
            args.extend(command.args)
            
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return CommandResult(True, stdout.decode().strip())
            else:
                return CommandResult(False, stdout.decode().strip(), stderr.decode().strip())
        
        except Exception as e:
            return CommandResult(False, "", str(e))
    
    async def _execute_system(self, command: Command, parsed_args: Dict[str, Any] = None) -> CommandResult:
        # Direct system command execution
        try:
            args = command.script_path.split() + (command.args or [])
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return CommandResult(True, stdout.decode().strip())
            else:
                return CommandResult(False, stdout.decode().strip(), stderr.decode().strip())
        
        except Exception as e:
            return CommandResult(False, "", str(e))

class AIParser:
    """Interface for AI-powered command parsing"""
    
    def __init__(self):
        # This would integrate with Claude/GPT-4 APIs
        # For now, this is a placeholder for the AI integration
        pass
    
    async def parse_command(self, user_input: str, command: Command) -> Dict[str, Any]:
        """Parse natural language command into structured parameters"""
        # This would call Claude or GPT-4 to parse complex commands
        # For now, return a basic parse
        return {"raw_input": user_input, "command_key": command.key}
    
    async def clarify_command(self, user_input: str, possible_commands: List[Command]) -> str:
        """Generate clarification question for ambiguous commands"""
        if len(possible_commands) > 1:
            cmd_names = [cmd.name for cmd in possible_commands]
            return f"I found multiple possible commands: {', '.join(cmd_names)}. Which one did you mean?"
        return "I'm not sure what you mean. Could you be more specific?"

class VoiceAssistantDispatcher:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.state_manager = StateManager()
        self.command_registry = CommandRegistry(os.path.join(config_dir, "commands.yaml"))
        self.execution_engine = ExecutionEngine()
        self.ai_parser = AIParser()
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("scripts", exist_ok=True)
    
    @property
    def current_mode(self) -> AssistantMode:
        return AssistantMode(self.state_manager.get("current_mode", AssistantMode.GENERAL.value))
    
    def set_mode(self, mode: AssistantMode):
        self.state_manager.set("current_mode", mode.value)
        logger.info(f"Switched to {mode.value} mode")
    
    async def dispatch(self, user_input: str) -> CommandResult:
        """Main dispatch method for processing voice commands"""
        logger.info(f"Processing command: '{user_input}' in {self.current_mode.value} mode")
        
        # Find matching commands
        matches = self.command_registry.find_matches(user_input, self.current_mode)
        
        if not matches:
            return CommandResult(False, "No matching commands found", 
                               "Try saying 'help' or be more specific about what you want to do.")
        
        # If multiple matches with similar scores, ask for clarification
        if len(matches) > 1 and abs(matches[0][1] - matches[1][1]) < 0.3:
            clarification = await self.ai_parser.clarify_command(user_input, [m[0] for m in matches[:3]])
            return CommandResult(False, clarification, "Command needs clarification")
        
        # Use the best match
        command, confidence = matches[0]
        logger.info(f"Selected command: {command.key} (confidence: {confidence:.2f})")
        
        # Parse command if AI parsing is enabled
        parsed_args = None
        if command.ai_parsing:
            parsed_args = await self.ai_parser.parse_command(user_input, command)
        
        # Request confirmation if required
        if command.requires_confirmation:
            # In a real implementation, this would trigger a voice confirmation dialog
            logger.info(f"Command {command.key} requires confirmation")
            # For now, we'll proceed, but this is where you'd implement confirmation logic
        
        # Execute the command
        result = await self.execution_engine.execute_command(command, parsed_args)
        
        # Log the command execution
        self.state_manager.add_to_history(command.key, user_input, result)
        
        # Log execution details
        if result.success:
            logger.info(f"Command {command.key} executed successfully in {result.execution_time:.2f}s")
        else:
            logger.error(f"Command {command.key} failed: {result.error}")
        
        return result
    
    def get_available_commands(self, mode: AssistantMode = None) -> List[Command]:
        """Get list of available commands for current or specified mode"""
        if mode is None:
            mode = self.current_mode
            
        return [cmd for cmd in self.command_registry.commands.values() 
                if not cmd.modes or mode in cmd.modes]
    
    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent command history"""
        return self.state_manager.get("last_commands", [])[-limit:]
    
    def add_alias(self, alias: str, command_key: str):
        """Add a command alias"""
        aliases = self.state_manager.get("aliases", {})
        aliases[alias] = command_key
        self.state_manager.set("aliases", aliases)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        history = self.state_manager.get("last_commands", [])
        total_commands = len(history)
        successful_commands = sum(1 for cmd in history if cmd.get("success", False))
        
        return {
            "total_commands": total_commands,
            "successful_commands": successful_commands,
            "success_rate": successful_commands / total_commands if total_commands > 0 else 0,
            "current_mode": self.current_mode.value,
            "session_start": self.state_manager.get("session_start")
        }

# Example usage and testing
async def main():
    dispatcher = VoiceAssistantDispatcher()
    
    # Example commands
    test_commands = [
        "mute strip 1",
        "open notepad", 
        "patch strip 2 to A1",
        "switch to coding mode",
        "help"
    ]
    
    for cmd in test_commands:
        print(f"\n> {cmd}")
        result = await dispatcher.dispatch(cmd)
        print(f"Success: {result.success}")
        print(f"Output: {result.output}")
        if result.error:
            print(f"Error: {result.error}")
    
    # Print stats
    stats = dispatcher.get_stats()
    print(f"\nSession Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())