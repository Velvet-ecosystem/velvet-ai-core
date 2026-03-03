#!/usr/bin/env python3
"""
Custom Module Example

Shows how to create a simple module that responds to events.
"""

from velvet.core.velvet_module import VelvetModule
from velvet.core import VelvetRuntime

class HelloModule(VelvetModule):
    """
    A simple module that logs startup and shutdown.
    """
    
    def __init__(self):
        super().__init__(name="hello_module")
        self.counter = 0
    
    def start(self):
        """Called when module starts"""
        self.log("Hello from custom module!")
        self.counter = 0
    
    def stop(self):
        """Called when module stops"""
        self.log(f"Goodbye! Ran {self.counter} times.")

def main():
    # Note: This is a simplified example
    # In practice, modules would be registered with ModuleLoader
    # and started by the runtime
    
    module = HelloModule()
    module.start()
    
    # Simulate some work
    module.counter += 1
    module.log("Module is running...")
    
    module.stop()

if __name__ == "__main__":
    main()
