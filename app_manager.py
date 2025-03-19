import customtkinter as ctk
from ui import FaultDetectionApp
from login import GenesisAuth

class AppManager:
    @staticmethod
    def launch_main_app(username):
        """Launch the main application"""
        return FaultDetectionApp(username)
    
    @staticmethod
    def launch_login():
        """Launch the login screen"""
        return GenesisAuth() 