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

from datetime import datetime

class InventoryView:

    def __init__(
        self,
        root,
        controller,
        username,
        role
    ):

        self.root = root
        self.controller = controller
        self.username = username
        self.role = role

        self.selected_hardware_id = None

        self.build()

    # ======================================================
    # BUILD
    # ======================================================

    def build(self):

        header = tk.Frame(
            self.root,
            padx=20,
            pady=15
        )

        header.pack(fill="x")

        tk.Label(
            header,
            text="Hardware Laboratory",
            font=("Arial", 20, "bold")
        ).pack(side="left")

        right = tk.Frame(header)
        right.pack(side="right")

        tk.Label(
            right,
            text=f"User: {self.username}",
            fg="gray"
        ).pack(side="left", padx=10)

        tk.Button(
            right,
            text="My Profile & Security",
            command=self.open_profile
        ).pack(side="left", padx=5)

        tk.Button(
            right,
            text="Logout",
            command=self.logout
        ).pack(side="left", padx=5)

        # --------------------------------------------------
        # TITLE
        # --------------------------------------------------

        tk.Label(
            self.root,
            text="Available Laboratory Hardware",
            font=("Arial", 15, "bold")
        ).pack(
            anchor="w",
            padx=20,
            pady=(5, 2)
        )

        tk.Label(
            self.root,
            text=(
                "Browse available hardware and submit a "
                "borrowing request for laboratory use."
            ),
            fg="gray"
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 10)
        )

        # --------------------------------------------------
        # SEARCH
        # --------------------------------------------------

        search_frame = tk.Frame(
            self.root,
            padx=20,
            pady=5
        )

        search_frame.pack(fill="x")

        tk.Label(
            search_frame,
            text="Search:"
        ).pack(side="left")

        self.search_entry = tk.Entry(
            search_frame,
            width=25
        )

        self.search_entry.pack(
            side="left",
            padx=5
        )

        self.search_entry.bind(
            "<KeyRelease>",
            lambda event: self.search_hardware()
        )

        tk.Label(
            search_frame,
            text="Category:"
        ).pack(
            side="left",
            padx=(15, 3)
        )

        self.category_combo = ttk.Combobox(
            search_frame,
            state="readonly",
            width=18
        )

        self.category_combo.pack(side="left")

        self.category_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.search_hardware()
        )

        tk.Label(
            search_frame,
            text="Status:"
        ).pack(
            side="left",
            padx=(15, 3)
        )

        self.status_combo = ttk.Combobox(
            search_frame,
            state="readonly",
            width=15,
            values=(
                "All Statuses",
                "In Stock",
                "Low Stock",
                "Out of Stock"
            )
        )

        self.status_combo.set("All Statuses")
        self.status_combo.pack(side="left")

        self.status_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.search_hardware()
        )

        # --------------------------------------------------
        # TABLE
        # --------------------------------------------------

        table_frame = tk.Frame(
            self.root,
            padx=20
        )

        table_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "name",
            "category",
            "total",
            "available",
            "price",
            "status"
        )

        self.hardware_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "name": "Hardware",
            "category": "Category",
            "total": "Total Qty",
            "available": "Available",
            "price": "Unit Price",
            "status": "Status"
        }

        widths = {
            "id": 55,
            "name": 210,
            "category": 150,
            "total": 90,
            "available": 95,
            "price": 110,
            "status": 120
        }

        for column in columns:

            self.hardware_tree.heading(
                column,
                text=headings[column]
            )

            self.hardware_tree.column(
                column,
                width=widths[column],
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.hardware_tree.yview
        )

        self.hardware_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.hardware_tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.hardware_tree.bind(
            "<<TreeviewSelect>>",
            self.select_hardware
        )

        # --------------------------------------------------
        # PALE STATUS COLORS
        # --------------------------------------------------

        self.hardware_tree.tag_configure(
            "in_stock",
            background="#E8F5E9"
        )

        self.hardware_tree.tag_configure(
            "low_stock",
            background="#FFF8E1"
        )

        self.hardware_tree.tag_configure(
            "out_stock",
            background="#FFEBEE"
        )

        # --------------------------------------------------
        # BUTTONS
        # --------------------------------------------------

        button_frame = tk.Frame(
            self.root,
            pady=12
        )

        button_frame.pack(fill="x")

        tk.Button(
            button_frame,
            text="Request to Borrow",
            command=self.open_borrow_form,
            bg="#2196F3",
            fg="white",
            width=20
        ).pack(
            side="left",
            padx=(20, 5)
        )

        tk.Button(
            button_frame,
            text="My Borrowings",
            command=self.open_my_borrowings,
            width=18
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Refresh",
            command=self.load_data,
            width=12
        ).pack(
            side="right",
            padx=20
        )

        self.load_categories()
        self.load_data()

    # ======================================================
    # LOAD CATEGORIES
    # ======================================================

    def load_categories(self):

        categories = self.controller.get_categories()

        self.category_combo["values"] = (
            ["All Categories"] + categories
        )

        self.category_combo.set(
            "All Categories"
        )

    # ======================================================
    # LOAD DATA
    # ======================================================

    def load_data(self, rows=None):

        if rows is None:

            rows = self.controller.get_available_hardware()

        for item in self.hardware_tree.get_children():

            self.hardware_tree.delete(item)

        for row in rows:

            (
                item_id,
                name,
                category,
                total,
                available,
                price,
                status
            ) = row

            if status == "In Stock":

                tag = "in_stock"

            elif status == "Low Stock":

                tag = "low_stock"

            else:

                tag = "out_stock"

            self.hardware_tree.insert(
                "",
                "end",
                values=(
                    item_id,
                    name,
                    category,
                    total,
                    available,
                    f"₱{price:,.2f}",
                    status
                ),
                tags=(tag,)
            )

    # ======================================================
    # SELECT HARDWARE
    # ======================================================

    def select_hardware(self, event=None):

        selection = self.hardware_tree.selection()

        if not selection:

            self.selected_hardware_id = None

            return

        values = self.hardware_tree.item(
            selection[0],
            "values"
        )

        self.selected_hardware_id = int(
            values[0]
        )

    # ======================================================
    # SEARCH
    # ======================================================

    def search_hardware(self):

        rows = self.controller.search_hardware(
            self.search_entry.get(),
            self.category_combo.get(),
            self.status_combo.get()
        )

        self.load_data(rows)

    # ======================================================
    # BORROW FORM
    # ======================================================

    def open_borrow_form(self):

        window = tk.Toplevel(self.root)

        window.title(
            "Borrow Hardware"
        )

        # COMPACT WINDOW SIZE
        window.geometry(
            "650x600"
        )

        window.resizable(
            False,
            False
        )

        window.transient(
            self.root
        )

        window.grab_set()

        # ==================================================
        # TITLE
        # ==================================================

        tk.Label(
            window,
            text="Hardware Borrow Slip",
            font=("Arial", 15, "bold")
        ).pack(
            pady=(10, 2)
        )

        tk.Label(
            window,
            text=(
                "Add laboratory components to your borrowing request."
            ),
            fg="gray"
        ).pack(
            pady=(0, 7)
        )

        # ==================================================
        # STUDENT NUMBER
        # ==================================================

        top_form = tk.Frame(
            window,
            padx=15
        )

        top_form.pack(
            fill="x"
        )

        tk.Label(
            top_form,
            text="Student Number:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=4
        )

        student_number_entry = tk.Entry(
            top_form,
            width=30
        )

        student_number_entry.grid(
            row=0,
            column=1,
            sticky="w",
            pady=4
        )

        # ==================================================
        # COMPONENT SELECTION
        # ==================================================

        selection_frame = tk.LabelFrame(
            window,
            text="Add Components",
            padx=8,
            pady=5
        )

        selection_frame.pack(
            fill="x",
            padx=15,
            pady=6
        )

        tk.Label(
            selection_frame,
            text="Component:"
        ).grid(
            row=0,
            column=0,
            padx=4,
            pady=3
        )

        hardware_combo = ttk.Combobox(
            selection_frame,
            state="readonly",
            width=25
        )

        hardware_combo.grid(
            row=0,
            column=1,
            padx=4,
            pady=3
        )

        tk.Label(
            selection_frame,
            text="Quantity:"
        ).grid(
            row=0,
            column=2,
            padx=4,
            pady=3
        )

        quantity_entry = tk.Entry(
            selection_frame,
            width=7
        )

        quantity_entry.insert(
            0,
            "1"
        )

        quantity_entry.grid(
            row=0,
            column=3,
            padx=4,
            pady=3
        )

        available_label = tk.Label(
            selection_frame,
            text="Available: -",
            fg="gray"
        )

        available_label.grid(
            row=1,
            column=0,
            columnspan=4,
            pady=2
        )

        # ==================================================
        # AVAILABLE HARDWARE DATA
        # ==================================================

        available_rows = (
            self.controller.get_available_hardware()
        )

        hardware_data = {}

        for row in available_rows:

            (
                item_id,
                name,
                category,
                total,
                available,
                price,
                status
            ) = row

            display = (
                f"{name} "
                f"({category})"
            )

            hardware_data[display] = {
                "item_id": item_id,
                "name": name,
                "available": available
            }

        hardware_combo["values"] = list(
            hardware_data.keys()
        )

        if hardware_data:

            hardware_combo.current(0)

            first = hardware_data[
                hardware_combo.get()
            ]

            available_label.config(
                text=f"Available: {first['available']}"
            )

        def update_available(event=None):

            selected = hardware_combo.get()

            if selected in hardware_data:

                available = hardware_data[
                    selected
                ]["available"]

                available_label.config(
                    text=f"Available: {available}"
                )

        hardware_combo.bind(
            "<<ComboboxSelected>>",
            update_available
        )

        # ==================================================
        # COMPONENT CART
        # ==================================================

        cart_frame = tk.LabelFrame(
            window,
            text="Components in Borrow Slip",
            padx=6,
            pady=5
        )

        cart_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=4
        )

        cart_columns = (
            "id",
            "component",
            "quantity",
            "available"
        )

        cart_tree = ttk.Treeview(
            cart_frame,
            columns=cart_columns,
            show="headings",
            height=4
        )

        cart_headings = {
            "id": "ID",
            "component": "Component",
            "quantity": "Quantity",
            "available": "Available"
        }

        cart_widths = {
            "id": 40,
            "component": 230,
            "quantity": 80,
            "available": 80
        }

        for column in cart_columns:

            cart_tree.heading(
                column,
                text=cart_headings[column]
            )

            cart_tree.column(
                column,
                width=cart_widths[column],
                anchor="center"
            )

        cart_tree.pack(
            fill="both",
            expand=True
        )

        # ==================================================
        # CART FUNCTIONS
        # ==================================================

        def add_component():

            selected = hardware_combo.get()

            if selected not in hardware_data:

                messagebox.showwarning(
                    "Add Component",
                    "Please select a hardware component.",
                    parent=window
                )

                return

            try:

                quantity = int(
                    quantity_entry.get().strip()
                )

            except ValueError:

                messagebox.showwarning(
                    "Add Component",
                    "Quantity must be a valid number.",
                    parent=window
                )

                return

            if quantity <= 0:

                messagebox.showwarning(
                    "Add Component",
                    "Quantity must be at least 1.",
                    parent=window
                )

                return

            data = hardware_data[selected]

            item_id = data["item_id"]
            available = data["available"]

            # ----------------------------------------------
            # Check if already in cart
            # ----------------------------------------------

            for item in cart_tree.get_children():

                values = cart_tree.item(
                    item,
                    "values"
                )

                existing_id = int(
                    values[0]
                )

                if existing_id == item_id:

                    existing_quantity = int(
                        values[2]
                    )

                    new_quantity = (
                        existing_quantity
                        + quantity
                    )

                    if new_quantity > available:

                        messagebox.showwarning(
                            "Quantity",
                            f"Only {available} "
                            f"unit(s) of "
                            f"{data['name']} "
                            f"are available.",
                            parent=window
                        )

                        return

                    cart_tree.item(
                        item,
                        values=(
                            item_id,
                            data["name"],
                            new_quantity,
                            available
                        )
                    )

                    return

            # ----------------------------------------------
            # Check availability
            # ----------------------------------------------

            if quantity > available:

                messagebox.showwarning(
                    "Quantity",
                    f"Only {available} unit(s) "
                    f"of {data['name']} "
                    f"are available.",
                    parent=window
                )

                return

            cart_tree.insert(
                "",
                "end",
                values=(
                    item_id,
                    data["name"],
                    quantity,
                    available
                )
            )

        def remove_component():

            selection = cart_tree.selection()

            if not selection:

                messagebox.showwarning(
                    "Remove Component",
                    "Please select a component "
                    "from the borrow slip.",
                    parent=window
                )

                return

            cart_tree.delete(
                selection[0]
            )

        # ==================================================
        # CART BUTTONS
        # ==================================================

        button_row = tk.Frame(
            selection_frame
        )

        button_row.grid(
            row=2,
            column=0,
            columnspan=4,
            pady=4
        )

        tk.Button(
            button_row,
            text="Add Component",
            command=add_component,
            width=16
        ).pack(
            side="left",
            padx=4
        )

        tk.Button(
            button_row,
            text="Remove Selected",
            command=remove_component,
            width=16
        ).pack(
            side="left",
            padx=4
        )

        # ==================================================
        # OTHER BORROW INFORMATION
        # ==================================================

        info_frame = tk.Frame(
            window,
            padx=15
        )

        info_frame.pack(
            fill="x",
            pady=3
        )

        tk.Label(
            info_frame,
            text="Purpose:"
        ).grid(
            row=0,
            column=0,
            sticky="nw",
            pady=3
        )

        purpose_entry = tk.Text(
            info_frame,
            width=30,
            height=2
        )

        purpose_entry.grid(
            row=0,
            column=1,
            pady=3
        )

        tk.Label(
            info_frame,
            text="Course / Subject:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=3
        )

        course_entry = tk.Entry(
            info_frame,
            width=30
        )

        course_entry.grid(
            row=1,
            column=1,
            pady=3
        )

        tk.Label(
            info_frame,
            text="Borrow Date:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=3
        )

        borrow_date_entry = tk.Entry(
            info_frame,
            width=30
        )

        borrow_date_entry.insert(
            0,
            datetime.now().strftime(
                "%Y-%m-%d"
            )
        )

        borrow_date_entry.grid(
            row=2,
            column=1,
            pady=3
        )

        tk.Label(
            info_frame,
            text="Expected Return:"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=3
        )

        return_date_entry = tk.Entry(
            info_frame,
            width=30
        )

        return_date_entry.grid(
            row=3,
            column=1,
            pady=3
        )

        # ==================================================
        # SUBMIT
        # ==================================================

        def submit():

            student_number = (
                student_number_entry
                .get()
                .strip()
            )

            purpose = purpose_entry.get(
                "1.0",
                tk.END
            ).strip()

            course = (
                course_entry
                .get()
                .strip()
            )

            borrow_date = (
                borrow_date_entry
                .get()
                .strip()
            )

            return_date = (
                return_date_entry
                .get()
                .strip()
            )

            cart_items = []

            for item in cart_tree.get_children():

                values = cart_tree.item(
                    item,
                    "values"
                )

                cart_items.append({
                    "item_id": int(values[0]),
                    "quantity": int(values[2])
                })

            success, message = (
                self.controller.create_borrow_request(
                    self.username,
                    student_number,
                    cart_items,
                    purpose,
                    course,
                    borrow_date,
                    return_date
                )
            )

            if success:

                messagebox.showinfo(
                    "Borrow Request",
                    message,
                    parent=window
                )

                window.destroy()

                self.load_data()

            else:

                messagebox.showwarning(
                    "Borrow Request",
                    message,
                    parent=window
                )

        tk.Button(
            window,
            text="Submit Borrow Slip",
            command=submit,
            bg="#2196F3",
            fg="white",
            width=20,
            height=1
        ).pack(
            pady=8
        )

    # ======================================================
    # MY BORROWINGS
    # ======================================================

    def open_my_borrowings(self):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "My Borrowings"
        )

        window.geometry(
            "1150x550"
        )

        window.transient(
            self.root
        )

        tk.Label(
            window,
            text="My Borrowing Requests",
            font=("Arial", 16, "bold")
        ).pack(
            pady=15
        )

        table_frame = tk.Frame(
            window,
            padx=15
        )

        table_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "student",
            "components",
            "course",
            "purpose",
            "borrow",
            "return",
            "status"
        )

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "student": "Student No.",
            "components": "Components",
            "course": "Course",
            "purpose": "Purpose",
            "borrow": "Borrow Date",
            "return": "Expected Return",
            "status": "Status"
        }

        widths = {
            "id": 50,
            "student": 120,
            "components": 270,
            "course": 130,
            "purpose": 180,
            "borrow": 100,
            "return": 110,
            "status": 130
        }

        for column in columns:

            tree.heading(
                column,
                text=headings[column]
            )

            tree.column(
                column,
                width=widths[column],
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=tree.yview
        )

        tree.configure(
            yscrollcommand=scrollbar.set
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # --------------------------------------------------
        # STATUS COLORS
        # --------------------------------------------------

        tree.tag_configure(
            "PENDING",
            background="#FFF8E1"
        )

        tree.tag_configure(
            "APPROVED",
            background="#E8F5E9"
        )

        tree.tag_configure(
            "REJECTED",
            background="#FFEBEE"
        )

        tree.tag_configure(
            "RETURN_REQUESTED",
            background="#E3F2FD"
        )

        tree.tag_configure(
            "RETURNED",
            background="#F5F5F5"
        )

        def load_requests():

            for item in tree.get_children():

                tree.delete(item)

            rows = (
                self.controller
                .get_user_borrow_requests(
                    self.username
                )
            )

            for row in rows:

                components = "\n".join(
                    f"{name} x{quantity}"
                    for _, name, quantity
                    in row["items"]
                )

                tree.insert(
                    "",
                    "end",
                    values=(
                        row["request_id"],
                        row["student_number"],
                        components,
                        row["course"],
                        row["purpose"],
                        row["borrow_date"],
                        row["expected_return_date"],
                        row["status"]
                    ),
                    tags=(row["status"],)
                )

        def request_return():

            selection = tree.selection()

            if not selection:

                messagebox.showwarning(
                    "Return Hardware",
                    "Please select an approved borrowing."
                )

                return

            values = tree.item(
                selection[0],
                "values"
            )

            request_id = int(
                values[0]
            )

            status = values[7]

            if status != "APPROVED":

                messagebox.showwarning(
                    "Return Hardware",
                    "Only APPROVED borrowings "
                    "can be returned."
                )

                return

            confirm = messagebox.askyesno(
                "Request Return",
                f"Submit a return request for "
                f"Request #{request_id}?"
            )

            if not confirm:

                return

            success, message = (
                self.controller.request_return(
                    request_id,
                    self.username
                )
            )

            if success:

                messagebox.showinfo(
                    "Return Request",
                    message
                )

                load_requests()
                self.load_data()

            else:

                messagebox.showwarning(
                    "Return Request",
                    message
                )

        button_frame = tk.Frame(
            window,
            pady=10
        )

        button_frame.pack(
            fill="x"
        )

        tk.Button(
            button_frame,
            text="Request Return",
            command=request_return,
            width=18
        ).pack(
            side="left",
            padx=15
        )

        tk.Button(
            button_frame,
            text="Refresh",
            command=load_requests,
            width=12
        ).pack(
            side="left"
        )

        tk.Button(
            button_frame,
            text="Close",
            command=window.destroy,
            width=12
        ).pack(
            side="right",
            padx=15
        )

        load_requests()

    # ======================================================
    # PROFILE
    # ======================================================

    def open_profile(self):

        self.controller.app.show_profile(
            self.username,
            self.role
        )

    # ======================================================
    # LOGOUT
    # ======================================================

    def logout(self):

        self.controller.app.auth_controller.logout()