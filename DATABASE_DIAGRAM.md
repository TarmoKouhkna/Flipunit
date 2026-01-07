# Database Diagram Generation Guide

This guide explains how to generate a visual database schema diagram (ERD) for the Flipunit PostgreSQL database.

## Prerequisites

- PostgreSQL database running (port 5432)
- Python virtual environment activated
- Homebrew installed (for graphviz)

## Steps

### 1. Activate Virtual Environment

```bash
cd /Users/tarmokouhkna/Documents/Flipunit
source venv/bin/activate
```

### 2. Install Required Packages

```bash
# Install Python packages
pip install eralchemy graphviz

# Install system dependency (graphviz binary)
brew install graphviz
```

### 3. Generate the Diagram

```bash
eralchemy -i 'postgresql://tarmokouhkna@localhost:5432/flipunit' -o flipunit_erd.png
```

**Note:** Replace `tarmokouhkna` with your PostgreSQL username if different.

### 4. View the Diagram

```bash
# Open the generated diagram
open flipunit_erd.png

# Or locate it in the project directory
ls -lh flipunit_erd.png
```

The diagram will be saved as `flipunit_erd.png` in your project root directory.

## Alternative: Generate DOT Format

If you need to edit or convert the diagram:

```bash
# Generate DOT format
eralchemy -i 'postgresql://tarmokouhkna@localhost:5432/flipunit' -o flipunit_erd.dot

# Convert DOT to PNG (requires graphviz)
dot -Tpng flipunit_erd.dot -o flipunit_erd.png
```

## What the Diagram Shows

- All database tables (Django system tables + custom tables)
- Table columns with data types
- Foreign key relationships
- Many-to-many relationship junction tables
- Primary keys

## Troubleshooting

**If the command fails:**
- Ensure PostgreSQL is running: `lsof -i :5432`
- Check database connection: `psql -d flipunit`
- Verify graphviz is installed: `which dot`
- Try with verbose output: `eralchemy -i 'postgresql://...' -o output.png -v`

**If you get "command not found":**
- Make sure virtual environment is activated (you should see `(venv)` in prompt)
- Verify packages are installed: `pip list | grep eralchemy`

## Alternative Tools

If `eralchemy` doesn't work, consider:
- **dbdiagram.io**: Web-based tool (https://dbdiagram.io)
- **TablePlus**: Built-in diagram view (if available)
- **pgAdmin**: ERD Tool feature

