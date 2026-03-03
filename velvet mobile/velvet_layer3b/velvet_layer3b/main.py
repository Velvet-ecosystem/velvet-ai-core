from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform
from threading import Thread

# Layer 2 imports
from velvet.paths import db_path, settings_path
from velvet.memory import VelvetMemory
from velvet.state import load_state, touch_seen
from velvet.offline import offline_fallback
from velvet import api

# Layer 3A imports
from velvet import mode_expression

# Layer 3B imports
from velvet.voice_input import get_voice_input, is_voice_available

# Configure colors
DARK_BG = (0.04, 0.04, 0.04, 1)
VELVET_PURPLE = (0.42, 0.27, 0.51, 1)
TEXT_COLOR = (0.9, 0.9, 0.9, 1)
INPUT_BG = (0.12, 0.12, 0.12, 1)


class ChatDisplay(ScrollView):
    """Scrollable chat message display"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        
        self.chat_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=10,
            padding=[10, 10, 10, 10]
        )
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.add_widget(self.chat_layout)
    
    def add_message(self, speaker, text):
        """Add a message to the chat display"""
        msg_label = Label(
            text=f"[b]{speaker}:[/b] {text}",
            markup=True,
            size_hint_y=None,
            text_size=(Window.width - 40, None),
            color=TEXT_COLOR,
            halign='left',
            valign='top'
        )
        msg_label.bind(texture_size=msg_label.setter('size'))
        self.chat_layout.add_widget(msg_label)
        
        # Auto-scroll to bottom
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)
    
    def scroll_to_bottom(self):
        """Scroll to the bottom of the chat"""
        self.scroll_y = 0


class VelvetApp(App):
    """Main Velvet application with Layer 2 integration"""
    
    def build(self):
        """Build the UI"""
        Window.clearcolor = DARK_BG
        
        # Main layout
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title (with mode indicator)
        self.title_label = Label(
            text='VELVET',
            size_hint=(1, 0.1),
            color=VELVET_PURPLE,
            font_size='24sp',
            bold=True
        )
        root.add_widget(self.title_label)
        
        # Chat display
        self.chat_display = ChatDisplay()
        root.add_widget(self.chat_display)
        
        # Input area
        input_box = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.15),
            spacing=10
        )
        
        # Mic button (Layer 3B - only show if voice available)
        self.mic_btn = None
        if is_voice_available():
            self.mic_btn = Button(
                text='🎤',
                size_hint=(0.15, 1),
                background_color=(0.3, 0.3, 0.3, 1),
                background_normal='',
                color=TEXT_COLOR,
                font_size='20sp'
            )
            self.mic_btn.bind(on_press=self.on_mic_press)
            self.mic_btn.bind(on_release=self.on_mic_release)
            input_box.add_widget(self.mic_btn)
        
        self.text_input = TextInput(
            hint_text='Type your message...',
            multiline=False,
            size_hint=(0.6 if self.mic_btn else 0.75, 1),
            background_color=INPUT_BG,
            foreground_color=TEXT_COLOR,
            cursor_color=VELVET_PURPLE,
            padding=[10, 10, 10, 10]
        )
        self.text_input.bind(on_text_validate=self.on_send)
        
        send_btn = Button(
            text='Send',
            size_hint=(0.25, 1),
            background_color=VELVET_PURPLE,
            background_normal='',
            color=TEXT_COLOR,
            bold=True
        )
        send_btn.bind(on_press=self.on_send)
        
        input_box.add_widget(self.text_input)
        input_box.add_widget(send_btn)
        root.add_widget(input_box)
        
        return root
    
    def on_start(self):
        """Initialize Layer 2 components on app start"""
        # Initialize paths using App.user_data_dir
        self.db_file = db_path(self.user_data_dir)
        self.settings_file = settings_path(self.user_data_dir)
        
        # Initialize memory and state
        self.memory = VelvetMemory(self.db_file)
        self.state = load_state(self.settings_file)
        self.state = touch_seen(self.settings_file, self.state)
        
        # Log app start
        self.memory.append("lifecycle", "system", "app_start", 
                          {"mode": self.state.mode, "device_id": self.state.device_id})
        
        # Update title with mode label (Layer 3A)
        Clock.schedule_once(self._update_mode_display, 0.1)
        
        # Show welcome message
        Clock.schedule_once(self._show_welcome, 0.1)
    
    def _update_mode_display(self, dt):
        """Update title label with current mode (Layer 3A)"""
        mode_label = mode_expression.get_mode_label(self.state.mode)
        self.title_label.text = mode_label
    
    def _show_welcome(self, dt):
        """Display welcome message on main thread"""
        welcome = mode_expression.format_ready_message(self.state.mode)
        self.chat_display.add_message("Velvet", welcome)
    
    def on_pause(self):
        """Handle app pause (Android lifecycle)"""
        if hasattr(self, 'memory'):
            self.memory.append("lifecycle", "system", "app_pause", {})
        return True
    
    def on_resume(self):
        """Handle app resume (Android lifecycle)"""
        if hasattr(self, 'memory') and hasattr(self, 'state'):
            from velvet.state import touch_seen
            self.state = touch_seen(self.settings_file, self.state)
            self.memory.append("lifecycle", "system", "app_resume", 
                              {"mode": self.state.mode})
    
    def on_send(self, instance):
        """Handle send button press"""
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        
        # Clear input
        self.text_input.text = ''
        
        # Display user message
        self.chat_display.add_message("You", user_text)
        
        # Process in background thread
        Thread(target=self._process_message, args=(user_text,), daemon=True).start()
    
    def _process_message(self, user_text):
        """Process message in background thread"""
        # Append user message to memory
        self.memory.append("chat", "user", user_text, {})
        
        # Check for mode change command (Layer 3A - optional test hook)
        if user_text.lower().startswith("/mode "):
            new_mode = user_text[6:].strip().capitalize()
            self._handle_mode_change(new_mode)
            return
        
        try:
            # Get recent context
            recent_context = self.memory.recent_chat_context(limit_pairs=6)
            
            # Call API
            response = api.chat(user_text, recent_context, self.state.mode)
            
            # Append Velvet response to memory
            self.memory.append("chat", "velvet", response, {})
            
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._show_response(response), 0)
            
        except Exception as e:
            # Handle offline/error case
            recent_context = self.memory.recent_chat_context(limit_pairs=3)
            fallback = offline_fallback(user_text, recent_context, self.state.mode)
            
            # Log the error context
            self.memory.append("error", "system", str(e), 
                              {"user_text": user_text, "fallback": True})
            
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._show_response(fallback), 0)
    
    def _handle_mode_change(self, new_mode):
        """Handle mode change command (Layer 3A test hook)"""
        from velvet.state import set_mode
        old_mode = self.state.mode
        self.state = set_mode(self.settings_file, self.state, new_mode)
        
        # Update UI on main thread
        def update_ui(dt):
            self._update_mode_display(dt)
            ack = mode_expression.format_mode_change_ack(old_mode, new_mode)
            self.chat_display.add_message("System", ack)
        
        Clock.schedule_once(update_ui, 0)
    
    def _show_response(self, response):
        """Display response on main thread"""
        self.chat_display.add_message("Velvet", response)
    
    # Layer 3B: Voice Input Handlers
    
    def on_mic_press(self, instance):
        """Handle mic button press - start listening (Layer 3B)"""
        voice = get_voice_input()
        
        if not voice.is_available:
            reason = voice.get_unavailability_reason()
            Clock.schedule_once(lambda dt: self._show_voice_error(reason), 0)
            return
        
        # Visual feedback - button active
        if self.mic_btn:
            self.mic_btn.background_color = VELVET_PURPLE
            self.mic_btn.text = '🎤 ...'
        
        # Start listening
        success = voice.start_listening(
            on_result=self._on_voice_result,
            on_error=self._on_voice_error
        )
        
        if not success:
            Clock.schedule_once(lambda dt: self._show_voice_error(
                "I can't do voice input right now, but you can type."
            ), 0)
            self._reset_mic_button()
    
    def on_mic_release(self, instance):
        """Handle mic button release - stop listening (Layer 3B)"""
        voice = get_voice_input()
        voice.stop_listening()
        
        # Check for result (Android STT completes on stop)
        Clock.schedule_once(lambda dt: self._check_voice_result(), 0.5)
    
    def _check_voice_result(self):
        """Check for voice transcription result (Layer 3B)"""
        voice = get_voice_input()
        result = voice.get_last_result()
        
        if result:
            self._on_voice_result(result)
        else:
            self._reset_mic_button()
    
    def _on_voice_result(self, text):
        """Handle voice transcription result (Layer 3B)"""
        self._reset_mic_button()
        
        if text and text.strip():
            # Feed into text input (user can edit before sending)
            self.text_input.text = text.strip()
            self.text_input.focus = True
    
    def _on_voice_error(self, error_msg):
        """Handle voice input error (Layer 3B)"""
        self._reset_mic_button()
        Clock.schedule_once(lambda dt: self._show_voice_error(error_msg), 0)
    
    def _show_voice_error(self, msg):
        """Display voice error to user (Layer 3B)"""
        self.chat_display.add_message("System", msg)
    
    def _reset_mic_button(self):
        """Reset mic button to inactive state (Layer 3B)"""
        if self.mic_btn:
            self.mic_btn.background_color = (0.3, 0.3, 0.3, 1)
            self.mic_btn.text = '🎤'


if __name__ == '__main__':
    VelvetApp().run()
