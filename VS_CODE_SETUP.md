# VS Code + Flask Setup Guide 🚀

## The Problem
You're using VS Code Live Server for your frontend, but the contact form needs a Flask backend server. Both need to run together.

## ✅ SOLUTION - Run Both Servers

### Step 1: Start Flask Backend Server
1. **Open Terminal/PowerShell**
2. **Navigate to your project**:
   ```bash
   cd "E:\office work\Web project"
   ```
3. **Start Flask server**:
   ```bash
   python app.py
   ```
4. **You should see**:
   ```
   Database initialized successfully!
   * Running on http://127.0.0.1:8000
   * Running on http://192.168.100.19:8000
   ```
5. **Keep this terminal window open** - Flask server must keep running

### Step 2: Start VS Code Live Server (Frontend)
1. **Open VS Code**
2. **Open your project folder**: `E:\office work\Web project`
3. **Right-click on `index.html`**
4. **Select "Open with Live Server"**
5. **Your website opens in browser** (usually `http://127.0.0.1:5500` or `http://localhost:5500`)

### Step 3: Test Contact Form
1. **Navigate to contact section** on your website
2. **Fill out the form**:
   - Name: Muhammad Ahad
   - Email: ahadarshad2001@gmail.com
   - Subject: Test message
   - Message: This is working or not
3. **Click "پیغام بھیجیں"**
4. **Should work now!** ✅

## 🔧 How It Works

```
VS Code Live Server (Port 5500) ← User sees website
        ↓ (Contact form submission)
Flask Server (Port 8000) ← Handles form data & saves to database
```

- **VS Code Live Server**: Serves your HTML/CSS/JS files
- **Flask Server**: Handles contact form submissions and database operations
- **JavaScript**: Connects the two by sending form data from port 5500 to port 8000

## 🚨 Important Notes

### ✅ DO:
- Keep both servers running at the same time
- Use VS Code Live Server for viewing the website
- Let Flask handle contact form submissions

### ❌ DON'T:
- Close the Flask server terminal
- Try to access the website only through Flask (port 8000) if you want VS Code features
- Worry if they're on different ports - that's normal!

## 🛠 Troubleshooting

### Flask Server Won't Start:
```bash
# Check if port 8000 is busy
netstat -an | findstr ":8000"
# If busy, kill the process or restart computer
```

### Contact Form Still Shows Error:
1. **Check Flask terminal** for error messages
2. **Open browser console** (F12 → Console tab)
3. **Look for network errors or CORS issues**

### VS Code Live Server Issues:
1. **Restart VS Code**
2. **Try different port** (should auto-select available port)
3. **Check if Live Server extension is installed**

## 🎯 Success Indicators

✅ **Flask server running**: Terminal shows "Running on http://127.0.0.1:8000"  
✅ **VS Code Live Server running**: Browser opens with your website  
✅ **Contact form works**: No network errors, success popup appears  
✅ **Data saves**: Messages appear in admin dashboard  

## 📱 Alternative Method

If you prefer to use only Flask (without VS Code Live Server):
1. **Stop VS Code Live Server**
2. **Access website directly**: `http://localhost:8000/`
3. **Everything works the same way**

The advantage of using VS Code Live Server is that it auto-refreshes when you make changes to HTML/CSS/JS files, while Flask is better for backend operations.

Both methods work perfectly! Choose whichever you prefer. 🎉
