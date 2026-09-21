# DESKTOP ONLY — retained for the original desktop version
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    TKINTER_AVAILABLE = True

except ImportError:
    tk = None
    ttk = None
    messagebox = None
    filedialog = None
    TKINTER_AVAILABLE = False


class AdminView:

    def __init__(
        self,
        root,
        reset_controller,
        admin_username,
        inventory_controller
    ):

        self.root = root
        self.reset = reset_controller
        self.admin_username = admin_username
        self.inventory = inventory_controller

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
            text="Hardware Laboratory Admin Panel",
            font=("Arial", 20, "bold")
        ).pack(side="left")

        right = tk.Frame(header)
        right.pack(side="right")

        tk.Label(
            right,
            text=f"Administrator: {self.admin_username}",
            fg="gray"
        ).pack(
            side="left",
            padx=10
        )

        tk.Button(
            right,
            text="My Profile & Security",
            command=self.open_profile
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            right,
            text="Logout",
            command=self.logout
        ).pack(
            side="left",
            padx=5
        )

        self.notebook = ttk.Notebook(
            self.root
        )

        self.notebook.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        self.build_hardware_tab()
        self.build_borrow_tab()
        self.build_account_tab()

    # ======================================================
    # HARDWARE TAB
    # ======================================================

    def build_hardware_tab(self):

        tab = tk.Frame(
            self.notebook
        )

        self.notebook.add(
            tab,
            text="Hardware Inventory"
        )

        search_frame = tk.Frame(
            tab,
            padx=10,
            pady=10
        )

        search_frame.pack(
            fill="x"
        )

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

        self.category_combo.pack(
            side="left"
        )

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

        self.status_combo.set(
            "All Statuses"
        )

        self.status_combo.pack(
            side="left"
        )

        self.status_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.search_hardware()
        )

        # --------------------------------------------------
        # TABLE
        # --------------------------------------------------

        table_frame = tk.Frame(
            tab,
            padx=10
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
            "id": 50,
            "name": 190,
            "category": 140,
            "total": 85,
            "available": 90,
            "price": 100,
            "status": 110
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
        # PALE COLORS
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
        # FORM
        # --------------------------------------------------

        form = tk.LabelFrame(
            tab,
            text="Hardware Management",
            padx=10,
            pady=10
        )

        form.pack(
            fill="x",
            padx=10,
            pady=10
        )

        tk.Label(
            form,
            text="Item Name:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.name_entry = tk.Entry(
            form,
            width=25
        )

        self.name_entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        tk.Label(
            form,
            text="Category:"
        ).grid(
            row=0,
            column=2,
            sticky="w",
            padx=5,
            pady=5
        )

        self.category_entry = tk.Entry(
            form,
            width=20
        )

        self.category_entry.grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        tk.Label(
            form,
            text="Total Quantity:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.quantity_entry = tk.Entry(
            form,
            width=25
        )

        self.quantity_entry.grid(
            row=1,
            column=1,
            padx=5,
            pady=5
        )

        tk.Label(
            form,
            text="Unit Price:"
        ).grid(
            row=1,
            column=2,
            sticky="w",
            padx=5,
            pady=5
        )

        self.price_entry = tk.Entry(
            form,
            width=20
        )

        self.price_entry.grid(
            row=1,
            column=3,
            padx=5,
            pady=5
        )

        button_frame = tk.Frame(form)

        button_frame.grid(
            row=0,
            column=4,
            rowspan=2,
            padx=15
        )

        tk.Button(
            button_frame,
            text="Add Hardware",
            command=self.add_hardware,
            width=15
        ).pack(pady=2)

        tk.Button(
            button_frame,
            text="Update Selected",
            command=self.update_hardware,
            width=15
        ).pack(pady=2)

        tk.Button(
            button_frame,
            text="Delete Selected",
            command=self.delete_hardware,
            width=15
        ).pack(pady=2)

        tk.Button(
            button_frame,
            text="Export CSV",
            command=self.export_csv,
            width=15
        ).pack(pady=2)

        self.load_categories()
        self.load_hardware()

    # ======================================================
    # HARDWARE FUNCTIONS
    # ======================================================

    def load_categories(self):

        categories = self.inventory.get_categories()

        self.category_combo["values"] = (
            ["All Categories"] + categories
        )

        self.category_combo.set(
            "All Categories"
        )

    def load_hardware(self, rows=None):

        if rows is None:

            rows = self.inventory.get_all_hardware()

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

        self.name_entry.delete(
            0,
            tk.END
        )

        self.name_entry.insert(
            0,
            values[1]
        )

        self.category_entry.delete(
            0,
            tk.END
        )

        self.category_entry.insert(
            0,
            values[2]
        )

        self.quantity_entry.delete(
            0,
            tk.END
        )

        self.quantity_entry.insert(
            0,
            values[3]
        )

        self.price_entry.delete(
            0,
            tk.END
        )

        price = (
            values[5]
            .replace("₱", "")
            .replace(",", "")
        )

        self.price_entry.insert(
            0,
            price
        )

    def search_hardware(self):

        rows = self.inventory.search_hardware(
            self.search_entry.get(),
            self.category_combo.get(),
            self.status_combo.get()
        )

        self.load_hardware(rows)

    def add_hardware(self):

        success, message = (
            self.inventory.add_hardware(
                self.name_entry.get(),
                self.category_entry.get(),
                self.quantity_entry.get(),
                self.price_entry.get()
            )
        )

        if success:

            messagebox.showinfo(
                "Hardware",
                message
            )

            self.clear_form()
            self.load_categories()
            self.load_hardware()

        else:

            messagebox.showwarning(
                "Hardware",
                message
            )

    def update_hardware(self):

        if not self.selected_hardware_id:

            messagebox.showwarning(
                "Update Hardware",
                "Please select a hardware item first."
            )

            return

        success, message = (
            self.inventory.update_hardware(
                self.selected_hardware_id,
                self.quantity_entry.get(),
                self.price_entry.get()
            )
        )

        if success:

            messagebox.showinfo(
                "Update Hardware",
                message
            )

            self.clear_form()
            self.load_hardware()

        else:

            messagebox.showwarning(
                "Update Hardware",
                message
            )

    def delete_hardware(self):

        if not self.selected_hardware_id:

            messagebox.showwarning(
                "Delete Hardware",
                "Please select a hardware item first."
            )

            return

        selection = self.hardware_tree.selection()

        if not selection:

            return

        values = self.hardware_tree.item(
            selection[0],
            "values"
        )

        confirm = messagebox.askyesno(
            "Delete Hardware",
            f"Delete '{values[1]}'?"
        )

        if not confirm:

            return

        success, message = (
            self.inventory.delete_hardware(
                self.selected_hardware_id
            )
        )

        if success:

            messagebox.showinfo(
                "Delete Hardware",
                message
            )

            self.clear_form()
            self.load_hardware()
            self.load_categories()

        else:

            messagebox.showwarning(
                "Delete Hardware",
                message
            )

    def clear_form(self):

        self.selected_hardware_id = None

        for entry in (
            self.name_entry,
            self.category_entry,
            self.quantity_entry,
            self.price_entry
        ):

            entry.delete(
                0,
                tk.END
            )

    def export_csv(self):

        filename = filedialog.asksaveasfilename(
            title="Export Inventory",
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv")
            ]
        )

        if not filename:

            return

        success, message = (
            self.inventory.export_csv(
                filename
            )
        )

        if success:

            messagebox.showinfo(
                "Export",
                message
            )

        else:

            messagebox.showerror(
                "Export",
                message
            )

    # ======================================================
    # BORROW REQUESTS
    # ======================================================

    def build_borrow_tab(self):

        tab = tk.Frame(
            self.notebook
        )

        self.notebook.add(
            tab,
            text="Borrow Requests"
        )

        tk.Label(
            tab,
            text="Hardware Borrow Requests",
            font=("Arial", 14, "bold")
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 3)
        )

        tk.Label(
            tab,
            text=(
                "Review and manage laboratory hardware "
                "borrowing slips."
            ),
            fg="gray"
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 10)
        )

        table_frame = tk.Frame(
            tab,
            padx=10
        )

        table_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "user",
            "student",
            "components",
            "course",
            "purpose",
            "borrow",
            "return",
            "status"
        )

        self.borrow_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "user": "User",
            "student": "Student No.",
            "components": "Components",
            "course": "Course",
            "purpose": "Purpose",
            "borrow": "Borrow Date",
            "return": "Expected Return",
            "status": "Status"
        }

        widths = {
            "id": 45,
            "user": 90,
            "student": 110,
            "components": 350,
            "course": 110,
            "purpose": 170,
            "borrow": 100,
            "return": 110,
            "status": 120
        }

        for column in columns:

            self.borrow_tree.heading(
                column,
                text=headings[column]
            )

            self.borrow_tree.column(
                column,
                width=widths[column],
                anchor="center"
            )

        yscroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.borrow_tree.yview
        )

        xscroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.borrow_tree.xview
        )

        self.borrow_tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        self.borrow_tree.pack(
            side="top",
            fill="both",
            expand=True
        )

        yscroll.pack(
            side="right",
            fill="y"
        )

        xscroll.pack(
            side="bottom",
            fill="x"
        )

        # --------------------------------------------------
        # STATUS COLORS
        # --------------------------------------------------

        self.borrow_tree.tag_configure(
            "PENDING",
            background="#FFF8E1"
        )

        self.borrow_tree.tag_configure(
            "APPROVED",
            background="#E8F5E9"
        )

        self.borrow_tree.tag_configure(
            "REJECTED",
            background="#FFEBEE"
        )

        self.borrow_tree.tag_configure(
            "RETURN_REQUESTED",
            background="#E3F2FD"
        )

        self.borrow_tree.tag_configure(
            "RETURNED",
            background="#F5F5F5"
        )

        # --------------------------------------------------
        # BUTTONS
        # --------------------------------------------------

        button_frame = tk.Frame(
            tab,
            pady=10
        )

        button_frame.pack(
            fill="x"
        )

        tk.Button(
            button_frame,
            text="Approve Request",
            command=lambda:
                self.review_borrow("approve"),
            bg="#4CAF50",
            fg="white",
            width=18
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Reject Request",
            command=lambda:
                self.review_borrow("reject"),
            bg="#f44336",
            fg="white",
            width=18
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Confirm Return",
            command=self.confirm_return,
            width=18
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Refresh",
            command=self.load_borrow_requests,
            width=12
        ).pack(
            side="right",
            padx=5
        )

        self.load_borrow_requests()

    def load_borrow_requests(self):

        for item in self.borrow_tree.get_children():

            self.borrow_tree.delete(item)

        rows = self.inventory.get_borrow_requests()

        for row in rows:

            components = " • ".join(
                f"{name} x{quantity}"
                for _, name, quantity
                in row["items"]
            )

            self.borrow_tree.insert(
                "",
                "end",
                values=(
                    row["request_id"],
                    row["username"],
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

    def review_borrow(self, action):

        selection = self.borrow_tree.selection()

        if not selection:

            messagebox.showwarning(
                "Borrow Request",
                "Please select a request."
            )

            return

        values = self.borrow_tree.item(
            selection[0],
            "values"
        )

        request_id = int(
            values[0]
        )

        status = values[8]

        if status != "PENDING":

            messagebox.showwarning(
                "Borrow Request",
                f"This request is already {status}."
            )

            return

        confirm = messagebox.askyesno(
            "Borrow Request",
            f"Are you sure you want to "
            f"{action} Request #{request_id}?"
        )

        if not confirm:

            return

        success, message = (
            self.inventory.review_borrow_request(
                request_id,
                action,
                self.admin_username
            )
        )

        if success:

            messagebox.showinfo(
                "Borrow Request",
                message
            )

            self.load_borrow_requests()
            self.load_hardware()

        else:

            messagebox.showwarning(
                "Borrow Request",
                message
            )

    def confirm_return(self):

        selection = self.borrow_tree.selection()

        if not selection:

            messagebox.showwarning(
                "Return",
                "Please select a borrowing."
            )

            return

        values = self.borrow_tree.item(
            selection[0],
            "values"
        )

        request_id = int(
            values[0]
        )

        status = values[8]

        if status != "RETURN_REQUESTED":

            messagebox.showwarning(
                "Return",
                "Only RETURN_REQUESTED borrowings "
                "can be confirmed."
            )

            return

        confirm = messagebox.askyesno(
            "Confirm Return",
            f"Confirm the return of "
            f"Request #{request_id}?"
        )

        if not confirm:

            return

        success, message = (
            self.inventory.confirm_return(
                request_id,
                self.admin_username
            )
        )

        if success:

            messagebox.showinfo(
                "Return",
                message
            )

            self.load_borrow_requests()
            self.load_hardware()

        else:

            messagebox.showwarning(
                "Return",
                message
            )

    # ======================================================
    # ACCOUNT REQUESTS
    # ======================================================

    def build_account_tab(self):

        tab = tk.Frame(
            self.notebook
        )

        self.notebook.add(
            tab,
            text="Account Requests"
        )

        tk.Label(
            tab,
            text="Password Reset / Unlock Requests",
            font=("Arial", 14, "bold")
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 10)
        )

        table_frame = tk.Frame(
            tab,
            padx=15
        )

        table_frame.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "username",
            "email",
            "requested",
            "status"
        )

        self.request_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        headings = {
            "id": "ID",
            "username": "Username",
            "email": "Email",
            "requested": "Requested",
            "status": "Status"
        }

        widths = {
            "id": 60,
            "username": 150,
            "email": 250,
            "requested": 180,
            "status": 120
        }

        for column in columns:

            self.request_tree.heading(
                column,
                text=headings[column]
            )

            self.request_tree.column(
                column,
                width=widths[column],
                anchor="center"
            )

        self.request_tree.pack(
            fill="both",
            expand=True
        )

        button_frame = tk.Frame(
            tab,
            pady=10
        )

        button_frame.pack(
            fill="x"
        )

        tk.Button(
            button_frame,
            text="Approve",
            command=lambda:
                self.review_account("approve"),
            bg="#4CAF50",
            fg="white",
            width=15
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Reject",
            command=lambda:
                self.review_account("reject"),
            bg="#f44336",
            fg="white",
            width=15
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Refresh",
            command=self.load_requests,
            width=12
        ).pack(
            side="right"
        )

        self.load_requests()

    def load_requests(self):

        for item in self.request_tree.get_children():

            self.request_tree.delete(item)

        rows = self.reset.get_requests()

        for row in rows:

            self.request_tree.insert(
                "",
                "end",
                values=(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4]
                )
            )

    def review_account(self, action):

        selection = self.request_tree.selection()

        if not selection:

            messagebox.showwarning(
                "Account Request",
                "Please select an account request."
            )

            return

        values = self.request_tree.item(
            selection[0],
            "values"
        )

        request_id = int(
            values[0]
        )

        status = values[4]

        if status != "PENDING":

            messagebox.showwarning(
                "Account Request",
                f"This request is already {status}."
            )

            return

        confirm = messagebox.askyesno(
            "Account Request",
            f"Are you sure you want to "
            f"{action} Request #{request_id}?"
        )

        if not confirm:

            return

        success, message = (
            self.reset.review_request(
                request_id,
                action,
                self.admin_username
            )
        )

        if success:

            messagebox.showinfo(
                "Account Request",
                message
            )

            self.load_requests()

        else:

            messagebox.showwarning(
                "Account Request",
                message
            )

    # ======================================================
    # PROFILE
    # ======================================================

    def open_profile(self):

        self.reset.app.show_profile(
            self.admin_username,
            "ADMIN"
        )

    # ======================================================
    # LOGOUT
    # ======================================================

    def logout(self):

        self.reset.app.auth_controller.logout()