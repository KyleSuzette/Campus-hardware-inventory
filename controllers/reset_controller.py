import bcrypt
import logging

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

        cursor.execute("""
            SELECT username
            FROM users
            WHERE LOWER(email) = LOWER(?)
        """, (email,))

        user = cursor.fetchone()

        if not user:

            conn.close()

            return False, (
                "No account is registered "
                "with this email address."
            )

        username = user[0]

        cursor.execute("""
            SELECT request_id
            FROM password_reset_requests
            WHERE LOWER(email) = LOWER(?)
            AND status = 'PENDING'
        """, (email,))

        if cursor.fetchone():

            conn.close()

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
            VALUES (?, ?, ?, 'PENDING')
        """, (
            username,
            email,
            requested_at
        ))

        conn.commit()
        conn.close()

        logging.info(
            f"Password reset request: {username}"
        )

        return True, (
            "Reset request submitted.\n\n"
            "An ADMIN must approve the request "
            "before the password can be changed."
        )

    # ======================================================
    # CHECK FOR AN APPROVED (NOT YET COMPLETED) REQUEST
    # ======================================================
    #
    # Used by AuthView's Reset / Unlock tab to decide whether
    # the "Submit" button should file a new pending request
    # or actually perform the password reset now that an
    # ADMIN has approved one.
    # ======================================================

    def has_approved_request(self, email):

        email = email.strip()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT request_id
            FROM password_reset_requests
            WHERE LOWER(email) = LOWER(?)
            AND status = 'APPROVED'
            ORDER BY request_id DESC
            LIMIT 1
        """, (email,))

        row = cursor.fetchone()

        conn.close()

        return row is not None

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

        cursor.execute("""
            SELECT username
            FROM users
            WHERE LOWER(email) = LOWER(?)
        """, (email,))

        user = cursor.fetchone()

        if not user:

            conn.close()

            return False, "Account not found."

        username = user[0]

        cursor.execute("""
            SELECT request_id
            FROM password_reset_requests
            WHERE LOWER(email) = LOWER(?)
            AND status = 'APPROVED'
            ORDER BY request_id DESC
            LIMIT 1
        """, (email,))

        approved = cursor.fetchone()

        if not approved:

            conn.close()

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
                password_hash = ?,
                failed_attempts = 0,
                is_locked = 0
            WHERE username = ?
        """, (
            password_hash,
            username
        ))

        cursor.execute("""
            UPDATE password_reset_requests
            SET status = 'COMPLETED'
            WHERE request_id = ?
        """, (approved[0],))

        conn.commit()
        conn.close()

        logging.info(
            f"Password reset completed: {username}"
        )

        return True, (
            "Password reset successful.\n"
            "Your account has been unlocked."
        )

    # ======================================================
    # ADMIN REVIEW
    # ======================================================

    def review_request(
        self,
        request_id,
        action,
        admin_username
    ):

        status = (
            "APPROVED"
            if action == "approve"
            else "REJECTED"
        )

        reviewed_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE password_reset_requests
            SET
                status = ?,
                reviewed_at = ?,
                reviewed_by = ?
            WHERE request_id = ?
            AND status = 'PENDING'
        """, (
            status,
            reviewed_at,
            admin_username,
            request_id
        ))

        conn.commit()
        conn.close()

        logging.info(
            f"ADMIN {admin_username} "
            f"{status} reset request {request_id}"
        )

        return True, (
            f"Request {request_id} "
            f"marked as {status}."
        )

    # ======================================================
    # GET REQUESTS
    # ======================================================

    def get_requests(self):

        conn = get_connection()
        cursor = conn.cursor()

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

        conn.close()

        return rows