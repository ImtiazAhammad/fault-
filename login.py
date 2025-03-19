import customtkinter as ctk
import sqlite3
import hashlib
from tkinter import messagebox
from ui import FaultDetectionApp

class GenesisAuth:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("GENESIS - Industrial Fault Detection System")
        self.window.geometry("1200x800")
        
        # Initialize database
        self.init_database()
        
        # Create main container
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True)
        
        # Create landing page
        self.create_landing_page()
        
        self.window.mainloop()
    
    def init_database(self):
        """Initialize SQLite database for user authentication"""
        conn = sqlite3.connect('genesis.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (username TEXT PRIMARY KEY,
                     password TEXT,
                     email TEXT,
                     created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
    
    def create_landing_page(self):
        """Create the landing page with login/register options"""
        # Clear main container
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Create two frames: left for branding, right for auth
        left_frame = ctk.CTkFrame(self.main_container, fg_color="#1E1E1E")
        left_frame.pack(side="left", fill="both", expand=True)
        
        right_frame = ctk.CTkFrame(self.main_container, fg_color="#2B2B2B")
        right_frame.pack(side="right", fill="both", expand=True)
        
        # Branding content
        logo_label = ctk.CTkLabel(left_frame, 
                                text="GENESIS",
                                font=("Orbitron", 48, "bold"),
                                text_color="#00FF00")
        logo_label.pack(pady=(100, 20))
        
        subtitle = ctk.CTkLabel(left_frame,
                              text="GENESIS||Industrial Fault Detection System",
                              font=("Exo 2", 24),
                              text_color="#AAAAAA")
        subtitle.pack(pady=(0, 50))
        
        features_text = """
        • Real-time Fault Detection
        • Advanced Parameter Monitoring
        • Trend Analysis & Statistics
        • Intelligent Alert System
        • Industrial Grade Security
        """
        features = ctk.CTkLabel(left_frame,
                              text=features_text,
                              font=("Exo 2", 16),
                              text_color="#FFFFFF",
                              justify="left")
        features.pack(pady=20)
        
        # Auth content
        auth_container = ctk.CTkFrame(right_frame, fg_color="#232323")
        auth_container.pack(pady=100, padx=50)
        
        # Login/Register toggle buttons
        toggle_frame = ctk.CTkFrame(auth_container, fg_color="#232323")
        toggle_frame.pack(fill="x", padx=20, pady=20)
        
        login_btn = ctk.CTkButton(toggle_frame,
                                text="Login",
                                font=("Orbitron", 14),
                                command=self.show_login_form)
        login_btn.pack(side="left", expand=True, padx=5)
        
        register_btn = ctk.CTkButton(toggle_frame,
                                   text="Register",
                                   font=("Orbitron", 14),
                                   fg_color="#555555",
                                   command=self.show_register_form)
        register_btn.pack(side="right", expand=True, padx=5)
        
        # Show login form by default
        self.show_login_form()
    
    def show_login_form(self):
        """Display the login form"""
        # Create form container
        self.auth_frame = ctk.CTkFrame(self.main_container, fg_color="#232323")
        self.auth_frame.place(relx=0.75, rely=0.5, anchor="center")
        
        # Login form
        title = ctk.CTkLabel(self.auth_frame,
                           text="Login to GENESIS",
                           font=("Orbitron", 24, "bold"),
                           text_color="#00FF00")
        title.pack(pady=20)
        
        username = ctk.CTkEntry(self.auth_frame,
                              placeholder_text="Username",
                              width=300,
                              font=("Exo 2", 14))
        username.pack(pady=10)
        
        password = ctk.CTkEntry(self.auth_frame,
                              placeholder_text="Password",
                              show="•",
                              width=300,
                              font=("Exo 2", 14))
        password.pack(pady=10)
        
        login_btn = ctk.CTkButton(self.auth_frame,
                                text="LOGIN",
                                font=("Orbitron", 14, "bold"),
                                command=lambda: self.login(username.get(), password.get()))
        login_btn.pack(pady=20)
    
    def show_register_form(self):
        """Display the registration form"""
        # Create form container
        self.auth_frame = ctk.CTkFrame(self.main_container, fg_color="#232323")
        self.auth_frame.place(relx=0.75, rely=0.5, anchor="center")
        
        # Register form
        title = ctk.CTkLabel(self.auth_frame,
                           text="Create Account",
                           font=("Orbitron", 24, "bold"),
                           text_color="#00FF00")
        title.pack(pady=20)
        
        username = ctk.CTkEntry(self.auth_frame,
                              placeholder_text="Username",
                              width=300,
                              font=("Exo 2", 14))
        username.pack(pady=10)
        
        email = ctk.CTkEntry(self.auth_frame,
                           placeholder_text="Email",
                           width=300,
                           font=("Exo 2", 14))
        email.pack(pady=10)
        
        password = ctk.CTkEntry(self.auth_frame,
                              placeholder_text="Password",
                              show="•",
                              width=300,
                              font=("Exo 2", 14))
        password.pack(pady=10)
        
        confirm_password = ctk.CTkEntry(self.auth_frame,
                                      placeholder_text="Confirm Password",
                                      show="•",
                                      width=300,
                                      font=("Exo 2", 14))
        confirm_password.pack(pady=10)
        
        register_btn = ctk.CTkButton(self.auth_frame,
                                   text="CREATE ACCOUNT",
                                   font=("Orbitron", 14, "bold"),
                                   command=lambda: self.register(
                                       username.get(),
                                       email.get(),
                                       password.get(),
                                       confirm_password.get()))
        register_btn.pack(pady=20)
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self, username, password):
        """Handle login authentication"""
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        conn = sqlite3.connect('genesis.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                 (username, self.hash_password(password)))
        user = c.fetchone()
        conn.close()
        
        if user:
            messagebox.showinfo("Success", "Login successful!")
            self.window.destroy()
            FaultDetectionApp()  # Launch main application
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def register(self, username, email, password, confirm_password):
        """Handle user registration"""
        if not username or not email or not password or not confirm_password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        try:
            conn = sqlite3.connect('genesis.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                     (username, email, self.hash_password(password)))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Account created successfully!")
            self.show_login_form()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {str(e)}")

if __name__ == "__main__":
    app = GenesisAuth() 