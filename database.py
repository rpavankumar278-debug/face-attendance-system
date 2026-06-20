from flask import session, flash
import bcrypt


import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='faceatt'
    )


def check_admin_login(email, password_input):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tbladminlogin WHERE userID = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        stored_hash = user['password'].encode('utf-8')
        if bcrypt.checkpw(password_input.encode('utf-8'), stored_hash):
            # Login successful - set session
            session['user_id'] = user['id']
            session['email'] = user['userid']
            return True
        else:
            flash("Invalid password", "danger")
    else:
        flash("User not found", "danger")
    return False



def execute_insert(query, params):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(query, params)

        conn.commit()
        cursor.close()
        conn.close()
        return "Saved successfully."
    except Exception as e:
        return f"Insert/Update error: {str(e)}"

        

def execute_delete(query, params):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(query, params)
        if cursor.rowcount == 0:
            message = "No record found to delete."
        else:
            message = "Record deleted successfully."

        conn.commit()
        cursor.close()
        conn.close()
        return message
    except Exception as e:
        return f"Delete error: {str(e)}"


def execute_select(query, params=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        result = cursor.fetchall()

        cursor.close()
        conn.close()
        return result
    except Exception as e:
        return f"Select error: {str(e)}"


def execute_insert_return_id(query, params):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
      
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                connection.commit()
                return cursor.lastrowid  # returns the auto-incremented id
            
    except Exception as e:
        print("Error during insert:", str(e))
        return None
    finally:
        if connection:
            connection.close()


def execute_update(query, params):
    connection = None
    try:
        connection = get_connection()

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                connection.commit()
                return True  # success
    except Exception as e:
        print("Error during update:", str(e))
        return False
    finally:
        if connection:
            connection.close()



def check_login(query, email, password_input):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (email,))
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    if users:
        # Try finding a match manually
        for user in users:
            if password_input == user['password']:
                session['fid'] = user['fid']
                session['name'] = user['name']
                return True
        flash("Invalid password", "danger")
        return False
    else:
        flash("User not found", "danger")
        return False




def check_student_login(query, email, password_input):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (email,))
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    if not users:
        return "not_found"

    for user in users:
        if password_input == user['password']:
            session['sid'] = user['sid']
            session['name'] = user['name']
            return "success"

    return "invalid_password"
