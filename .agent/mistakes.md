# Agent Mistakes & Lessons Learned

## Browser Caching Issues (2026-01-23)

### Problem
Users saw different content in Chrome vs Safari. Static version strings like `?v=3.0.5` don't work because:
1. They're static and don't change when files are updated
2. HTML pages with inline CSS/JS get cached by the browser
3. Different browsers have different caching behaviors

### Root Cause
- Used static version strings (`?v=3.0.5`) instead of dynamic cache busting
- HTML pages (dashboard.html, ctv_signup.html, etc.) were being cached by browsers
- Inline CSS in HTML files meant the whole HTML had to be re-fetched

### Solution
1. **For HTML pages** - Add no-cache headers via Flask:
   ```python
   from flask import make_response
   
   @app.route('/')
   def index():
       response = make_response(render_template('page.html'))
       response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
       response.headers['Pragma'] = 'no-cache'
       response.headers['Expires'] = '0'
       return response
   ```

2. **For static files (CSS/JS)** - Use file modification timestamps:
   ```python
   @app.url_defaults
   def hashed_url_for_static_file(endpoint, values):
       if endpoint == 'static':
           filename = values.get('filename')
           if filename:
               file_path = os.path.join(app.static_folder, filename)
               if os.path.isfile(file_path):
                   values['v'] = int(os.stat(file_path).st_mtime)
   ```

### Key Takeaway
**Never use static version strings for cache busting.** Always use:
- **No-cache headers** for HTML pages
- **File modification timestamps** for static assets (CSS, JS, images)
