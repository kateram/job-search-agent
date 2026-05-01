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
    Returns the row number written to.
    """
    worksheet = _get_worksheet()

    row = [
        package_data["company_name"],
        package_data["role_title"],
        package_data["fit_score"],
        package_data["cover_letter"],
        "\n".join(package_data["cv_notes"]),
        package_data["company_brief"],
        package_data.get("status", "To Apply"),
        package_data.get("created_at", datetime.now().isoformat()),
    ]

    worksheet.append_row(row)
    return f"Row appended successfully"


async def get_existing_applications(company_name: str) -> list[dict]:
    """
    Check if a company already exists in the tracker.
    Returns matching rows as a list of dicts.
    """
    worksheet = _get_worksheet()
    records = worksheet.get_all_records()

    return [r for r in records if r.get("Company", "").lower() == company_name.lower()]