from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)

from functools import wraps
import os

from models.database import init_db
from controllers.auth_controller import AuthController
from controllers.inventory_controller import InventoryController
from controllers.reset_controller import ResetController


# ======================================================
# FLASK APPLICATION
# ======================================================

app = Flask(__name__)

app.secret_key = "campus-hardware-laboratory-secret-key"

import smtplib
import random
from email.mime.text import MIMEText

# --- BREVO SMTP CONFIGURATION ---
SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 2525
# TODO: Replace these with your actual Brevo SMTP Login and Master Password
SMTP_LOGIN = "bbf7d8001@smtp-brevo.com"       
SMTP_PASSWORD = "xsmtpsib-a7f39383ee51f0b832863464e30af73547a7e552f86b553f287d7cb64c14dd16-CkNrxLctz82BDvti"  

def send_otp_email(receiver_email, otp, intent):
    """Sends a 6-digit OTP using Brevo SMTP."""
    msg = MIMEText(f"Your {intent} One-Time Password (OTP) is: {otp}\n\nPlease enter this code to proceed. Do not share this code with anyone.")
    msg['Subject'] = f"Laboratory System - {intent} OTP"
    msg['From'] = "kylesuzetteiwarat22@gmail.com"  # Replace with your verified Brevo email
    msg['To'] = receiver_email
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_LOGIN, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False



# ======================================================
# WEB APPLICATION BRIDGE
# ======================================================

class WebAppBridge:

    def __init__(self):

        self.auth_controller = AuthController(self)

        self.inventory_controller = InventoryController(self)

        self.reset_controller = ResetController(self)


web = WebAppBridge()


