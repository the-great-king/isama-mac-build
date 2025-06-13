class WindowManager:
    """
    Manages window instances to allow communication between windows.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WindowManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the window manager."""
        self.windows = {}
    
    def register_window(self, window_name: str, window_instance):
        """Register a window instance."""
        self.windows[window_name] = window_instance
    
    def get_window(self, window_name: str):
        """Get a window instance by name."""
        return self.windows.get(window_name)
    
    def remove_window(self, window_name: str):
        """Remove a window instance when it's closed."""
        if window_name in self.windows:
            del self.windows[window_name] 