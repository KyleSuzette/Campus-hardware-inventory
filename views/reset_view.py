# DESKTOP ONLY — retained for the original desktop version
try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True

except ImportError:
    tk = None
    messagebox = None
    TKINTER_AVAILABLE = False

class ResetView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

        # Main frame
        self.frame = tk.Frame(parent, bg="#f0f0f0")
        self.frame.pack(fill="both", expand=True)

        # Keep the same compact structure as Register
        form_frame = tk.Frame(self.frame, bg="#f0f0f0")
        form_frame.pack(pady=25)

        # -------------------------
        # Account Username
        # -------------------------
        tk.Label(
            form_frame,
            text="Account Username:",
            font=("Arial", 10),
            bg="#f0f0f0",
            anchor="w"
        ).grid(row=0, column=0, padx=(0, 10), pady=6, sticky="w")

        self.username_entry = tk.Entry(
            form_frame,
            width=30,
            font=("Arial", 10)
        )
        self.username_entry.grid(
            row=0,
            column=1,
            pady=6
        )

        # -------------------------
        # Registered Email
        # -------------------------
        tk.Label(
            form_frame,
            text="Registered Email:",
            font=("Arial", 10),
            bg="#f0f0f0",
            anchor="w"
        ).grid(row=1, column=0, padx=(0, 10), pady=6, sticky="w")

        self.email_entry = tk.Entry(
            form_frame,
            width=30,
            font=("Arial", 10)
        )
        self.email_entry.grid(
            row=1,
            column=1,
            pady=6
        )

        # -------------------------
        # Desired New Password
        # -------------------------
        tk.Label(
            form_frame,
            text="Desired New Password:",
            font=("Arial", 10),
            bg="#f0f0f0",
            anchor="w"
        ).grid(row=2, column=0, padx=(0, 10), pady=6, sticky="w")

        self.new_password_entry = tk.Entry(
            form_frame,
            width=30,
            font=("Arial", 10),
            show="*"
        )
        self.new_password_entry.grid(
            row=2,
            column=1,
            pady=6
        )

        # -------------------------
        # Confirm New Password
        # -------------------------
        tk.Label(
            form_frame,
            text="Confirm New Password:",
            font=("Arial", 10),
            bg="#f0f0f0",
            anchor="w"
        ).grid(row=3, column=0, padx=(0, 10), pady=6, sticky="w")

        self.confirm_password_entry = tk.Entry(
            form_frame,
            width=30,
            font=("Arial", 10),
            show="*"
        )
        self.confirm_password_entry.grid(
            row=3,
            column=1,
            pady=6
        )

        # -------------------------
        # Submit Button
        # -------------------------
        self.submit_button = tk.Button(
            form_frame,
            text="Submit Reset / Unlock Request",
            font=("Arial", 10),
            width=28,
            command=self.submit_request,
            cursor="hand2"
        )
        self.submit_button.grid(
            row=4,
            column=0,
            columnspan=2,
            pady=(15, 5)
        )

    def submit_request(self):
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        if not username or not email or not new_password or not confirm_password:
            messagebox.showwarning(
                "Missing Information",
                "Please complete all fields."
            )
            return

        if new_password != confirm_password:
            messagebox.showerror(
                "Password Mismatch",
                "The new passwords do not match."
            )
            return

        # Send the request to the controller
        self.controller.submit_reset_request(
            username,
            email,
            new_password
        )

    def clear_fields(self):
        self.username_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.new_password_entry.delete(0, tk.END)
        self.confirm_password_entry.delete(0, tk.END)