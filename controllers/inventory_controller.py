import psycopg
import csv
import logging

from datetime import datetime

from models.database import get_connection

DB_NAME = "hardware_inventory.db"


class InventoryController:

    def __init__(self, app=None, db_name=DB_NAME):

        self.app = app
        self.db_name = db_name

    # ======================================================
    # DATABASE CONNECTION
    # ======================================================

    def connect(self):

        return get_connection()

    # ======================================================
    # HARDWARE STATUS
    # ======================================================

    def get_status(self, quantity):

        quantity = int(quantity)

        if quantity > 5:
            return "In Stock"

        elif quantity >= 1:
            return "Low Stock"

        else:
            return "Out of Stock"

    # ======================================================
    # GET ALL HARDWARE
    # ======================================================

    def get_all_hardware(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                item_id,
                item_name,
                category,
                quantity,
                COALESCE(
                    available_quantity,
                    quantity
                ),
                unit_price,
                status
            FROM hardware
            ORDER BY item_id
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    # ======================================================
    # GET AVAILABLE HARDWARE
    # ======================================================

    def get_available_hardware(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                item_id,
                item_name,
                category,
                quantity,
                COALESCE(
                    available_quantity,
                    quantity
                ),
                unit_price,
                status
            FROM hardware
            WHERE COALESCE(
                available_quantity,
                quantity
            ) > 0
            ORDER BY item_id
        """)

        rows = cursor.fetchall()

        conn.close()

        return rows

    # ======================================================
    # GET CATEGORIES
    # ======================================================

    def get_categories(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT category
            FROM hardware
            WHERE category IS NOT NULL
            AND category != ''
            ORDER BY category
        """)

        rows = cursor.fetchall()

        conn.close()

        return [
            row[0]
            for row in rows
        ]

    # ======================================================
    # ADD HARDWARE
    # ======================================================

    def add_hardware(
        self,
        name,
        category,
        quantity,
        price
    ):

        name = name.strip()
        category = category.strip()

        if not name or not category:

            return False, (
                "Please fill in all fields."
            )

        try:

            quantity = int(quantity)
            price = float(price)

            if quantity < 0 or price < 0:

                return False, (
                    "Quantity and price cannot be negative."
                )

        except ValueError:

            return False, (
                "Quantity and price must be valid numbers."
            )

        conn = self.connect()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT item_id
                FROM hardware
                WHERE LOWER(item_name) = LOWER(%s)
            """, (name,))

            if cursor.fetchone():

                return False, (
                    "Hardware already exists."
                )

            status = self.get_status(quantity)

            cursor.execute("""
                INSERT INTO hardware
                (
                    item_name,
                    category,
                    quantity,
                    available_quantity,
                    unit_price,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                name,
                category,
                quantity,
                quantity,
                price,
                status
            ))

            conn.commit()

            logging.info(
                f"Hardware added: {name} | "
                f"Category={category} | "
                f"Quantity={quantity} | "
                f"Price={price}"
            )

            return True, (
                "Hardware added successfully."
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Error adding hardware: {e}"
            )

            return False, (
                "Failed to add hardware."
            )

        finally:

            conn.close()

    # ======================================================
    # UPDATE HARDWARE
    # ======================================================

        # ======================================================
    # UPDATE HARDWARE
    # ======================================================

    def update_hardware(
        self,
        item_id,
        name,
        category,
        quantity,
        available_quantity,
        price
    ):

        name = name.strip()
        category = category.strip()

        if not name or not category:

            return False, (
                "Please fill in all fields."
            )

        try:

            item_id = int(item_id)
            quantity = int(quantity)
            available_quantity = int(
                available_quantity
            )
            price = float(price)

            if quantity < 0 or price < 0:

                return False, (
                    "Quantity and price cannot be negative."
                )

            if available_quantity < 0:

                return False, (
                    "Available stock cannot be negative."
                )

            if available_quantity > quantity:

                return False, (
                    "Available stock cannot be greater "
                    "than total quantity."
                )

        except ValueError:

            return False, (
                "Quantity, available stock, and price "
                "must be valid numbers."
            )

        conn = self.connect()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT item_id
                FROM hardware
                WHERE item_id = %s
            """, (item_id,))

            item = cursor.fetchone()

            if not item:

                return False, (
                    "Hardware record not found."
                )

            # ----------------------------------------------
            # DETERMINE NEW STATUS
            # BASED ON AVAILABLE STOCK
            # ----------------------------------------------

            status = self.get_status(
                available_quantity
            )

            # ----------------------------------------------
            # UPDATE HARDWARE
            # ----------------------------------------------

            cursor.execute("""
                UPDATE hardware
                SET
                    item_name = %s,
                    category = %s,
                    quantity = %s,
                    available_quantity = %s,
                    unit_price = %s,
                    status = %s
                WHERE item_id = %s
            """, (
                name,
                category,
                quantity,
                available_quantity,
                price,
                status,
                item_id
            ))

            conn.commit()

            logging.info(
                f"Hardware updated: "
                f"ID={item_id} | "
                f"Name={name} | "
                f"Category={category} | "
                f"Quantity={quantity} | "
                f"Available={available_quantity} | "
                f"Price={price}"
            )

            return True, (
                "Hardware updated successfully."
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Hardware update error: {e}"
            )

            return False, (
                "Failed to update hardware."
            )

        finally:

            conn.close()
    # ======================================================
    # DELETE HARDWARE
    # ======================================================

    def delete_hardware(self, item_id):

        try:

            item_id = int(item_id)

        except ValueError:

            return False, (
                "Invalid hardware ID."
            )

        conn = self.connect()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT item_name
                FROM hardware
                WHERE item_id = %s
            """, (item_id,))

            item = cursor.fetchone()

            if not item:

                return False, (
                    "Hardware record not found."
                )

            cursor.execute("""
                SELECT COUNT(*)
                FROM borrow_request_items bri
                JOIN borrow_requests br
                    ON bri.request_id = br.request_id
                WHERE bri.item_id = %s
                AND br.status IN
                (
                    'PENDING',
                    'APPROVED',
                    'RETURN_REQUESTED'
                )
            """, (item_id,))

            active_requests = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM borrow_requests
                WHERE item_id = %s
                AND status IN
                (
                    'PENDING',
                    'APPROVED',
                    'RETURN_REQUESTED'
                )
            """, (item_id,))

            active_requests += cursor.fetchone()[0]

            if active_requests > 0:

                return False, (
                    "This hardware cannot be deleted "
                    "because it has an active borrowing "
                    "request."
                )

            cursor.execute("""
                DELETE FROM hardware
                WHERE item_id = %s
            """, (item_id,))

            conn.commit()

            return True, (
                "Hardware deleted successfully."
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Hardware deletion error: {e}"
            )

            return False, (
                "Failed to delete hardware."
            )

        finally:

            conn.close()

    # ======================================================
    # SEARCH HARDWARE
    # ======================================================

    def search_hardware(
        self,
        search_text="",
        category="All Categories",
        status="All Statuses"
    ):

        search_text = search_text.strip().lower()

        conn = self.connect()
        cursor = conn.cursor()

        conditions = [
            """(
                LOWER(item_name) LIKE %s
                OR LOWER(category) LIKE %s
                OR LOWER(status) LIKE %s
            )"""
        ]

        params = [
            f"%{search_text}%",
            f"%{search_text}%",
            f"%{search_text}%"
        ]

        if category and category != "All Categories":

            conditions.append(
                "category = %s"
            )

            params.append(category)

        if status and status != "All Statuses":

            conditions.append(
                "status = %s"
            )

            params.append(status)

        where_clause = " AND ".join(conditions)

        cursor.execute(
            f"""
                SELECT
                    item_id,
                    item_name,
                    category,
                    quantity,
                    COALESCE(
                        available_quantity,
                        quantity
                    ),
                    unit_price,
                    status
                FROM hardware
                WHERE {where_clause}
                ORDER BY item_id
            """,
            params
        )

        rows = cursor.fetchall()

        conn.close()

        return rows

    # ======================================================
    # TOTAL ASSET VALUE
    # ======================================================

    def get_total_asset_value(self):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT SUM(
                quantity * unit_price
            )
            FROM hardware
        """)

        total = cursor.fetchone()[0] or 0

        conn.close()

        return total

    # ======================================================
    # CREATE MULTI-COMPONENT BORROW REQUEST
    # ======================================================

    def create_borrow_request(
        self,
        username,
        student_number,
        items,
        purpose,
        course,
        borrow_date,
        expected_return_date
    ):

        username = username.strip()
        student_number = student_number.strip()
        purpose = purpose.strip()
        course = course.strip()
        borrow_date = borrow_date.strip()
        expected_return_date = expected_return_date.strip()

        if not username:

            return False, "Invalid user."

        if not student_number:

            return False, (
                "Please enter the student number."
            )

        if not items:

            return False, (
                "Please add at least one hardware component."
            )

        if not purpose:

            return False, (
                "Please enter the purpose of borrowing."
            )

        if not course:

            return False, (
                "Please enter the course or subject."
            )

        if not borrow_date:

            return False, (
                "Please enter the borrow date."
            )

        if not expected_return_date:

            return False, (
                "Please enter the expected return date."
            )

        try:

            borrow_dt = datetime.strptime(
                borrow_date,
                "%Y-%m-%d"
            )

            return_dt = datetime.strptime(
                expected_return_date,
                "%Y-%m-%d"
            )

        except ValueError:

            return False, (
                "Dates must use the format "
                "YYYY-MM-DD."
            )

        if return_dt < borrow_dt:

            return False, (
                "Expected return date cannot be "
                "earlier than the borrow date."
            )

        conn = self.connect()

        try:

            # psycopg starts a transaction automatically

            cursor = conn.cursor()

            validated_items = []

            for item in items:

                item_id = int(item["item_id"])
                requested_quantity = int(
                    item["quantity"]
                )

                if requested_quantity <= 0:

                    conn.rollback()

                    return False, (
                        "Every component must have "
                        "a quantity of at least 1."
                    )

                cursor.execute("""
                    SELECT
                        item_name,
                        COALESCE(
                            available_quantity,
                            quantity
                        )
                    FROM hardware
                    WHERE item_id = %s
                """, (item_id,))

                hardware = cursor.fetchone()

                if not hardware:

                    conn.rollback()

                    return False, (
                        "One of the selected hardware "
                        "items no longer exists."
                    )

                item_name = hardware[0]
                available = int(hardware[1])

                if requested_quantity > available:

                    conn.rollback()

                    return False, (
                        f"{item_name}: only {available} "
                        f"unit(s) are available."
                    )

                validated_items.append(
                    (
                        item_id,
                        requested_quantity,
                        item_name
                    )
                )

            first_item_id = validated_items[0][0]
            first_quantity = validated_items[0][1]

            requested_at = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor.execute("""
                INSERT INTO borrow_requests
                (
                    username,
                    student_number,
                    item_id,
                    quantity,
                    purpose,
                    course,
                    borrow_date,
                    expected_return_date,
                    notes,
                    status,
                    requested_at
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s, %s, %s, NULL,
                    'PENDING', %s
                )
                RETURNING request_id
            """, (
                username,
                student_number,
                first_item_id,
                first_quantity,
                purpose,
                course,
                borrow_date,
                expected_return_date,
                requested_at
            ))

            request_id = cursor.fetchone()[0]

            for item_id, quantity, item_name in validated_items:

                cursor.execute("""
                    INSERT INTO borrow_request_items
                    (
                        request_id,
                        item_id,
                        quantity
                    )
                    VALUES (%s, %s, %s)
                """, (
                    request_id,
                    item_id,
                    quantity
                ))

            conn.commit()

            logging.info(
                f"Borrow slip created: "
                f"Request={request_id} | "
                f"User={username} | "
                f"Student={student_number} | "
                f"Components={len(validated_items)}"
            )

            return True, (
                f"Borrow request #{request_id} "
                f"submitted successfully.\n\n"
                f"Your request is now waiting for "
                f"ADMIN approval."
            )

        except (psycopg.Error, ValueError) as e:

            conn.rollback()

            logging.error(
                f"Borrow request error: {e}"
            )

            return False, (
                "Failed to submit borrow request."
            )

        finally:

            conn.close()

    # ======================================================
    # GET COMPONENTS OF A BORROW REQUEST
    # ======================================================

    def get_request_items(
        self,
        request_id,
        cursor=None
    ):

        close_connection = False

        if cursor is None:

            conn = self.connect()
            cursor = conn.cursor()
            close_connection = True

        cursor.execute("""
            SELECT
                bri.item_id,
                h.item_name,
                bri.quantity
            FROM borrow_request_items bri
            JOIN hardware h
                ON bri.item_id = h.item_id
            WHERE bri.request_id = %s
            ORDER BY bri.borrow_item_id
        """, (request_id,))

        rows = cursor.fetchall()

        if close_connection:

            conn.close()

        if not rows:

            if close_connection:

                conn = self.connect()
                cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    br.item_id,
                    h.item_name,
                    br.quantity
                FROM borrow_requests br
                JOIN hardware h
                    ON br.item_id = h.item_id
                WHERE br.request_id = %s
            """, (request_id,))

            rows = cursor.fetchall()

            if close_connection:

                conn.close()

        return [
            (
                int(item_id),
                item_name,
                int(quantity)
            )
            for item_id, item_name, quantity in rows
        ]

    # ======================================================
    # FORMAT REQUEST COMPONENTS
    # ======================================================

    def format_request_items(
        self,
        request_id,
        cursor=None
    ):

        rows = self.get_request_items(
            request_id,
            cursor
        )

        return "\n".join(
            f"{name} x{quantity}"
            for _, name, quantity in rows
        )

    # ======================================================
    # GET USER BORROW REQUESTS
    # ======================================================

    def get_user_borrow_requests(
        self,
        username
    ):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                request_id,
                student_number,
                purpose,
                course,
                borrow_date,
                expected_return_date,
                status,
                requested_at,
                return_requested_at,
                returned_at
            FROM borrow_requests
            WHERE LOWER(username) = LOWER(%s)
            ORDER BY request_id DESC
        """, (username.strip(),))

        requests = cursor.fetchall()

        result = []

        for row in requests:

            (
                request_id,
                student_number,
                purpose,
                course,
                borrow_date,
                expected_return_date,
                status,
                requested_at,
                return_requested_at,
                returned_at
            ) = row

            items = self.get_request_items(
                request_id,
                cursor
            )

            result.append({
                "request_id": request_id,
                "student_number": student_number or "",
                "items": items,
                "purpose": purpose,
                "course": course,
                "borrow_date": borrow_date,
                "expected_return_date": expected_return_date,
                "status": status,
                "requested_at": requested_at,
                "return_requested_at":
                    return_requested_at,
                "returned_at": returned_at
            })

        conn.close()

        return result

    # ======================================================
    # GET ALL BORROW REQUESTS
    # ======================================================

    def get_borrow_requests(
        self,
        status=None
    ):

        conn = self.connect()
        cursor = conn.cursor()

        if status:

            cursor.execute("""
                SELECT
                    request_id,
                    username,
                    student_number,
                    purpose,
                    course,
                    borrow_date,
                    expected_return_date,
                    status,
                    requested_at,
                    reviewed_at,
                    reviewed_by,
                    return_requested_at,
                    returned_at,
                    return_confirmed_by
                FROM borrow_requests
                WHERE status = %s
                ORDER BY request_id DESC
            """, (status,))

        else:

            cursor.execute("""
                SELECT
                    request_id,
                    username,
                    student_number,
                    purpose,
                    course,
                    borrow_date,
                    expected_return_date,
                    status,
                    requested_at,
                    reviewed_at,
                    reviewed_by,
                    return_requested_at,
                    returned_at,
                    return_confirmed_by
                FROM borrow_requests
                ORDER BY request_id DESC
            """)

        requests = cursor.fetchall()

        result = []

        for row in requests:

            (
                request_id,
                username,
                student_number,
                purpose,
                course,
                borrow_date,
                expected_return_date,
                status,
                requested_at,
                reviewed_at,
                reviewed_by,
                return_requested_at,
                returned_at,
                return_confirmed_by
            ) = row

            items = self.get_request_items(
                request_id,
                cursor
            )

            result.append({
                "request_id": request_id,
                "username": username,
                "student_number": student_number or "",
                "items": items,
                "purpose": purpose,
                "course": course,
                "borrow_date": borrow_date,
                "expected_return_date":
                    expected_return_date,
                "status": status,
                "requested_at": requested_at,
                "reviewed_at": reviewed_at,
                "reviewed_by": reviewed_by,
                "return_requested_at":
                    return_requested_at,
                "returned_at": returned_at,
                "return_confirmed_by":
                    return_confirmed_by
            })

        conn.close()

        return result

    # ======================================================
    # ADMIN REVIEW BORROW REQUEST
    # ======================================================

    def review_borrow_request(
        self,
        request_id,
        action,
        admin_username
    ):

        try:

            request_id = int(request_id)

        except (ValueError, TypeError):

            return False, (
                "Invalid request ID."
            )

        action = str(action).lower().strip()

        if action not in (
            "approve",
            "reject"
        ):

            return False, (
                "Invalid review action."
            )

        conn = self.connect()

        try:

            # psycopg starts a transaction automatically

            cursor = conn.cursor()

            cursor.execute("""
                SELECT status
                FROM borrow_requests
                WHERE request_id = %s
            """, (request_id,))

            request = cursor.fetchone()

            if not request:

                conn.rollback()

                return False, (
                    "Borrow request not found."
                )

            current_status = request[0]

            if current_status != "PENDING":

                conn.rollback()

                return False, (
                    f"This request has already been "
                    f"{current_status.lower()}."
                )

            request_items = self.get_request_items(
                request_id,
                cursor
            )

            if not request_items:

                conn.rollback()

                return False, (
                    "No hardware components were found "
                    "for this borrowing request."
                )

            reviewed_at = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # ==================================================
            # REJECT
            # ==================================================

            if action == "reject":

                cursor.execute("""
                    UPDATE borrow_requests
                    SET
                        status = 'REJECTED',
                        reviewed_at = %s,
                        reviewed_by = %s
                    WHERE request_id = %s
                    AND status = 'PENDING'
                """, (
                    reviewed_at,
                    admin_username,
                    request_id
                ))

                if cursor.rowcount != 1:

                    conn.rollback()

                    return False, (
                        "The request could not be rejected."
                    )

                conn.commit()

                return True, (
                    f"Borrow request {request_id} "
                    f"has been rejected."
                )

            # ==================================================
            # APPROVE
            # ==================================================

            # Check every component again.
            for item_id, item_name, quantity in request_items:

                quantity = int(quantity)

                cursor.execute("""
                    SELECT
                        COALESCE(
                            available_quantity,
                            quantity
                        )
                    FROM hardware
                    WHERE item_id = %s
                """, (item_id,))

                hardware = cursor.fetchone()

                if not hardware:

                    conn.rollback()

                    return False, (
                        f"{item_name} is no longer "
                        f"available in the inventory."
                    )

                available = int(hardware[0])

                if available < quantity:

                    conn.rollback()

                    return False, (
                        f"Not enough {item_name} "
                        f"is currently available."
                    )

            # --------------------------------------------------
            # Decrease every component
            # --------------------------------------------------

            for item_id, item_name, quantity in request_items:

                quantity = int(quantity)

                cursor.execute("""
                    UPDATE hardware
                    SET
                        available_quantity =
                            available_quantity - %s
                    WHERE item_id = %s
                    AND available_quantity >= %s
                """, (
                    quantity,
                    item_id,
                    quantity
                ))

                if cursor.rowcount != 1:

                    conn.rollback()

                    return False, (
                        f"Unable to update availability "
                        f"for {item_name}."
                    )

                cursor.execute("""
                    SELECT
                        available_quantity
                    FROM hardware
                    WHERE item_id = %s
                """, (item_id,))

                hardware_row = cursor.fetchone()

                if not hardware_row:

                    conn.rollback()

                    return False, (
                        f"Unable to read updated "
                        f"availability for {item_name}."
                    )

                available = int(
                    hardware_row[0]
                )

                status_text = self.get_status(
                    available
                )

                cursor.execute("""
                    UPDATE hardware
                    SET status = %s
                    WHERE item_id = %s
                """, (
                    status_text,
                    item_id
                ))

            # --------------------------------------------------
            # Approve slip
            # --------------------------------------------------

            cursor.execute("""
                UPDATE borrow_requests
                SET
                    status = 'APPROVED',
                    reviewed_at = %s,
                    reviewed_by = %s
                WHERE request_id = %s
                AND status = 'PENDING'
            """, (
                reviewed_at,
                admin_username,
                request_id
            ))

            if cursor.rowcount != 1:

                conn.rollback()

                return False, (
                    "The request could not be approved."
                )

            conn.commit()

            return True, (
                f"Borrow request {request_id} "
                f"approved successfully."
            )

        except (psycopg.Error, ValueError, TypeError) as e:

            conn.rollback()

            logging.error(
                f"Borrow request review error: {e}"
            )

            return False, (
                "Failed to process borrow request."
            )

        finally:

            conn.close()

    # ======================================================
    # USER REQUESTS RETURN
    # ======================================================

    def request_return(
        self,
        request_id,
        username
    ):

        try:

            request_id = int(request_id)

        except (ValueError, TypeError):

            return False, (
                "Invalid request ID."
            )

        conn = self.connect()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                SELECT status
                FROM borrow_requests
                WHERE request_id = %s
                AND LOWER(username) = LOWER(%s)
            """, (
                request_id,
                username.strip()
            ))

            request = cursor.fetchone()

            if not request:

                return False, (
                    "Borrow request not found."
                )

            if request[0] != "APPROVED":

                return False, (
                    "Only approved borrowings can "
                    "be returned."
                )

            return_requested_at = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor.execute("""
                UPDATE borrow_requests
                SET
                    status = 'RETURN_REQUESTED',
                    return_requested_at = %s
                WHERE request_id = %s
                AND LOWER(username) = LOWER(%s)
                AND status = 'APPROVED'
            """, (
                return_requested_at,
                request_id,
                username.strip()
            ))

            conn.commit()

            return True, (
                "Return request submitted.\n\n"
                "Please wait for ADMIN confirmation."
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Return request error: {e}"
            )

            return False, (
                "Failed to submit return request."
            )

        finally:

            conn.close()

    # ======================================================
    # ADMIN CONFIRMS RETURN
    # ======================================================

    def confirm_return(
        self,
        request_id,
        admin_username
    ):

        try:

            request_id = int(request_id)

        except (ValueError, TypeError):

            return False, (
                "Invalid request ID."
            )

        conn = self.connect()

        try:

            # psycopg starts a transaction automatically

            cursor = conn.cursor()

            cursor.execute("""
                SELECT status
                FROM borrow_requests
                WHERE request_id = %s
            """, (request_id,))

            request = cursor.fetchone()

            if not request:

                conn.rollback()

                return False, (
                    "Borrow request not found."
                )

            if request[0] != "RETURN_REQUESTED":

                conn.rollback()

                return False, (
                    "This borrowing is not waiting "
                    "for return confirmation."
                )

            request_items = self.get_request_items(
                request_id,
                cursor
            )

            if not request_items:

                conn.rollback()

                return False, (
                    "No hardware components were found."
                )

            # --------------------------------------------------
            # Return every component
            # --------------------------------------------------

            for item_id, item_name, quantity in request_items:

                quantity = int(quantity)

                cursor.execute("""
                    UPDATE hardware
                    SET
                        available_quantity =
                            CASE
                                WHEN available_quantity + %s
                                     > quantity
                                THEN quantity
                                ELSE available_quantity + %s
                            END
                    WHERE item_id = %s
                """, (
                    quantity,
                    quantity,
                    item_id
                ))

                if cursor.rowcount != 1:

                    conn.rollback()

                    return False, (
                        f"Hardware record for "
                        f"{item_name} was not found."
                    )

                cursor.execute("""
                    SELECT available_quantity
                    FROM hardware
                    WHERE item_id = %s
                """, (item_id,))

                hardware_row = cursor.fetchone()

                if not hardware_row:

                    conn.rollback()

                    return False, (
                        f"Unable to read updated "
                        f"availability for {item_name}."
                    )

                available = int(
                    hardware_row[0]
                )

                status_text = self.get_status(
                    available
                )

                cursor.execute("""
                    UPDATE hardware
                    SET status = %s
                    WHERE item_id = %s
                """, (
                    status_text,
                    item_id
                ))

            returned_at = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor.execute("""
                UPDATE borrow_requests
                SET
                    status = 'RETURNED',
                    returned_at = %s,
                    return_confirmed_by = %s
                WHERE request_id = %s
                AND status = 'RETURN_REQUESTED'
            """, (
                returned_at,
                admin_username,
                request_id
            ))

            if cursor.rowcount != 1:

                conn.rollback()

                return False, (
                    "Return confirmation failed."
                )

            conn.commit()

            return True, (
                f"Return for request {request_id} "
                f"confirmed successfully."
            )

        except (psycopg.Error, ValueError, TypeError) as e:

            conn.rollback()

            logging.error(
                f"Return confirmation error: {e}"
            )

            return False, (
                "Failed to confirm return."
            )

        finally:

            conn.close()

    # ======================================================
    # ADMIN REJECTS RETURN
    # ======================================================

    def reject_return(
        self,
        request_id,
        admin_username
    ):

        try:

            request_id = int(request_id)

        except (ValueError, TypeError):

            return False, (
                "Invalid request ID."
            )

        conn = self.connect()

        try:

            # psycopg starts a transaction automatically

            cursor = conn.cursor()

            cursor.execute("""
                SELECT status
                FROM borrow_requests
                WHERE request_id = %s
            """, (request_id,))

            request = cursor.fetchone()

            if not request:

                conn.rollback()

                return False, (
                    "Borrow request not found."
                )

            if request[0] != "RETURN_REQUESTED":

                conn.rollback()

                return False, (
                    "This borrowing is not waiting "
                    "for return confirmation."
                )

            reviewed_at = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor.execute("""
                UPDATE borrow_requests
                SET
                    status = 'APPROVED',
                    reviewed_at = %s,
                    reviewed_by = %s
                WHERE request_id = %s
                AND status = 'RETURN_REQUESTED'
            """, (
                reviewed_at,
                admin_username,
                request_id
            ))

            if cursor.rowcount != 1:

                conn.rollback()

                return False, (
                    "Return rejection failed."
                )

            conn.commit()

            return True, (
                f"Return request {request_id} "
                f"has been rejected. "
                f"The hardware remains borrowed."
            )

        except psycopg.Error as e:

            conn.rollback()

            logging.error(
                f"Return rejection error: {e}"
            )

            return False, (
                "Failed to reject return request."
            )

        finally:

            conn.close()

    # ======================================================
    # EXPORT CSV
    # ======================================================

    def export_csv(
        self,
        filename="inventory_report.csv"
    ):

        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                item_id,
                item_name,
                category,
                quantity,
                COALESCE(
                    available_quantity,
                    quantity
                ),
                unit_price,
                status
            FROM hardware
            ORDER BY item_id
        """)

        rows = cursor.fetchall()

        conn.close()

        try:

            with open(
                filename,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "ID",
                    "Name",
                    "Category",
                    "Total Qty",
                    "Available Qty",
                    "Price",
                    "Status"
                ])

                writer.writerows(rows)

            return True, (
                "Inventory report exported successfully."
            )

        except Exception as e:

            logging.error(
                f"CSV export error: {e}"
            )

            return False, (
                "Failed to export inventory report."
            )