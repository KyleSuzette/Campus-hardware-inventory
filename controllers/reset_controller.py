import bcrypt
import logging
import psycopg

from datetime import datetime

from models.database import get_connection


class ResetController:

    def __init__(self, app):
        self.app = app

    # ======================================================
    # SUBMIT REQUEST
    # ======================================================

    def submit_request(self, email):

        email = email.strip()

        if not self.app.auth_controller.validate_email(email):
            return False, "Please enter a valid email address."

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT username
                FROM users
                WHERE LOWER(email) = LOWER(%s)
            """, (email,))

            user = cursor.fetchone()

            if not user:

                return False, (
                    "No account is registered "
                    "with this email address."
                )

            username = user[0]

            cursor.execute("""
                SELECT request_id
                FROM password_reset_requests
                WHERE LOWER(email) = LOWER(%s)
                AND status = 'PENDING'
            """, (email,))

            if cursor.fetchone():

                return False, (
                    "A reset request is already pending "
                    "ADMIN approval."
                )

            requested_at = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor.execute("""
                INSERT INTO password_reset_requests
                (
                    username,
                    email,
                    requested_at,
                    status
                )
                VALUES (%s, %s, %s, 'PENDING')
            """, (
                username,
                email,
                requested_at
            ))

            conn.commit()

            logging.info(
                f"Password reset request: {username}"
            )

            return True, (
                "Reset request submitted.\n\n"
                "An ADMIN must approve the request "
                "before the password can be changed."
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Password reset request database error: {e}"
            )

            return False, (
                "Failed to submit reset request "
                "due to a database error."
            )

        finally:

            cursor.close()
            conn.close()

    # ======================================================
    # CHECK FOR AN APPROVED (NOT YET COMPLETED) REQUEST
    # ======================================================

    def has_approved_request(self, email):

        email = email.strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT request_id
                FROM password_reset_requests
                WHERE LOWER(email) = LOWER(%s)
                AND status = 'APPROVED'
                ORDER BY request_id DESC
                LIMIT 1
            """, (email,))

            row = cursor.fetchone()

            return row is not None

        except psycopg.Error as e:

            logging.error(
                f"Approved reset request check error: {e}"
            )

            return False

        finally:

            cursor.close()
            conn.close()

    # ======================================================
    # PERFORM RESET
    # ======================================================

    def perform_reset(
        self,
        email,
        new_password
    ):

        email = email.strip()

        if not self.app.auth_controller.validate_email(email):
            return False, "Invalid email address."

        valid, message = (
            self.app.auth_controller.validate_password(
                new_password
            )
        )

        if not valid:
            return False, message

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT username
                FROM users
                WHERE LOWER(email) = LOWER(%s)
            """, (email,))

            user = cursor.fetchone()

            if not user:

                return False, "Account not found."

            username = user[0]

            cursor.execute("""
                SELECT request_id
                FROM password_reset_requests
                WHERE LOWER(email) = LOWER(%s)
                AND status = 'APPROVED'
                ORDER BY request_id DESC
                LIMIT 1
            """, (email,))

            approved = cursor.fetchone()

            if not approved:

                return False, (
                    "No approved reset request was found."
                )

            password_hash = bcrypt.hashpw(
                new_password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            cursor.execute("""
                UPDATE users
                SET
                    password_hash = %s,
                    failed_attempts = 0,
                    is_locked = 0
                WHERE username = %s
            """, (
                password_hash,
                username
            ))

            cursor.execute("""
                UPDATE password_reset_requests
                SET status = 'COMPLETED'
                WHERE request_id = %s
            """, (approved[0],))

            conn.commit()

            logging.info(
                f"Password reset completed: {username}"
            )

            return True, (
                "Password reset successful.\n"
                "Your account has been unlocked."
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Password reset database error: {e}"
            )

            return False, (
                "Password reset failed due to a database error."
            )

        finally:

            cursor.close()
            conn.close()

    # ======================================================
    # ADMIN REVIEW
    # ======================================================

    def review_request(
        self,
        request_id,
        action,
        admin_username
    ):

        # Convert the action to a consistent format.
        # This prevents "APPROVE" from accidentally
        # being treated as REJECTED.
        action = str(action).strip().upper()

        if action == "APPROVE":
            status = "APPROVED"

        elif action == "REJECT":
            status = "REJECTED"

        else:
            return False, "Invalid reset review action."

        reviewed_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                UPDATE password_reset_requests
                SET
                    status = %s,
                    reviewed_at = %s,
                    reviewed_by = %s
                WHERE request_id = %s
                AND status = 'PENDING'
            """, (
                status,
                reviewed_at,
                admin_username,
                request_id
            ))

            if cursor.rowcount != 1:

                conn.rollback()

                return False, (
                    "Reset request was not found "
                    "or has already been reviewed."
                )

            conn.commit()

            logging.info(
                f"ADMIN {admin_username} "
                f"{status} reset request {request_id}"
            )

            return True, (
                f"Request {request_id} "
                f"marked as {status}."
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Reset request review database error: {e}"
            )

            return False, (
                "Failed to review reset request "
                "due to a database error."
            )

        finally:

            cursor.close()
            conn.close()

    # ======================================================
    # GET REQUESTS
    # ======================================================

    def get_requests(self):

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT
                    request_id,
                    username,
                    email,
                    requested_at,
                    status
                FROM password_reset_requests
                ORDER BY request_id DESC
            """)

            rows = cursor.fetchall()

            return rows

        except psycopg.Error as e:

            logging.error(
                f"Get reset requests database error: {e}"
            )

            return []

        finally:

            cursor.close()
            conn.close()