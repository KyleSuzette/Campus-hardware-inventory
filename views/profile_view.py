# DESKTOP ONLY — retained for the original desktop version
try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True

except ImportError:
    tk = None
    messagebox = None
    TKINTER_AVAILABLE = False


class ProfileView:

    def __init__(
        self,
        root,
        auth_controller,
        username,
        role
    ):

        self.root = root
        self.auth = auth_controller
        self.username = username
        self.role = role

        self.build()

    # ======================================================
    # BUILD
    # ======================================================

    def build(self):

        tk.Label(
            self.root,
            text="My Profile & Security",
            font=("Arial", 18, "bold")
        ).pack(pady=(20, 3))

        tk.Label(
            self.root,
            text="Account Information",
            fg="gray"
        ).pack(pady=(0, 10))

        info = self.auth.get_user_info(
            self.username
        )

        info_frame = tk.LabelFrame(
            self.root,
            text="Account Details",
            padx=15,
            pady=10
        )

        info_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 15)
        )

        if info:

            tk.Label(
                info_frame,
                text=f"Username: {info['username']}",
                anchor="w"
            ).pack(
                fill="x",
                pady=2
            )

            tk.Label(
                info_frame,
                text=f"Email: {info['email']}",
                anchor="w"
            ).pack(
                fill="x",
                pady=2
            )

            tk.Label(
                info_frame,
                text=f"Role: {info['role']}",
                anchor="w"
            ).pack(
                fill="x",
                pady=2
            )

        # --------------------------------------------------
        # PASSWORD
        # --------------------------------------------------

        change_frame = tk.LabelFrame(
            self.root,
            text="Change Password",
            padx=15,
            pady=10
        )

        change_frame.pack(
            fill="x",
            padx=25,
            pady=(0, 15)
        )

        tk.Label(
            change_frame,
            text="Current Password:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=4
        )

        self.current_password_entry = tk.Entry(
            change_frame,
            width=28,
            show="*"
        )

        self.current_password_entry.grid(
            row=0,
            column=1,
            pady=4
        )

        tk.Label(
            change_frame,
            text="New Password:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=4
        )

        self.new_password_entry = tk.Entry(
            change_frame,
            width=28,
            show="*"
        )

        self.new_password_entry.grid(
            row=1,
            column=1,
            pady=4
        )

        tk.Label(
            change_frame,
            text="Confirm New Password:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=4
        )

        self.confirm_password_entry = tk.Entry(
            change_frame,
            width=28,
            show="*"
        )

        self.confirm_password_entry.grid(
            row=2,
            column=1,
            pady=4
        )

        tk.Label(
            change_frame,
            text=(
                "Minimum 8 characters, 1 uppercase letter,\n"
                "1 number, 1 special character (@#$%^&*)"
            ),
            fg="gray",
            justify="left",
            font=("Arial", 8)
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(4, 8)
        )

        tk.Button(
            change_frame,
            text="Change Password",
            command=self.change_password,
            bg="#2196F3",
            fg="white",
            width=20
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            pady=5
        )

        # --------------------------------------------------
        # BACK BUTTON
        # --------------------------------------------------

        back_text = (
            "Back to Admin Panel"
            if str(self.role).upper() == "ADMIN"
            else "Back to Hardware Laboratory"
        )

        tk.Button(
            self.root,
            text=back_text,
            command=self.go_back,
            width=25
        ).pack(pady=5)

        tk.Button(
            self.root,
            text="Logout",
            command=self.logout,
            width=25
        ).pack(pady=(5, 15))

    # ======================================================
    # CHANGE PASSWORD
    # ======================================================

    def change_password(self):

        current_password = (
            self.current_password_entry.get()
        )

        new_password = (
            self.new_password_entry.get()
        )

        confirm_password = (
            self.confirm_password_entry.get()
        )

        if not current_password or not new_password or not confirm_password:

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

        success, message = self.auth.change_password(
            self.username,
            current_password,
            new_password
        )

        if success:

            messagebox.showinfo(
                "Password Changed",
                message
            )

            self.auth.logout()

        else:

            messagebox.showwarning(
                "Password Change Failed",
                message
            )

    # ======================================================
    # BACK
    # ======================================================

    def go_back(self):

        if str(self.role).upper() == "ADMIN":

            self.auth.app.show_admin_approvals()

        else:

            self.auth.app.show_inventory(
                self.username,
                self.role
            )

    # ======================================================
    # LOGOUT
    # ======================================================

    def logout(self):

        self.auth.logout()