import bcrypt
import logging
import re
import time
import psycopg

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
                WHERE LOWER(email) = LOWER(%s)
            """, (email,))

            if cursor.fetchone():

                return False, (
                    "This email address is already registered."
                )

            # Check username

            cursor.execute("""
                SELECT id
                FROM users
                WHERE LOWER(username) = LOWER(%s)
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
                VALUES (%s, %s, %s, %s, 0, 0, 0)
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

        except psycopg.IntegrityError:

            conn.rollback()

            return False, (
                "Username or email already exists."
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Registration database error: {e}"
            )

            return False, (
                "Registration failed due to a database error."
            )

        finally:

            cursor.close()
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

        try:

            cursor.execute("""
                SELECT
                    password_hash,
                    failed_attempts,
                    is_locked,
                    locked_until,
                    role
                FROM users
                WHERE LOWER(username) = LOWER(%s)
            """, (username,))

            user = cursor.fetchone()

            if not user:

                return False, (
                    "Invalid username or password."
                )

            (
                password_hash,
                failed_attempts,
                is_locked,
                locked_until,
                role
            ) = user

            # --------------------------------------------------
            # CHECK TEMPORARY ACCOUNT LOCK
            # --------------------------------------------------

            if is_locked:

                current_time = time.time()

                # Account is still within the 30-second lock
                if locked_until and current_time < locked_until:

                    remaining_seconds = max(
                        1,
                        int(locked_until - current_time + 0.999)
                    )

                    return False, (
                        "Your account is temporarily locked.\n\n"
                        f"Try again in {remaining_seconds} seconds."
                    )

                # 30-second lock has expired.
                # Automatically unlock the account.

                cursor.execute("""
                    UPDATE users
                    SET
                        failed_attempts = 0,
                        is_locked = 0,
                        locked_until = 0
                    WHERE LOWER(username) = LOWER(%s)
                """, (username,))

                conn.commit()

                failed_attempts = 0
                is_locked = 0
                locked_until = 0

                logging.info(
                    f"Temporary account lock expired: {username}"
                )

            # --------------------------------------------------
            # CHECK PASSWORD
            # --------------------------------------------------

            try:

                correct = bcrypt.checkpw(
                    password.encode("utf-8"),
                    password_hash.encode("utf-8")
                )

            except ValueError:

                correct = False

            # --------------------------------------------------
            # SUCCESSFUL LOGIN
            # --------------------------------------------------

            if correct:

                cursor.execute("""
                    UPDATE users
                    SET
                        failed_attempts = 0,
                        is_locked = 0,
                        locked_until = 0
                    WHERE LOWER(username) = LOWER(%s)
                """, (username,))

                conn.commit()

                logging.info(
                    f"Successful login: "
                    f"{username} | role={role}"
                )

                return True, role

            # --------------------------------------------------
            # FAILED LOGIN
            # --------------------------------------------------

            failed_attempts += 1

            # --------------------------------------------------
            # LOCK AFTER 3 FAILURES FOR 30 SECONDS
            # --------------------------------------------------

            if failed_attempts >= 3:

                lock_expiration = (
                    time.time() + 30
                )

                cursor.execute("""
                    UPDATE users
                    SET
                        failed_attempts = 3,
                        is_locked = 1,
                        locked_until = %s
                    WHERE LOWER(username) = LOWER(%s)
                """, (
                    lock_expiration,
                    username
                ))

                conn.commit()

                logging.warning(
                    f"Account temporarily locked for "
                    f"30 seconds: {username}"
                )

                return False, (
                    "Your account has been temporarily locked "
                    "for 30 seconds after 3 failed login attempts."
                )

            # --------------------------------------------------
            # UPDATE FAILED ATTEMPTS
            # --------------------------------------------------

            cursor.execute("""
                UPDATE users
                SET failed_attempts = %s
                WHERE LOWER(username) = LOWER(%s)
            """, (
                failed_attempts,
                username
            ))

            conn.commit()

            remaining = (
                3 - failed_attempts
            )

            return False, (
                "Invalid username or password.\n\n"
                f"Attempts remaining: {remaining}"
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Login database error: {e}"
            )

            return False, (
                "Login failed due to a database error."
            )

        finally:

            cursor.close()
            conn.close()

    # ======================================================
    # GET USER INFO (Task 5 — Profile & Security)
    # ======================================================

    def get_user_info(self, username):

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT
                    username,
                    email,
                    role
                FROM users
                WHERE LOWER(username) = LOWER(%s)
            """, (username.strip(),))

            row = cursor.fetchone()

            if not row:
                return None

            return {
                "username": row[0],
                "email": row[1],
                "role": row[2]
            }

        except psycopg.Error as e:

            logging.error(
                f"Get user info database error: {e}"
            )

            return None

        finally:

            cursor.close()
            conn.close()

    # ======================================================
    # DIRECT PASSWORD CHANGE (Task 5)
    # ======================================================
    #
    # This is distinct from the Reset / Unlock flow:
    # it is used by an already-authenticated user from
    # My Profile & Security and requires the user's current
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

        try:

            cursor.execute("""
                SELECT password_hash
                FROM users
                WHERE LOWER(username) = LOWER(%s)
            """, (username,))

            row = cursor.fetchone()

            if not row:

                return False, (
                    "Account not found."
                )

            password_hash = row[0]

            try:

                correct = bcrypt.checkpw(
                    current_password.encode("utf-8"),
                    password_hash.encode("utf-8")
                )

            except ValueError:

                correct = False

            if not correct:

                return False, (
                    "Current password is incorrect."
                )

            valid, message = (
                self.validate_password(
                    new_password
                )
            )

            if not valid:

                return False, message

            new_hash = bcrypt.hashpw(
                new_password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            cursor.execute("""
                UPDATE users
                SET password_hash = %s
                WHERE LOWER(username) = LOWER(%s)
            """, (
                new_hash,
                username
            ))

            conn.commit()

            logging.info(
                f"Password changed directly by user: {username}"
            )

            return True, (
                "Password changed successfully.\n"
                "Please log in again with your new password."
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Password change database error: {e}"
            )

            return False, (
                "Password change failed due to a database error."
            )

        finally:

            cursor.close()
            conn.close()

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