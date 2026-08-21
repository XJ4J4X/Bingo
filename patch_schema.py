with open('server.py', 'r') as f:
    content = f.read()

import re

# Insert ALTER TABLE statements in init_db
alter_sqls = """    if 'wins' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN wins INTEGER DEFAULT 0")
    if 'lives_participated' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN lives_participated INTEGER DEFAULT 0")
    if 'boxes_checked' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN boxes_checked INTEGER DEFAULT 0")
    if 'boxes_correct' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN boxes_correct INTEGER DEFAULT 0")
"""

content = content.replace("    if 'color' not in columns:\n        c.execute(\"ALTER TABLE users ADD COLUMN color TEXT\")\n", "    if 'color' not in columns:\n        c.execute(\"ALTER TABLE users ADD COLUMN color TEXT\")\n" + alter_sqls)

# And also add them to the CREATE TABLE statement
content = content.replace("            color TEXT\n        )", "            color TEXT,\n            wins INTEGER DEFAULT 0,\n            lives_participated INTEGER DEFAULT 0,\n            boxes_checked INTEGER DEFAULT 0,\n            boxes_correct INTEGER DEFAULT 0\n        )")

with open('server.py', 'w') as f:
    f.write(content)
print("Schema patch applied.")
