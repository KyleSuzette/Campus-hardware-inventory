# DESKTOP ONLY — retained for the original desktop version
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TKINTER_AVAILABLE = True

except ImportError:
    tk = None
    ttk = None
    messagebox = None
    TKINTER_AVAILABLE = False


class AuthView:

    def __init__(
        self,
        root,
        auth_controller,
        reset_controller
    ):

        self.root = root
        self.auth = auth_controller
        self.reset = reset_controller

        self.build()

    # ======================================================
    # BUILD
    # ======================================================

    def build(self):

        tk.Label(
            self.root,
            text="Campus Hardware Inventory",
            font=("Arial", 18, "bold")
        ).pack(pady=(20, 3))

        tk.Label(
            self.root,
            text="User Authentication",
            fg="gray"
        ).pack(pady=(0, 10))

        notebook = ttk.Notebook(self.root)

        notebook.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=10
        )

        self.build_login_tab(notebook)
        self.build_register_tab(notebook)
        self.build_reset_tab(notebook)

    # ======================================================
    # LOGIN TAB
    # ======================================================

    def build_login_tab(self, notebook):

        tab = tk.Frame(
            notebook,
            padx=30,
            pady=20
        )

        notebook.add(
            tab,
            text="Login"
        )

        tk.Label(
            tab,
            text="Username:"
        ).pack(anchor="w")

        self.login_username = tk.Entry(
            tab,
            width=35
        )

        self.login_username.pack(
            pady=(3, 12)
        )

        tk.Label(
            tab,
            text="Password:"
        ).pack(anchor="w")

        self.login_password = tk.Entry(
            tab,
            width=35,
            show="*"
        )

        self.login_password.pack(
            pady=3
        )

        self.show_login_password = tk.BooleanVar()

        tk.Checkbutton(
            tab,
            text="Show Password",
            variable=self.show_login_password,
            command=lambda: self.login_password.config(
                show="" if self.show_login_password.get() else "*"
            )
        ).pack(
            anchor="w"
        )

        tk.Button(
            tab,
            text="Login",
            command=self.login,
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2
        ).pack(pady=20)

    # ======================================================
    # REGISTER TAB
    # ======================================================

    def build_register_tab(self, notebook):

        tab = tk.Frame(
            notebook,
            padx=30,
            pady=10
        )

        notebook.add(
            tab,
            text="Register"
        )

        tk.Label(
            tab,
            text="Username:"
        ).pack(anchor="w")

        self.reg_username = tk.Entry(
            tab,
            width=35
        )

        self.reg_username.pack(
            pady=3
        )

        tk.Label(
            tab,
            text="Email:"
        ).pack(anchor="w")

        self.reg_email = tk.Entry(
            tab,
            width=35
        )

        self.reg_email.pack(
            pady=3
        )

        tk.Label(
            tab,
            text="User Role:"
        ).pack(anchor="w")

        self.reg_role = ttk.Combobox(
            tab,
            values=("USER", "ADMIN"),
            state="readonly",
            width=32
        )

        self.reg_role.set("USER")

        self.reg_role.pack(
            pady=3
        )

        tk.Label(
            tab,
            text="Password:"
        ).pack(anchor="w")

        self.reg_password = tk.Entry(
            tab,
            width=35,
            show="*"
        )

        self.reg_password.pack(
            pady=3
        )

        tk.Label(
            tab,
            text=(
                "Minimum 8 characters\n"
                "1 uppercase letter\n"
                "1 number\n"
                "1 special character"
            ),
            fg="gray",
            justify="left"
        ).pack(
            anchor="w",
            pady=5
        )

        tk.Button(
            tab,
            text="Create Account",
            command=self.register,
            bg="#2196F3",
            fg="white",
            width=20
        ).pack(
            pady=10
        )

    # ======================================================
    # RESET / UNLOCK TAB
    # ======================================================

    def build_reset_tab(self, notebook):

        tab = tk.Frame(
            notebook,
            padx=30,
            pady=20
        )

        notebook.add(
            tab,
            text="Reset / Unlock"
        )

        tk.Label(
            tab,
            text=(
                "Step 1: submit this form to request a "
                "reset.\nStep 2: after an ADMIN approves it, "
                "submit it again\nwith your new password to "
                "unlock your account."
            ),
            fg="gray",
            justify="left",
            font=("Arial", 8)
        ).pack(
            anchor="w",
            pady=(0, 8)
        )

        # Form container
        form_frame = tk.Frame(tab)

        form_frame.pack(
            pady=5
        )

        # --------------------------------------------------
        # Username
        # --------------------------------------------------

        tk.Label(
            form_frame,
            text="Account Username:",
            font=("Arial", 10),
            anchor="w"
        ).grid(
            row=0,
            column=0,
            padx=(0, 10),
            pady=6,
            sticky="w"
        )

        self.reset_username = tk.Entry(
            form_frame,
            width=30,
            font=("Arial", 10)
        )

        self.reset_username.grid(
            row=0,
            column=1,
            pady=6
        )

        # --------------------------------------------------
        # Email
        # --------------------------------------------------

        tk.Label(
            form_frame,
            text="Registered Email:",
            font=("Arial", 10),
            anchor="w"
        ).grid(
            row=1,
            column=0,
            padx=(0, 10),
            pady=6,
            sticky="w"
        )

        self.reset_email = tk.Entry(
            form_frame,
            width=30,
            font=("Arial", 10)
        )

        self.reset_email.grid(
            row=1,
            column=1,
            pady=6
        )

        # --------------------------------------------------
        # New Password
        # --------------------------------------------------

        tk.Label(
            form_frame,
            text="Desired New Password:",
            font=("Arial", 10),
            anchor="w"
        ).grid(
            row=2,
            column=0,
            padx=(0, 10),
            pady=6,
            sticky="w"
        )

        self.reset_password = tk.Entry(
            form_frame,
            width=30,
            font=("Arial", 10),
            show="*"
        )

        self.reset_password.grid(
            row=2,
            column=1,
            pady=6
        )

        # --------------------------------------------------
        # Confirm Password
        # --------------------------------------------------

        tk.Label(
            form_frame,
            text="Confirm New Password:",
            font=("Arial", 10),
            anchor="w"
        ).grid(
            row=3,
            column=0,
            padx=(0, 10),
            pady=6,
            sticky="w"
        )

        self.reset_confirm_password = tk.Entry(
            form_frame,
            width=30,
            font=("Arial", 10),
            show="*"
        )

        self.reset_confirm_password.grid(
            row=3,
            column=1,
            pady=6
        )

        # --------------------------------------------------
        # Submit Button
        # --------------------------------------------------

        tk.Button(
            form_frame,
            text="Submit Reset / Unlock Request",
            font=("Arial", 10),
            width=28,
            command=self.submit_reset,
            cursor="hand2"
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            pady=(15, 5)
        )

    # ======================================================
    # LOGIN ACTION
    # ======================================================

    def login(self):

        username = self.login_username.get().strip()
        password = self.login_password.get()

        if not username or not password:
            messagebox.showwarning(
                "Login",
                "Please enter your username and password."
            )
            return

        success, result = self.auth.login(
            username,
            password
        )

        if success:

            self.auth.app.current_username = username
            self.auth.app.current_role = result

            if str(result).upper() == "ADMIN":

                self.auth.app.show_admin_approvals()

            else:

                self.auth.app.show_inventory(
                    username,
                    result
                )

        else:

            messagebox.showerror(
                "Login Failed",
                result
            )

        username = self.login_username.get().strip()
        password = self.login_password.get()

        success, result = self.auth.login(
            username,
            password
        )

        if success:

           if str(result).upper() == "ADMIN":

            self.auth.app.current_username = username
            self.auth.app.current_role = result

            self.auth.app.show_admin_approvals()

        else:

            self.auth.app.show_inventory(
            username,
            result
        )

    # ======================================================
    # REGISTER ACTION
    # ======================================================

    def register(self):

        success, message = self.auth.register(
            self.reg_username.get().strip(),
            self.reg_email.get().strip(),
            self.reg_password.get(),
            self.reg_role.get()
        )

        if success:

            messagebox.showinfo(
                "Registration",
                message
            )

            self.reg_username.delete(
                0,
                tk.END
            )

            self.reg_email.delete(
                0,
                tk.END
            )

            self.reg_password.delete(
                0,
                tk.END
            )

        else:

            messagebox.showwarning(
                "Registration",
                message
            )

    # ======================================================
    # RESET / UNLOCK ACTION
    # ======================================================
    #
    # Two-step flow:
    #   1. No approved request yet -> file a new PENDING
    #      request (username/new-password fields are only
    #      used for validation/UX at this stage).
    #   2. An APPROVED request already exists for this email
    #      -> actually perform the reset using the new
    #      password fields, which unlocks the account.
    # ======================================================

    def submit_reset(self):

        username = self.reset_username.get().strip()
        email = self.reset_email.get().strip()
        new_password = self.reset_password.get()
        confirm_password = self.reset_confirm_password.get()

        # --------------------------------------------------
        # Required field validation
        # --------------------------------------------------

        if (
            not username
            or not email
            or not new_password
            or not confirm_password
        ):

            messagebox.showwarning(
                "Missing Information",
                "Please complete all fields."
            )

            return

        # --------------------------------------------------
        # Password confirmation
        # --------------------------------------------------

        if new_password != confirm_password:

            messagebox.showerror(
                "Password Mismatch",
                "The new passwords do not match."
            )

            return

        # --------------------------------------------------
        # Decide which step we're on
        # --------------------------------------------------

        if self.reset.has_approved_request(email):

            success, message = self.reset.perform_reset(
                email,
                new_password
            )

        else:

            success, message = self.reset.submit_request(
                email
            )

        if success:

            messagebox.showinfo(
                "Reset Request",
                message
            )

            self.reset_username.delete(
                0,
                tk.END
            )

            self.reset_email.delete(
                0,
                tk.END
            )

            self.reset_password.delete(
                0,
                tk.END
            )

            self.reset_confirm_password.delete(
                0,
                tk.END
            )

        else:

            messagebox.showwarning(
                "Reset Request",
                message
            )

