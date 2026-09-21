import sqlite3
import bcrypt
import logging
import re

from models.database import get_connection


# Keep track of the current application.
# This allows older views that call logout_user()
# to continue working.
_current_app = None


class AuthController:

    def __init__(self, app):

        global _current_app

        self.app = app

        _current_app = app

    # ======================================================
    # PASSWORD VALIDATION
    # ======================================================

    def validate_password(
        self,
        password
    ):

        if len(password) < 8:

            return False, (
                "Password must be at least 8 characters."
            )

        if not any(
            c.isupper()
            for c in password
        ):

            return False, (
                "Password must contain an uppercase letter."
            )

        if not any(
            c.isdigit()
            for c in password
        ):

            return False, (
                "Password must contain a number."
            )

        if not any(
            c in "@#$%^&*"
            for c in password
        ):

            return False, (
                "Password must contain a special character."
            )

        return True, (
            "Password is valid."
        )

    # ======================================================
    # EMAIL VALIDATION
    # ======================================================

    def validate_email(
        self,
        email
    ):

        pattern = (
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        )

        return bool(
            re.match(
                pattern,
                email
            )
        )

    # ======================================================
    # REGISTER
    # ======================================================

    def register(
        self,
        username,
        email,
        password,
        role
    ):

        username = username.strip()
        email = email.strip()
        role = role.strip().upper()

        if (
            not username
            or not email
            or not password
            or not role
        ):

            return False, (
                "Please complete all fields."
            )

        if len(username) < 3:

            return False, (
                "Username must be at least 3 characters."
            )

        if not self.validate_email(email):

            return False, (
                "Please enter a valid email address."
            )

        valid, message = (
            self.validate_password(
                password
            )
        )

        if not valid:

            return False, message

        conn = get_connection()
        cursor = conn.cursor()

        try:

            # Check email

            cursor.execute("""
                SELECT id
                FROM users
                WHERE LOWER(email) = LOWER(?)
            """, (email,))

            if cursor.fetchone():

                return False, (
                    "This email address is already registered."
                )

            # Check username

            cursor.execute("""
                SELECT id
                FROM users
                WHERE LOWER(username) = LOWER(?)
            """, (username,))

            if cursor.fetchone():

                return False, (
                    "This username is already taken."
                )

            # Hash password

            password_hash = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            # Insert user

            cursor.execute("""
                INSERT INTO users
                (
                    username,
                    password_hash,
                    email,
                    role,
                    failed_attempts,
                    locked_until,
                    is_locked
                )
                VALUES (?, ?, ?, ?, 0, 0, 0)
            """, (
                username,
                password_hash,
                email,
                role
            ))

            conn.commit()

            logging.info(
                f"User registered: "
                f"{username} | role={role}"
            )

            return True, (
                "Registration successful."
            )

        except sqlite3.IntegrityError:

            return False, (
                "Username or email already exists."
            )

        finally:

            conn.close()

    # ======================================================
    # LOGIN
    # ======================================================

    def login(
        self,
        username,
        password
    ):

        username = username.strip()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                password_hash,
                failed_attempts,
                is_locked,
                role
            FROM users
            WHERE LOWER(username) = LOWER(?)
        """, (username,))

        user = cursor.fetchone()

        if not user:

            conn.close()

            return False, (
                "Invalid username or password."
            )

        (
            password_hash,
            failed_attempts,
            is_locked,
            role
        ) = user

        # Check locked account

        if is_locked:

            conn.close()

            return False, (
                "This account is locked.\n\n"
                "Please use Reset / Unlock Password."
            )

        # Check password

        try:

            correct = bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8")
            )

        except ValueError:

            correct = False

        # Successful login

        if correct:

            cursor.execute("""
                UPDATE users
                SET failed_attempts = 0
                WHERE LOWER(username) = LOWER(?)
            """, (username,))

            conn.commit()
            conn.close()

            logging.info(
                f"Successful login: "
                f"{username} | role={role}"
            )

            return True, role

        # Failed login

        failed_attempts += 1

        # Lock after 3 failures

        if failed_attempts >= 3:

            cursor.execute("""
                UPDATE users
                SET
                    failed_attempts = 3,
                    is_locked = 1
                WHERE LOWER(username) = LOWER(?)
            """, (username,))

            conn.commit()
            conn.close()

            logging.warning(
                f"Account locked: {username}"
            )

            return False, (
                "Your account has been locked "
                "after 3 failed login attempts."
            )

        # Update failed attempts

        cursor.execute("""
            UPDATE users
            SET failed_attempts = ?
            WHERE LOWER(username) = LOWER(?)
        """, (
            failed_attempts,
            username
        ))

        conn.commit()
        conn.close()

        remaining = (
            3 - failed_attempts
        )

        return False, (
            "Invalid username or password.\n\n"
            f"Attempts remaining: {remaining}"
        )

    # ======================================================
    # GET USER INFO (Task 5 — Profile & Security)
    # ======================================================

    def get_user_info(self, username):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                username,
                email,
                role
            FROM users
            WHERE LOWER(username) = LOWER(?)
        """, (username.strip(),))

        row = cursor.fetchone()

        conn.close()

        if not row:
            return None

        return {
            "username": row[0],
            "email": row[1],
            "role": row[2]
        }

    # ======================================================
    # DIRECT PASSWORD CHANGE (Task 5)
    # ======================================================
    #
    # This is distinct from the Reset / Unlock flow: it is
    # used by an already-authenticated user from
    # My Profile & Security, and requires the user's current
    # password rather than ADMIN approval.
    # ======================================================

    def change_password(
        self,
        username,
        current_password,
        new_password
    ):

        username = username.strip()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT password_hash
            FROM users
            WHERE LOWER(username) = LOWER(?)
        """, (username,))

        row = cursor.fetchone()

        if not row:

            conn.close()

            return False, "Account not found."

        password_hash = row[0]

        try:

            correct = bcrypt.checkpw(
                current_password.encode("utf-8"),
                password_hash.encode("utf-8")
            )

        except ValueError:

            correct = False

        if not correct:

            conn.close()

            return False, "Current password is incorrect."

        valid, message = self.validate_password(
            new_password
        )

        if not valid:

            conn.close()

            return False, message

        new_hash = bcrypt.hashpw(
            new_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute("""
            UPDATE users
            SET password_hash = ?
            WHERE LOWER(username) = LOWER(?)
        """, (
            new_hash,
            username
        ))

        conn.commit()
        conn.close()

        logging.info(
            f"Password changed directly by user: {username}"
        )

        return True, (
            "Password changed successfully.\n"
            "Please log in again with your new password."
        )

    # ======================================================
    # LOGOUT
    # ======================================================

    def logout(self):

        logging.info(
            f"User logged out: "
            f"{self.app.current_username}"
        )

        self.app.current_username = None
        self.app.current_role = None

        self.app.show_auth()


# ==========================================================
# COMPATIBILITY LOGOUT FUNCTION
# ==========================================================
#
# Kept for backward compatibility with any older code that
# imports logout_user() directly. Current views should
# prefer calling auth_controller.logout() (via app), since
# that instance method is what actually has access to the
# Application object it needs.
# ==========================================================

def logout_user():

    global _current_app

    if _current_app is None:

        logging.warning(
            "Logout requested but no application "
            "instance is available."
        )

        return

    logging.info(
        f"User logged out: "
        f"{_current_app.current_username}"
    )

    _current_app.current_username = None
    _current_app.current_role = None

    _current_app.show_auth()