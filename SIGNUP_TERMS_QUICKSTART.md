# Quick Start Guide - Signup Terms Management

## Setup (First Time Only)

### Step 1: Run Migration
```bash
python migrate_signup_terms.py
```

Expected output:
```
============================================================
Signup Terms Migration
============================================================
📋 Creating signup_terms table...
✅ Migration completed successfully!
   - Created signup_terms table
   - Inserted default Vietnamese terms
   - Inserted default English terms
   - Created indexes
```

### Step 2: Restart Application
Your app will automatically restart on Railway. If running locally, restart the server.

---

## Using the Feature

### Accessing the Editor

1. **Log in** to Admin Panel: `/admin`
2. Click **"Signup Terms"** in the sidebar (document icon)
3. Select language: **Vietnamese** or **English**

### Editing Terms

#### Quick Edit (Minor Changes)
1. Modify text in the content area
2. Click **"Save Terms"** 
3. ✅ Done! Changes are live immediately

#### HTML Formatting
Use the toolbar buttons:
- **H4** - Add section headings
- **P** - Add paragraphs  
- **B** - Make text bold
- **I** - Make text italic
- **• List** - Create bullet points

#### Preview
The right side shows a **Live Preview** - you'll see exactly how it looks to users.

### Managing Versions

#### View History
1. Click **"Version History"**
2. See all past versions with:
   - Version number
   - Date/time of change
   - Who made the change
   - Preview of content

#### Load Previous Version
1. In Version History, find the version you want
2. Click **"Load"**
3. Edit if needed
4. Click **"Save Terms"**

#### Activate Different Version
1. In Version History, find inactive version
2. Click **"Activate"**
3. ✅ That version becomes active immediately

---

## Common Tasks

### Change Welcome Text
```html
<h4>1. GIỚI THIỆU</h4>
<p>Chào mừng bạn đến với chương trình CTV...</p>
```
1. Find the `<h4>1. GIỚI THIỆU</h4>` section
2. Edit the `<p>` text below it
3. Save

### Add New Section
1. Go to where you want to add it
2. Click **H4** button
3. Type section number and title
4. Click **P** button  
5. Type section content
6. Save

### Format Bullet Points
1. Type your points, one per line:
   ```
   Benefit 1
   Benefit 2
   Benefit 3
   ```
2. Select the lines
3. Click **• List** button
4. Each line becomes: `<p>- Benefit 1</p>`

### Make Text Bold
1. Select the text
2. Click **B** button
3. It wraps in `<strong>` tags

---

## Example: Adding a New Benefits Section

**Before:**
```html
<h4>3. QUYỀN VÀ NGHĨA VỤ CỦA CTV</h4>
<p><strong>Quyền lợi:</strong></p>
```

**After:**
```html
<h4>3. QUYỀN VÀ NGHĨA VỤ CỦA CTV</h4>
<p><strong>Quyền lợi:</strong></p>
<p>- Được hưởng hoa hồng hấp dẫn</p>
<p>- Được đào tạo miễn phí</p>
<p>- Được hỗ trợ tài liệu marketing</p>
<p>- Được tham gia các sự kiện đặc biệt</p>
```

**Steps:**
1. Find the section
2. Click at end of `<p><strong>Quyền lợi:</strong></p>`
3. Type each benefit on a new line
4. Select all benefit lines
5. Click **• List** button
6. Preview and Save

---

## Tips & Tricks

### ✅ DO
- Preview changes before saving
- Use simple, clear language
- Test on mobile (terms are viewed on phones)
- Save often
- Keep paragraph lengths reasonable

### ❌ DON'T
- Don't use complex HTML (tables, divs, etc.)
- Don't delete the structure entirely
- Don't forget to test in both languages
- Don't activate untested versions

---

## Testing Your Changes

### Quick Test Flow
1. **Save** your changes in admin panel
2. **Open** `/ctv/signup` in a new tab
3. **Click** "Điều khoản và Điều kiện" link
4. **Verify** your changes appear correctly
5. **Check** on mobile if possible

### Language Test
1. Change language to English (or Vietnamese)
2. Verify terms load in that language
3. Check formatting looks good

---

## Troubleshooting

### "Terms not appearing"
**Solution:** Hard refresh the signup page (Ctrl+Shift+R)

### "Formatting looks broken"
**Solution:** Check your HTML tags are properly closed:
```html
✅ <p>Text here</p>
❌ <p>Text here
```

### "Can't see my changes"
**Solution:** 
1. Check the terms were saved (look for success message)
2. Verify the version is active (green badge in history)
3. Clear browser cache

### "Lost my changes"
**Solution:** Check Version History - all versions are saved!

---

## HTML Quick Reference

```html
<!-- Heading -->
<h4>Section Title</h4>

<!-- Paragraph -->
<p>Regular text paragraph</p>

<!-- Bold -->
<p><strong>Important text</strong></p>

<!-- Italic -->
<p><em>Emphasized text</em></p>

<!-- Bullet Point -->
<p>- List item</p>

<!-- Line Break -->
<p>First line<br>Second line</p>
```

---

## Need Help?

1. Check the **Live Preview** - it shows you exactly what users see
2. Use **Version History** - you can always go back
3. Test on the **actual signup page** - `/ctv/signup`
4. Check browser **console** for errors (F12)

---

**Remember:** Changes are live immediately after saving! Always preview first.

**Pro Tip:** Keep the signup page open in another tab while editing for quick testing.