# ======================================================
# LOGIN REQUIRED
# ======================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "username" not in session:

            flash(
                "Please log in first.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        return function(*args, **kwargs)

    return wrapper


# ======================================================
# ADMIN REQUIRED
# ======================================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "username" not in session:

            flash(
                "Please log in first.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        if session.get("role") != "ADMIN":

            flash(
                "Administrator access required.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return function(*args, **kwargs)

    return wrapper


# ======================================================
# HOME
# ======================================================

@app.route("/")
def index():

    if "username" in session:

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# ======================================================
# LOGIN
# ======================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            flash(
                "Please enter your username and password.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        success, result = web.auth_controller.login(
            username,
            password
        )

        if success:

            session["username"] = username

            session["role"] = result

            flash(
                "Login successful.",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            result,
            "danger"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "login.html"
    )


# ======================================================
# REGISTER
# ======================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "USER").strip().upper()

    if not username or not email or not password:
        flash("All registration fields are required.", "danger")
        return redirect(url_for("register"))

    # Generate OTP and save to session
    otp = str(random.randint(100000, 999999))
    session['pending_user'] = {'username': username, 'email': email, 'password': password, 'role': role, 'otp': otp}
    
    if send_otp_email(email, otp, intent="Account Registration"):
        flash("We sent a 6-digit code to your email. Please verify.", "info")
        return redirect(url_for("verify_otp", action="register"))
    else:
        flash("Failed to send OTP email. Please try again.", "danger")
        return redirect(url_for("register"))



# ======================================================
# PASSWORD RESET REQUEST
# ======================================================

@app.route("/reset-request", methods=["GET", "POST"])
def reset_request():
    if request.method == "GET":
        return render_template("reset.html")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    if not username or not email or not new_password or not confirm_password:
        flash("All reset fields are required.", "danger")
        return redirect(url_for("reset_request"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("reset_request"))

    # Generate OTP and save to session
    otp = str(random.randint(100000, 999999))
    session['pending_reset'] = {'username': username, 'email': email, 'new_password': new_password, 'otp': otp}
    
    if send_otp_email(email, otp, intent="Password Reset"):
        flash("We sent a 6-digit code to your email. Please verify.", "info")
        return redirect(url_for("verify_otp", action="reset"))
    else:
        flash("Failed to send OTP email. Please try again.", "danger")
        return redirect(url_for("reset_request"))


@app.route("/verify-otp/<action>", methods=["GET", "POST"])
def verify_otp(action):

    # Determine which session data to use
    session_key = (
        'pending_user'
        if action == "register"
        else 'pending_reset'
    )

    if session_key not in session:

        flash(
            "Session expired. Please try again.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        user_otp = request.form.get(
            "otp_code",
            ""
        ).strip()

        data = session[session_key]

        if user_otp == data['otp']:

            # ==========================================
            # REGISTER
            # ==========================================
            if action == "register":

                ok, msg = web.auth_controller.register(
                    data['username'],
                    data['email'],
                    data['password'],
                    data['role']
                )

                session.pop(
                    session_key,
                    None
                )

                flash(
                    "Account successfully verified and created!"
                    if ok
                    else msg,
                    "success" if ok else "danger"
                )

                if ok:
                    return redirect(
                        url_for("login")
                    )

                return redirect(
                    url_for("register")
                )

            # ==========================================
            # RESET / UNLOCK PASSWORD
            # ==========================================
            elif action == "reset":

                ok, msg = (
                    web.reset_controller
                    .submit_request(
                        data['email']
                    )
                )

                session.pop(
                    session_key,
                    None
                )

                flash(
                    "Email verified! Your password reset request has been submitted."
                    if ok
                    else msg,
                    "success" if ok else "danger"
                )

                return redirect(
                    url_for("login")
                )

        else:

            flash(
                "Invalid OTP code. Try again.",
                "danger"
            )

    return render_template(
        "otp_verify.html",
        action_url=url_for(
            "verify_otp",
            action=action
        )
    )

# ======================================================
# DASHBOARD
# ======================================================

@app.route("/dashboard")
@login_required
def dashboard():

    username = session.get(
        "username"
    )

    role = session.get(
        "role"
    )

    # --------------------------------------------------
    # SEARCH AND FILTER
    # --------------------------------------------------

    search = request.args.get(
        "search",
        ""
    ).strip()

    category = request.args.get(
        "category",
        "All Categories"
    ).strip()

    status = request.args.get(
        "status",
        "All Statuses"
    ).strip()

    if not category:

        category = "All Categories"

    if not status:

        status = "All Statuses"


    # --------------------------------------------------
    # HARDWARE
    # --------------------------------------------------

    if (
        search
        or category != "All Categories"
        or status != "All Statuses"
    ):

        items = (
            web.inventory_controller.search_hardware(
                search,
                category,
                status
            )
        )

    else:

        items = (
            web.inventory_controller.get_all_hardware()
        )


    categories = (
        web.inventory_controller.get_categories()
    )


    # --------------------------------------------------
    # UPDATE HARDWARE
    # --------------------------------------------------

    edit_id = request.args.get(
        "edit_id",
        ""
    ).strip()

    edit_item = None

    if edit_id:

        try:

            edit_id = int(
                edit_id
            )

            for item in items:

                if item[0] == edit_id:

                    edit_item = item

                    break

        except ValueError:

            edit_item = None


    # --------------------------------------------------
    # TOTAL STOCKS
    # --------------------------------------------------

    total_stocks = sum(
        item[3]
        for item in items
    )


    # --------------------------------------------------
    # BORROWING INFORMATION
    # --------------------------------------------------

    history = (
        web.inventory_controller
        .get_user_borrow_requests(username)
    )


    all_loans = (
        web.inventory_controller
        .get_borrow_requests("APPROVED")
    )

    admin_borrow_history = []
    if role == "ADMIN":
        admin_borrow_history = (
            web.inventory_controller
            .get_borrow_requests()
        )

    pending_borrows = (
        web.inventory_controller
        .get_borrow_requests("PENDING")
    )


    pending_returns = (
        web.inventory_controller
        .get_borrow_requests("RETURN_REQUESTED")
    )


    # --------------------------------------------------
    # USER INFORMATION
    # --------------------------------------------------

    user_info = (
        web.auth_controller
        .get_user_info(username)
    )


    # --------------------------------------------------
    # ACTIVE BORROWED ITEMS
    #
    # IMPORTANT:
    # get_user_borrow_requests() returns dictionaries.
    # Therefore, use request_item.get("status")
    # instead of request_item[6].
    # --------------------------------------------------

    active_loans = []

    for request_item in history:

        if request_item.get("status") == "APPROVED":

            active_loans.append(
                request_item
            )


    # --------------------------------------------------
    # PENDING BORROW REQUESTS
    # --------------------------------------------------

    pending_borrow_requests = []

    if role == "USER":

        for request_item in history:

            if request_item.get("status") == "PENDING":

                pending_borrow_requests.append(
                    request_item
                )

    else:

        pending_borrow_requests = pending_borrows


    # --------------------------------------------------
    # PASSWORD RESET REQUESTS
    # --------------------------------------------------

    pending_resets = []

    if role == "ADMIN":

        pending_resets = (
            web.reset_controller.get_requests()
        )


    # --------------------------------------------------
    # SEND DATA TO DASHBOARD
    # --------------------------------------------------

    return render_template(
        "dashboard.html",

        hardware=items,

        categories=categories,

        search_text=search,

        selected_category=category,

        selected_status=status,

        total_stocks=total_stocks,

        active_loans=active_loans,

        history=history,

        pending_returns=pending_returns,

        pending_borrows=pending_borrows,

        pending_borrow_requests=pending_borrow_requests,

        all_loans=all_loans,
        
        admin_borrow_history=admin_borrow_history,

        pending_resets=pending_resets,

        user_info=user_info,

        edit_item=edit_item
    )


# ======================================================
# BORROW HARDWARE
# ======================================================

@app.route(
    "/borrow",
    methods=["POST"]
)
@login_required
def borrow():

    username = session.get(
        "username"
    )

    student_number = request.form.get(
        "student_number",
        ""
    ).strip()

    item_id = request.form.get(
        "item_id",
        ""
    ).strip()

    quantity_text = request.form.get(
        "quantity",
        ""
    ).strip()

    course = request.form.get(
        "course",
        ""
    ).strip()

    borrow_date = request.form.get(
        "borrow_date",
        ""
    ).strip()

    expected_return_date = request.form.get(
        "expected_return_date",
        ""
    ).strip()

    purpose = request.form.get(
        "purpose",
        ""
    ).strip()


    # --------------------------------------------------
    # VALIDATE QUANTITY
    # --------------------------------------------------

    try:

        quantity = int(
            quantity_text
        )

    except ValueError:

        flash(
            "Quantity must be a valid number.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    if quantity < 1:

        flash(
            "Quantity must be at least 1.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # VALIDATE ITEM ID
    # --------------------------------------------------

    try:

        item_id = int(
            item_id
        )

    except ValueError:

        flash(
            "Please select a valid hardware item.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # CREATE ITEM LIST
    # --------------------------------------------------

    items = [
        {
            "item_id": item_id,
            "quantity": quantity
        }
    ]


    # --------------------------------------------------
    # CREATE BORROW REQUEST
    # --------------------------------------------------

    success, message = (
        web.inventory_controller
        .create_borrow_request(
            username,
            student_number,
            items,
            purpose,
            course,
            borrow_date,
            expected_return_date
        )
    )


    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# ======================================================
# REQUEST RETURN
# ======================================================

@app.route(
    "/return-request",
    methods=["POST"]
)
@login_required
def return_request():

    username = session.get(
        "username"
    )

    request_id = request.form.get(
        "request_id",
        ""
    ).strip()


    # --------------------------------------------------
    # VALIDATE REQUEST ID
    # --------------------------------------------------

    try:

        request_id = int(
            request_id
        )

    except ValueError:

        flash(
            "Invalid borrow request ID.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # REQUEST RETURN
    # --------------------------------------------------

    success, message = (
        web.inventory_controller
        .request_return(
            request_id,
            username
        )
    )


    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# ======================================================
# CHANGE PASSWORD
# ======================================================

@app.route(
    "/change-password",
    methods=["POST"]
)
@login_required
def change_password():

    username = session.get(
        "username"
    )

    current_password = request.form.get(
        "current_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    # --------------------------------------------------
    # CHECK NEW PASSWORD
    # --------------------------------------------------

    if new_password != confirm_password:

        flash(
            "New passwords do not match.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # CHANGE PASSWORD
    # --------------------------------------------------

    success, message = (
        web.auth_controller.change_password(
            username,
            current_password,
            new_password
        )
    )


    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# ======================================================
# ADMIN - ADD HARDWARE
# ======================================================

@app.route(
    "/admin/add",
    methods=["POST"]
)
@admin_required
def admin_add():

    name = request.form.get(
        "item_name",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    quantity_text = request.form.get(
        "quantity",
        ""
    ).strip()

    price_text = request.form.get(
        "unit_price",
        ""
    ).strip()


    # --------------------------------------------------
    # VALIDATE NUMBERS
    # --------------------------------------------------

    try:

        quantity = int(
            quantity_text
        )

        unit_price = float(
            price_text
        )

    except ValueError:

        flash(
            "Quantity must be an integer and unit price must be numeric.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # VALIDATE QUANTITY
    # --------------------------------------------------

    if quantity < 1:

        flash(
            "Quantity must be at least 1.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # VALIDATE PRICE
    # --------------------------------------------------

    if unit_price < 0:

        flash(
            "Unit price cannot be negative.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # VALIDATE TEXT FIELDS
    # --------------------------------------------------

    if not name or not category:

        flash(
            "Hardware name and category are required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # ADD HARDWARE
    # --------------------------------------------------

    ok, msg = (
        web.inventory_controller
        .add_hardware(
            name,
            category,
            quantity,
            unit_price
        )
    )


    flash(
        msg,
        "success" if ok else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# ======================================================
# ADMIN - UPDATE HARDWARE
# ======================================================

@app.route(
    "/admin/update",
    methods=["POST"]
)
@admin_required
def admin_update():

    item_id = request.form.get(
        "item_id",
        ""
    ).strip()

    name = request.form.get(
        "item_name",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    quantity_text = request.form.get(
        "quantity",
        ""
    ).strip()

    available_text = request.form.get(
        "available_quantity",
        ""
    ).strip()

    price_text = request.form.get(
        "unit_price",
        ""
    ).strip()


    # --------------------------------------------------
    # VALIDATE ITEM ID
    # --------------------------------------------------

    try:

        item_id = int(
            item_id
        )

    except ValueError:

        flash(
            "Invalid hardware ID.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # VALIDATE TEXT FIELDS
    # --------------------------------------------------

    if not name or not category:

        flash(
            "Hardware name and category are required.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard",
                edit_id=item_id
            )
        )


    # --------------------------------------------------
    # VALIDATE NUMBERS
    # --------------------------------------------------

    try:

        quantity = int(
            quantity_text
        )

        available_quantity = int(
            available_text
        )

        unit_price = float(
            price_text
        )

    except ValueError:

        flash(
            "Quantity and available stock must be whole numbers and unit price must be numeric.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard",
                edit_id=item_id
            )
        )


    # --------------------------------------------------
    # VALIDATE QUANTITY
    # --------------------------------------------------

    if quantity < 1:

        flash(
            "Quantity must be at least 1.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard",
                edit_id=item_id
            )
        )


    # --------------------------------------------------
    # VALIDATE AVAILABLE STOCK
    # --------------------------------------------------

    if available_quantity < 0:

        flash(
            "Available stock cannot be negative.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard",
                edit_id=item_id
            )
        )


    if available_quantity > quantity:

        flash(
            "Available stock cannot be greater than total quantity.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard",
                edit_id=item_id
            )
        )


    # --------------------------------------------------
    # VALIDATE PRICE
    # --------------------------------------------------

    if unit_price < 0:

        flash(
            "Unit price cannot be negative.",
            "danger"
        )

        return redirect(
            url_for(
                "dashboard",
                edit_id=item_id
            )
        )


    # --------------------------------------------------
    # UPDATE HARDWARE
    # --------------------------------------------------

    success, message = (
        web.inventory_controller
        .update_hardware(
            item_id,
            name,
            category,
            quantity,
            available_quantity,
            unit_price
        )
    )


    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# ======================================================
# ADMIN - DELETE HARDWARE
# ======================================================

@app.route(
    "/admin/delete",
    methods=["POST"]
)
@admin_required
def admin_delete():

    item_id = request.form.get(
        "item_id",
        ""
    ).strip()


    # --------------------------------------------------
    # VALIDATE ITEM ID
    # --------------------------------------------------

    try:

        item_id = int(
            item_id
        )

    except ValueError:

        flash(
            "Invalid hardware ID.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # DELETE HARDWARE
    # --------------------------------------------------

    success, message = (
        web.inventory_controller
        .delete_hardware(
            item_id
        )
    )


    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# ======================================================
# ADMIN - BORROW APPROVE / REJECT
# ======================================================

@app.route(
    "/admin/borrow-action",
    methods=["POST"]
)
@admin_required
def admin_borrow_action():

    request_id = request.form.get(
        "request_id",
        ""
    ).strip()

    action = request.form.get(
        "action",
        ""
    ).strip()

    admin_username = session.get(
        "username"
    )


    # --------------------------------------------------
    # VALIDATE REQUEST ID
    # --------------------------------------------------

    try:

        request_id = int(
            request_id
        )

    except ValueError:

        flash(
            "Invalid borrow request ID.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # VALIDATE ACTION
    # --------------------------------------------------

    if action not in (
        "APPROVE",
        "REJECT"
    ):

        flash(
            "Invalid approval action.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # APPROVE OR REJECT BORROW REQUEST
    # --------------------------------------------------

    success, message = (
        web.inventory_controller
        .review_borrow_request(
            request_id,
            action,
            admin_username
        )
    )


    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# ======================================================
# ADMIN - RETURN APPROVE / REJECT
# ======================================================

@app.route(
    "/admin/return-action",
    methods=["POST"]
)
@admin_required
def admin_return_action():

    request_id = request.form.get(
        "request_id",
        ""
    ).strip()

    action = request.form.get(
        "action",
        ""
    ).strip()

    admin_username = session.get(
        "username"
    )


    # --------------------------------------------------
    # VALIDATE REQUEST ID
    # --------------------------------------------------

    try:

        request_id = int(
            request_id
        )

    except ValueError:

        flash(
            "Invalid return request ID.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # APPROVE RETURN
    # --------------------------------------------------

    if action == "APPROVE":

        success, message = (
            web.inventory_controller
            .confirm_return(
                request_id,
                admin_username
            )
        )


    # --------------------------------------------------
    # REJECT RETURN
    # --------------------------------------------------

    elif action == "REJECT":

        success, message = (
            web.inventory_controller
            .reject_return(
                request_id,
                admin_username
            )
        )


    # --------------------------------------------------
    # INVALID ACTION
    # --------------------------------------------------

    else:

        flash(
            "Invalid return action.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # SHOW RESULT
    # --------------------------------------------------

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# ======================================================
# ADMIN - PASSWORD RESET APPROVE / REJECT
# ======================================================

@app.route(
    "/admin/reset-action",
    methods=["POST"]
)
@admin_required
def admin_reset_action():

    request_id = request.form.get(
        "request_id",
        ""
    ).strip()

    action = request.form.get(
        "action",
        ""
    ).strip()

    admin_username = session.get(
        "username"
    )


    # --------------------------------------------------
    # VALIDATE REQUEST ID
    # --------------------------------------------------

    try:

        request_id = int(
            request_id
        )

    except ValueError:

        flash(
            "Invalid reset request ID.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # REVIEW RESET REQUEST
    # --------------------------------------------------

    success, message = (
        web.reset_controller
        .review_request(
            request_id,
            action,
            admin_username
        )
    )


    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# ======================================================
# ADMIN - EXPORT CSV
# ======================================================

@app.route("/export")
@admin_required
def export_csv():

    filename = "inventory_report.csv"


    # --------------------------------------------------
    # EXPORT INVENTORY
    # --------------------------------------------------

    success, message = (
        web.inventory_controller
        .export_csv(
            filename
        )
    )


    if not success:

        flash(
            message,
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------
    # SEND CSV FILE
    # --------------------------------------------------

    return send_file(
        os.path.abspath(
            filename
        ),
        as_attachment=True,
        download_name=filename
    )


# ======================================================
# LOGOUT
# ======================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# ======================================================
# RUN FLASK APPLICATION
# ======================================================

if __name__ == "__main__":

    # Initialize the existing database.
    init_db()

    print()
    print("=" * 58)
    print(" CAMPUS HARDWARE INVENTORY - WEB PORTAL")
    print("=" * 58)
    print()

    print(" Open Google Chrome and go to:")
    print(" http://127.0.0.1:5000")

    print()
    print(" Press CTRL+C to stop the server.")
    print("=" * 58)
    print()

    # Start Flask.
    app.run(debug=True)
