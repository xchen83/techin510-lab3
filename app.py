import sqlite3
import os
from datetime import datetime
from enum import Enum

import streamlit as st
from pydantic import BaseModel
import streamlit_pydantic as sp

# Connect to our database
con = sqlite3.connect("groceryshoppingapp.sqlite", isolation_level=None)
cur = con.cursor()

# Create the table with 'status'
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        item TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL,
        created_at DATETIME NOT NULL,
        created_by TEXT,
        category TEXT
    )
    """
)

# Define our Enums and Task Model with 'status'
class TaskStatus(str, Enum):
    planned = "planned"
    purchased = "purchased"

class Task(BaseModel):
    item: str
    description: str
    status: TaskStatus = TaskStatus.planned
    created_at: datetime = datetime.now()
    created_by: str
    category: str

# Function to toggle task status
def toggle_status(task_id, new_status):
    cur.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))

# Function to delete a task
def delete_task(task_id):
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

def main():
    st.title("Grocery Shopping App")

    # Search bar
    search_query = st.text_input("Search tasks")

    # Filter dropdown
    categories = cur.execute("SELECT DISTINCT category FROM tasks").fetchall()
    categories = [c[0] for c in categories if c[0] is not None]  # Extract category items and remove None values
    categories.insert(0, "All")  # Add "All" option to categories
    selected_category = st.selectbox("Filter by category", categories)

    # Create a Form using the streamlit-pydantic package with 'status'
    data = sp.pydantic_form(key="task_form", model=Task)
    if data:
        cur.execute(
            """
            INSERT INTO tasks (item, description, status, created_at, created_by, category) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (data.item, data.description, data.status.value, data.created_at, data.created_by, data.category),
        )
        st.success("Task added successfully!")

    # Display tasks based on search and filter
    query = "SELECT * FROM tasks WHERE item LIKE ?"
    parameters = [f"%{search_query}%"]

    if selected_category != "All":
        query += " AND category = ?"
        parameters.append(selected_category)

    tasks = cur.execute(query, parameters).fetchall()

    # Create a header row
    header_cols = st.columns([1, 3, 3, 2])  # Adjust the width ratios as needed
    header_cols[0].write("Status")
    header_cols[1].write("Item")
    header_cols[2].write("Description")
    header_cols[3].write("Actions")  # Consolidated actions column

    for task in tasks:
        task_cols = st.columns([1, 3, 3, 2])  # Keep the same ratios as the header for consistency

        # Checkbox to toggle task status
        current_status = task[3]  # Fetch current status
        is_purchased = current_status == 'purchased'
        if task_cols[0].checkbox("", value=is_purchased, key=f"status_{task[0]}"):
            if not is_purchased:  # If the task was not already marked as purchased, update its status to 'purchased'
                toggle_status(task[0], 'purchased')
        elif is_purchased:  # If the checkbox is unchecked and the task was previously marked as purchased, update to 'planned'
            toggle_status(task[0], 'planned')

        # Display task item and description
        task_cols[1].write(task[1])
        task_cols[2].write(task[2])

        # Edit button for each task
        if task_cols[3].button("Delete", key=f"delete_{task[0]}"):
            delete_task(task[0])
            st.experimental_rerun() 

def edit_view(task_id):
    st.write(f"Editing task {task_id}")
    # Fetch task details from the database using task_id

if __name__ == "__main__":
    main()