import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from core.config import settings


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_worksheet():
    """Initialise and return the Google Sheet worksheet."""
    creds = Credentials.from_service_account_file(
        settings.google_credentials_path,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(settings.google_sheet_id)
    return sheet.sheet1


async def write_application(package_data: dict) -> str:
    """
    Append an application package as a new row in Google Sheets.
    Note: gspread is synchronous and blocks the event loop during I/O.
    For a personal single-user tool this is acceptable. In production,
    wrap with asyncio.to_thread() or switch to gspread-asyncio.
    """
    worksheet = _get_worksheet()

    cv_notes = package_data.get("CV Notes", [])
    if isinstance(cv_notes, list):
        cv_notes = "\n".join(cv_notes)

    quality_flags = package_data.get("Quality Flags", [])
    if isinstance(quality_flags, list):
        quality_flags = "\n".join(quality_flags) if quality_flags else ""

    row = [
        package_data["Company"],
        package_data["Role"],
        package_data["Fit Score"],
        package_data.get("Status", "To Apply"),
        package_data.get("Created At", ""),
        cv_notes,
        package_data["Cover Letter"],
        package_data["Company Brief"],
        quality_flags,
    ]

    worksheet.append_row(row)
    return "Row appended successfully"

async def get_existing_applications(company_name: str) -> list[dict]:
    """
    Check if a company already exists in the tracker.
    Returns matching rows as a list of dicts.
    """
    worksheet = _get_worksheet()
    records = worksheet.get_all_records()

    return [r for r in records if r.get("Company", "").lower() == company_name.lower()]