import tkinter as tk
from tkinter import messagebox
import sqlite3
from tkinter import ttk

# Helper function for animated label
class AnimatedLabel(tk.Label):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = ["#FF5733", "#33FF57", "#3357FF", "#F3FF33", "#FF33A1"]
        self.index = 0
        self.animate()

    def animate(self):
        self.config(fg=self.colors[self.index])
        self.index = (self.index + 1) % len(self.colors)
        self.after(500, self.animate)

def initialize_database():
    conn = sqlite3.connect('ice_cream_parlor.db')
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS flavors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        price REAL NOT NULL,
                        season TEXT DEFAULT 'All')''')

    
def fetch_flavors(season=None, search_query="", limit=20, offset=0):
    conn = sqlite3.connect('ice_cream_parlor.db')
    cursor = conn.cursor()
    query = 'SELECT name, price FROM flavors WHERE name LIKE ?'

    params = [f'%{search_query}%']

    if season and season != "All":
        query += ' AND (season = ? OR season = "All")'
        params.append(season)

    query += ' LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    cursor.execute(query, tuple(params))
    flavors = cursor.fetchall()
    conn.close()
    return flavors

def authenticate_user(username, password):
    conn = sqlite3.connect('ice_cream_parlor.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(username, password):
    conn = sqlite3.connect('ice_cream_parlor.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username already exists!")
    conn.close()

class IceCreamParlorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ice Cream Parlor")
        self.root.geometry("600x600")
        self.root.config(bg="#f0f0f0")
        initialize_database()
        self.current_user = None
        self.page_offset = 0
        self.cart = []
        self.selected_flavors = []  # Store selected flavors for adding to cart
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 12, 'bold'))
        self.style.map('TButton', background=[('!active', '#4CAF50'), ('active', '#45a049')])
        self.show_login_screen()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_window()

        AnimatedLabel(self.root, text="Welcome to Ice Cream Parlor", font=("Comic Sans MS", 24, "bold"), bg="#f0f0f0").pack(pady=20)

        tk.Label(self.root, text="Username:", font=("Poppins", 12), bg="#f0f0f0", fg="black").pack()
        self.username_entry = ttk.Entry(self.root, font=("Poppins", 12), width=20)
        self.username_entry.pack(pady=5)

        tk.Label(self.root, text="Password:", font=("Poppins", 12), bg="#f0f0f0", fg="black").pack()
        self.password_entry = ttk.Entry(self.root, font=("Poppins", 12), width=20, show="*")
        self.password_entry.pack(pady=5)

        ttk.Button(self.root, text="Login", command=self.login).pack(pady=10)
        ttk.Button(self.root, text="Sign Up", command=self.signup).pack(pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if authenticate_user(username, password):
            self.current_user = username
            self.show_home_page()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password!")

    def signup(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            add_user(username, password)
            messagebox.showinfo("Success", "Account created successfully!")
        else:
            messagebox.showerror("Error", "Please enter both username and password!")

    def show_home_page(self):
        self.clear_window()

        menu_frame = tk.Frame(self.root, bg="#f0f0f0")
        menu_frame.pack(pady=20)

        ttk.Button(menu_frame, text="Browse Flavors", command=self.show_flavors).pack(side="left", padx=10)
        ttk.Button(menu_frame, text="View Cart", command=self.view_cart).pack(side="left", padx=10)
        ttk.Button(menu_frame, text="Logout", command=self.show_login_screen).pack(side="left", padx=10)

        tk.Label(self.root, text=f"Welcome, {self.current_user}!", font=("Comic Sans MS", 20, "bold"), bg="#f0f0f0", fg="black").pack(pady=20)

    def show_flavors(self):
        self.clear_window()

        tk.Label(self.root, text="Search Flavors:", font=("Poppins", 12), bg="#f0f0f0", fg="black").pack()
        self.search_entry = ttk.Entry(self.root, font=("Poppins", 12), width=20)
        self.search_entry.pack(pady=5)

        tk.Label(self.root, text="Filter by Season:", font=("Poppins", 12), bg="#f0f0f0", fg="black").pack()
        self.season_var = tk.StringVar(value="All")
        seasons = ["All", "Summer", "Winter", "Spring"]
        ttk.Combobox(self.root, textvariable=self.season_var, values=seasons, font=("Poppins", 12)).pack(pady=5)

        ttk.Button(self.root, text="Search", command=self.search_flavors).pack(pady=10)

        self.flavor_listbox = tk.Listbox(self.root, width=50, height=10, font=("Poppins", 12))
        self.flavor_listbox.pack(pady=10)

        self.load_flavors()

        # Add Back and Next buttons
        ttk.Button(self.root, text="Back to Home", command=self.show_home_page).pack(side="left", padx=10, pady=10)
        ttk.Button(self.root, text="Next", command=self.next_page).pack(side="left", padx=10, pady=10)

    def search_flavors(self):
        search_query = self.search_entry.get()
        season = self.season_var.get()
        self.page_offset = 0
        self.load_flavors(search_query, season)

    def load_flavors(self, search_query="", season="All"):
        self.flavor_listbox.delete(0, tk.END)

        flavors = fetch_flavors(season, search_query, limit=5, offset=self.page_offset)
        for flavor in flavors:
            flavor_name, price = flavor
            flavor_button = ttk.Button(self.root, text=f"{flavor_name} - ${price:.2f}", command=lambda fn=flavor_name, pr=price: self.add_to_cart(fn, pr))
            flavor_button.pack(pady=5)

    def next_page(self):
        # Proceed to the cart page if next is clicked after adding items
        self.view_cart()

    def add_to_cart(self, flavor_name, price):
        self.cart.append((flavor_name, price))
        messagebox.showinfo("Added to Cart", f"{flavor_name} added to cart.")

    def view_cart(self):
        self.clear_window()

        tk.Label(self.root, text="Your Cart", font=("Comic Sans MS", 20, "bold"), bg="#f0f0f0", fg="black").pack(pady=20)

        if not self.cart:
            tk.Label(self.root, text="Your cart is empty", font=("Poppins", 12), bg="#f0f0f0", fg="black").pack()

        total_price = 0
        for item in self.cart:
            flavor_name, price = item
            total_price += price
            tk.Label(self.root, text=f"{flavor_name} - ${price:.2f}", font=("Poppins", 12), bg="#f0f0f0", fg="black").pack()

        tk.Label(self.root, text=f"Total Price: ${total_price:.2f}", font=("Poppins", 12, "bold"), bg="#f0f0f0", fg="black").pack()

        # Add Back and Checkout buttons
        ttk.Button(self.root, text="Back to Flavors", command=self.show_flavors).pack(side="left", padx=10, pady=10)
        ttk.Button(self.root, text="Checkout", command=self.checkout).pack(side="left", padx=10, pady=10)

    def checkout(self):
        if not self.cart:
            messagebox.showerror("Error", "Your cart is empty!")
        else:
            total_price = sum([item[1] for item in self.cart])
            messagebox.showinfo("Checkout", f"Total Amount: ${total_price:.2f}\nThank you for your purchase!")
            self.cart.clear()

root = tk.Tk()
app = IceCreamParlorApp(root)
root.mainloop()
