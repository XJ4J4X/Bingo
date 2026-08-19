def add_cache_buster(filename, version):
    with open(filename, 'r') as f:
        content = f.read()
    
    # Replace old cache busters or add new ones
    import re
    content = re.sub(r'href="style\.css(\?v=\d+)?"', f'href="style.css?v={version}"', content)
    content = re.sub(r'src="app\.js(\?v=\d+)?"', f'src="app.js?v={version}"', content)
    content = re.sub(r'src="admin\.js(\?v=\d+)?"', f'src="admin.js?v={version}"', content)
    
    # Update version in footer
    content = re.sub(r'v1\.0\.0\.\d+', f'v1.0.0.{version}', content)

    with open(filename, 'w') as f:
        f.write(content)

add_cache_buster('public/index.html', 25)
add_cache_buster('public/admin.html', 25)
