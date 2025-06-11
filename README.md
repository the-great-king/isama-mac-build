# Isama Management System

A PySide6-based shop management system with inventory tracking, sales management, and loan tracking capabilities.

## Features

- **User Authentication** - Secure login using Firebase Authentication
- **Inventory Management**
  - Add/edit products with stock tracking
  - Record stock updates with history
  - Low stock alerts
- **Sales Management**
  - Record cash and loan sales
  - Track items sold and revenue
  - Daily sales summary
- **Loan Management**
  - Track loan sales with buyer information
  - Record loan payments
  - Filter and view loan status
- **Dashboard**
  - Overview of key metrics
  - Daily sales and stock summary
  - Unpaid loans tracking

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Firebase Setup**
   - Create a new Firebase project at [Firebase Console](https://console.firebase.google.com)
   - Enable Firebase Authentication and Realtime Database
   - Download your service account key JSON file
   - Place it at `firebase/khosi-chat-room-firebase-adminsdk-frw9o-76ebdf2f74.json`
   - Create a `.env` file in the root directory with:
     ```
     FIREBASE_DATABASE_URL=your_database_url
     ```

3. **Run the Application**
   ```bash
   python main.py
   ```

## Project Structure

```
isama_management/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables
├── README.md              # This file
├── assets/               # Images and icons
├── firebase/
│   ├── db.py             # Firebase configuration
│   └── khosi-chat-room-firebase-adminsdk-frw9o-76ebdf2f74.json
├── models/
│   ├── user_model.py     # User data structure
│   ├── product_model.py  # Product and stock
│   └── transaction_model.py
├── screens/
│   ├── login.py         # Login window
│   ├── dashboard.py     # Main dashboard
│   ├── inventory.py     # Stock management
│   ├── sales.py        # Sales recording
│   └── loans.py        # Loan management
├── ui/
│   └── login.ui        # Qt Designer UI file
└── utils/
    └── helpers.py      # Utility functions
```

## Security Notes

- Never commit `khosi-chat-room-firebase-adminsdk-frw9o-76ebdf2f74.json` to version control
- Keep your Firebase credentials secure
- Use environment variables for sensitive data

## Development

To modify the UI:
1. Use Qt Designer to edit `.ui` files
2. The application loads UI files dynamically

To add features:
1. Create new model classes in `models/`
2. Add new screens in `screens/`
3. Update Firebase schema as needed

## License

This project is licensed under the MIT License - see the LICENSE file for details. 