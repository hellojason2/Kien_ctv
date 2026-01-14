# Signup Terms Management Feature

## Overview

The Signup Terms Management feature allows admins to edit and manage the agreement terms and conditions that appear during CTV signup. Terms are stored in the database and can be updated in real-time without code changes.

## Features

✅ **Multi-language Support**: Separate terms for Vietnamese (vi) and English (en)  
✅ **Version History**: Track all changes with versioning  
✅ **Live Preview**: See how terms will look before saving  
✅ **HTML Editor**: Rich text formatting with toolbar helpers  
✅ **Real-time Updates**: Changes appear immediately on signup page  
✅ **Active/Inactive Versions**: Activate specific versions with one click  
✅ **Audit Trail**: Track who made changes and when  

## Installation

### 1. Run the Migration

```bash
python migrate_signup_terms.py
```

This will:
- Create the `signup_terms` table
- Insert default Vietnamese and English terms
- Set up necessary indexes

### 2. Restart Your Application

```bash
# If using Railway or similar platforms, it will auto-restart
# If running locally:
python backend.py
```

## Usage

### Admin Panel Access

1. Log in to the Admin Panel
2. Navigate to **"Signup Terms"** in the sidebar
3. Select language (Vietnamese or English)
4. Edit the terms content

### Editing Terms

**Title Field**: 
- The main title displayed at the top of the terms modal

**Content Field (HTML)**:
- Use the toolbar buttons to format text
- Write HTML directly for more control
- See live preview on the right

**Toolbar Buttons**:
- **H4**: Insert heading 4 tag
- **P**: Insert paragraph tag
- **B**: Bold text (strong tag)
- **I**: Italic text (em tag)
- **• List**: Convert selected lines to list items

### Saving Changes

Click **"Save Terms"** to:
- Update the current version (if editing existing)
- Create a new version (if needed)
- Automatically activate the new version
- Make changes live immediately

### Version History

Click **"Version History"** to:
- View all past versions
- See who made changes and when
- Load a previous version for editing
- Activate a different version
- Delete old versions (except active ones)

## Database Schema

```sql
CREATE TABLE signup_terms (
    id SERIAL PRIMARY KEY,
    language VARCHAR(5) NOT NULL DEFAULT 'vi',
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(50),
    UNIQUE(language, version)
);
```

## API Endpoints

### Public Endpoints

**GET** `/api/admin/signup-terms/active?language={vi|en}`
- Returns the active terms for the specified language
- Used by the signup page to load terms dynamically
- No authentication required

### Admin-Only Endpoints

**GET** `/api/admin/signup-terms?language={vi|en}`
- Get all versions for a language
- Requires admin authentication

**POST** `/api/admin/signup-terms`
- Create a new version
- Requires: `language`, `title`, `content`
- Returns: new `id` and `version`

**PUT** `/api/admin/signup-terms/{id}`
- Update existing version
- Requires: `title`, `content`

**PUT** `/api/admin/signup-terms/{id}/activate`
- Activate a specific version
- Deactivates all other versions for that language

**DELETE** `/api/admin/signup-terms/{id}`
- Delete a version (only if not active)

## File Structure

```
/Users/thuanle/Documents/Ctv/
├── schema/
│   └── signup_terms.sql                    # Database schema
├── modules/
│   └── admin/
│       ├── terms.py                        # Backend API routes
│       └── __init__.py                     # Updated to import terms
├── templates/
│   └── admin/
│       ├── pages/
│       │   └── signup-terms.html           # Admin page UI
│       ├── base.html                       # Updated to include page
│       └── components/
│           └── sidebar.html                # Updated with menu item
├── static/
│   └── js/
│       ├── admin/
│       │   ├── signup-terms.js             # Admin page logic
│       │   ├── navigation.js               # Updated for routing
│       │   └── translations.js             # Updated with new keys
│       └── ctv/
│           └── signup.js                   # Updated to load terms
└── migrate_signup_terms.py                 # Migration script
```

## Workflow

### How It Works

1. **Admin edits terms** in Admin Panel
2. **Terms are saved** to the `signup_terms` table
3. **Version is activated** (or existing version updated)
4. **Signup page loads terms** via API call
5. **User sees updated terms** when they click "View Terms"

### Language Switching

When a user switches language on the signup page:
1. JavaScript detects language change
2. Automatically fetches terms for new language
3. Updates the terms modal content
4. No page reload required

## Best Practices

### Formatting Tips

✅ Use semantic HTML tags (`<h4>`, `<p>`, `<strong>`)  
✅ Keep paragraphs concise and readable  
✅ Use consistent heading levels  
✅ Test on mobile devices  

❌ Avoid inline styles  
❌ Don't use complex nested structures  
❌ Avoid very long paragraphs  

### Content Guidelines

- **Be clear and concise**: Users should understand quickly
- **Use bullet points**: Break down complex information
- **Highlight important terms**: Use `<strong>` for emphasis
- **Mobile-friendly**: Keep lines short and scannable

### Version Management

- **Create new versions** for major changes
- **Update existing** for minor text fixes
- **Test before activating** to ensure formatting looks good
- **Keep history** for audit purposes

## Troubleshooting

### Terms Not Loading on Signup Page

**Check:**
1. Is the table created? Run migration if not
2. Are there active terms? Check admin panel
3. Any JavaScript errors? Open browser console
4. Is the API endpoint working? Test in browser

### Changes Not Appearing

**Solutions:**
1. Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear browser cache
3. Check if the correct version is active
4. Verify terms were saved successfully

### Formatting Issues

**Tips:**
1. Use the live preview to check formatting
2. Validate your HTML
3. Test with different screen sizes
4. Keep structure simple

## Security

- ✅ Admin authentication required for editing
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS protection (content is sanitized on display)
- ✅ Audit trail (updated_by field tracks changes)

## Future Enhancements

Potential improvements:
- WYSIWYG rich text editor
- Markdown support
- Email notifications on changes
- Terms acceptance tracking per user
- Diff view between versions
- Export/import terms as JSON

## Support

For issues or questions:
1. Check the console for errors
2. Verify database connection
3. Test API endpoints manually
4. Review audit logs

---

**Created**: January 14, 2026  
**Version**: 1.0  
**Status**: Production Ready
