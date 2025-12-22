import os
import re

def fix_po_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if line.startswith('msgid "') or line.startswith('msgstr "'):
            # Extract the prefix and the quoted content
            if line.startswith('msgid "'):
                prefix = 'msgid "'
            else:
                prefix = 'msgstr "'
            
            # Get content after prefix
            rest = line[len(prefix):]
            
            # Check if line ends with a quote
            if rest.endswith('"'):
                # Extract the content between quotes
                content_part = rest[:-1]
                
                # Escape unescaped quotes
                # Replace " with \" but don't double-escape already escaped quotes
                content_part = content_part.replace('\\', '\\\\temp\\\\')  # Protect existing backslashes
                content_part = content_part.replace('"', '\\"')  # Escape quotes
                content_part = content_part.replace('\\\\temp\\\\', '\\')  # Restore backslashes
                
                # Reconstruct the line
                line = prefix + content_part + '"'
        
        fixed_lines.append(line)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"Fixed: {filepath}")

# Fix all ar_001.po files in scale_addons
scale_addons_path = r'c:\Users\ODOO\Documents\ODOO 19\odoo\scale_addons'

for root, dirs, files in os.walk(scale_addons_path):
    for file in files:
        if file == 'ar_001.po':
            filepath = os.path.join(root, file)
            try:
                fix_po_file(filepath)
            except Exception as e:
                print(f"Error fixing {filepath}: {e}")

print("\nAll PO files have been fixed!")
