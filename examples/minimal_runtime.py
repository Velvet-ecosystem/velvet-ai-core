#!/usr/bin/env python3
"""
Minimal Velvet Runtime Example

Demonstrates basic runtime initialization and lifecycle.
"""

from velvet.core import VelvetRuntime

def main():
    print("Starting Velvet Core Runtime...")
    
    # Create runtime instance
    runtime = VelvetRuntime()
    
    # Start all core modules
    runtime.start()
    
    print("Runtime started. Press Ctrl+C to stop.")
    
    try:
        # Run forever (until SIGTERM or SIGINT)
        runtime.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        runtime.stop()
        print("Runtime stopped.")

if __name__ == "__main__":
    main()
