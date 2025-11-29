# Invoice Generator - Full Stack Application

A modern invoice and estimate generator with a Python FastAPI backend, Vite React frontend, Supabase database, and authentication.

## Project Structure

```
invoice/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # FastAPI application entry
│   ├── requirements.txt    # Python dependencies
│   ├── .env                # Environment variables
│   ├── models/             # Pydantic models
│   │   └── invoice.py
│   ├── routes/             # API routes
│   │   ├── auth.py         # Authentication endpoints
│   │   └── invoices.py     # Invoice CRUD & PDF
│   └── services/           # Business logic
│       ├── invoice_generator.py  # PDF generation
│       ├── pdf_parser.py         # PDF upload parsing
│       └── supabase_client.py    # Supabase client
├── frontend/               # Vite React TypeScript frontend
│   ├── src/
│   │   ├── api/           # API client
│   │   ├── components/    # React components
│   │   ├── contexts/      # Auth context
│   │   ├── i18n/          # Internationalization
│   │   ├── lib/           # Supabase client
│   │   ├── App.tsx        # Main app component
│   │   └── App.css        # Styles
│   └── package.json
├── supabase/              # Supabase configuration
│   ├── config.toml
│   └── migrations/        # Database migrations
├── gui_invoice_app.py      # Original Tkinter GUI (legacy)
└── invoice_generator.py    # Original generator (legacy)
```

## Features

- 🔐 **Authentication**: User signup/signin with Supabase Auth
- 👤 **User Profiles**: Profile management with company info
- 🌍 **Bilingual Support**: English and French
- 📄 **PDF Generation**: Generate professional invoices and estimates
- 📤 **PDF Upload**: Upload existing invoices to extract data
- 💾 **Database Storage**: Save invoices to Supabase
- 📜 **Invoice History**: View and manage past invoices
- 🎨 **Modern UI**: Clean React-based interface
- 🔒 **Row Level Security**: Each user sees only their invoices

## Setup

### 1. Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run the migration files in order:
   - `supabase/migrations/20251129000001_create_profiles.sql`
   - `supabase/migrations/20251129000002_create_invoices.sql`
3. Copy your project URL and keys from **Settings > API**:
   - Project URL
   - Anon/Public key (for frontend)
   - Service Role key (for backend - optional)

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Edit .env and add your Supabase credentials
# SUPABASE_URL=your_project_url
# SUPABASE_KEY=your_anon_key
# SUPABASE_SERVICE_KEY=your_service_role_key (optional)

# Run the server
python -m uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Edit .env and add your Supabase credentials
# VITE_SUPABASE_URL=your_project_url
# VITE_SUPABASE_ANON_KEY=your_anon_key

# Start development server
npm run dev
```

The frontend will be available at http://localhost:5173

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register new user |
| POST | `/api/auth/signin` | Sign in user |
| POST | `/api/auth/signout` | Sign out user |
| GET | `/api/auth/me` | Get current user info |
| PUT | `/api/auth/profile` | Update user profile |

### Invoices
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/invoices/` | List user's invoices |
| POST | `/api/invoices/` | Create new invoice |
| GET | `/api/invoices/{id}` | Get invoice by ID |
| DELETE | `/api/invoices/{id}` | Delete invoice |
| GET | `/api/invoices/{id}/pdf` | Download invoice PDF |
| POST | `/api/invoices/generate-pdf` | Generate PDF preview |
| POST | `/api/invoices/upload` | Upload PDF to extract data |

## Environment Variables

### Backend (.env)
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
FRONTEND_URL=http://localhost:5173
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000/api
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Database Schema

The app uses two tables with Row Level Security (RLS):

### profiles
- `id` (UUID, references auth.users)
- `email`, `full_name`, `company_name`, `address`, `phone`
- Auto-created on user signup via trigger

### invoices
- `id` (UUID)
- `user_id` (UUID, references auth.users)
- `invoice_number`, `date`, `from_address`, `to_address`
- `items` (JSONB), `mode`, `language`, `total`
- `doc_title`, `created_at`, `updated_at`

## Usage

1. **Sign up** or **Sign in** to your account
2. Select Invoice or Estimate mode
3. Fill in your address and customer address
4. Add items with description, quantity, and price
5. Click "Preview PDF" to download the result
6. Click "Save Invoice" to store it in the database
7. View past invoices in the History tab
8. **Upload PDF**: Import existing invoices to extract data

## Legacy GUI

The original Tkinter GUI is still available:

```bash
python gui_invoice_app.py
```
