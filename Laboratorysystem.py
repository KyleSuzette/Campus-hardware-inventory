try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    TKINTER_AVAILABLE = True

except ImportError:
    tk = None
    messagebox = None
    ttk = None
    TKINTER_AVAILABLE = False

from models.database import init_db

from controllers.auth_controller import AuthController
from controllers.inventory_controller import InventoryController
from controllers.reset_controller import ResetController

from views.auth_view import AuthView
from views.inventory_view import InventoryView
from views.admin_view import AdminView
from views.profile_view import ProfileView


class Application:

    def __init__(self, root):

        self.root = root

        self.current_username = None
        self.current_role = None

        # Initialize database
        init_db()

        # Controllers
        self.auth_controller = AuthController(self)
        self.inventory_controller = InventoryController(self)
        self.reset_controller = ResetController(self)

        # Start application
        self.show_auth()

    # ======================================================
    # AUTHENTICATION SCREEN
    # ======================================================

    def show_auth(self):

        self.clear_window()

        self.root.title(
            "Campus Hardware Laboratory"
        )

        self.center_window(
            500,
            560
        )

        AuthView(
            self.root,
            self.auth_controller,
            self.reset_controller
        )

    # ======================================================
    # USER HARDWARE VIEW
    # ======================================================

    def show_inventory(
        self,
        username,
        role
    ):

        self.current_username = username
        self.current_role = role

        self.clear_window()

        self.root.title(
            "Hardware Laboratory"
        )

        self.center_window(
            1050,
            680
        )

        InventoryView(
            self.root,
            self.inventory_controller,
            username,
            role
        )

    # ======================================================
    # ADMIN PANEL
    # ======================================================

    def show_admin_approvals(self):

        self.clear_window()

        self.root.title(
            "Hardware Laboratory - Admin Panel"
        )

        self.center_window(
            1100,
            720
        )

        AdminView(
            self.root,
            self.reset_controller,
            self.current_username,
            self.inventory_controller
        )

    # ======================================================
    # PROFILE
    # ======================================================

    def show_profile(
        self,
        username,
        role
    ):

        self.current_username = username
        self.current_role = role

        self.clear_window()

        self.root.title(
            "My Profile & Security"
        )

        self.center_window(
            460,
            560
        )

        ProfileView(
            self.root,
            self.auth_controller,
            username,
            role
        )

    # ======================================================
    # CENTER WINDOW
    # ======================================================

    def center_window(
        self,
        width,
        height
    ):

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (
            screen_width - width
        ) // 2

        y = (
            screen_height - height
        ) // 2

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    # ======================================================
    # CLEAR WINDOW
    # ======================================================

    def clear_window(self):

        for widget in self.root.winfo_children():
            widget.destroy()


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = Application(root)

    root.mainloop()