from app import app, db
from models import Company, User

# Company data
companies_data = [
    {"name": "PT. IGP Internasional - Sleman", "code": "191"},
    {"name": "PT. Printec Perkasa II", "code": "180"},
    {"name": "PT. IGP Internasional - Klaten", "code": "195"},
    {"name": "PT. IGP Internasional - Tempel", "code": "194"},
    {"name": "Sansico Utama", "code": "491"},
    {"name": "PT. IGP Internasional - Bantul", "code": "199"},
    {"name": "PT. IGP Internasional - Piyungan", "code": "198"},
    {"name": "PT. Printec Perkasa I", "code": "160"},
    {"name": "PT. Grafitecindo Ciptaprima", "code": "170"},
]

# Super admin data
admin_username = "admin"
admin_email = "printecci@gmail.com"
admin_password = "admin123"

def populate_data():
    with app.app_context():
        print("Starting data population...")
        # Populate Companies
        for company_info in companies_data:
            company = Company.query.filter_by(company_code=company_info["code"]).first()
            if not company:
                new_company = Company(name=company_info["name"], company_code=company_info["code"])
                db.session.add(new_company)
                print(f"  Added company: {new_company.name} ({new_company.company_code})")
            else:
                print(f"  Company {company_info['name']} ({company_info['code']}) already exists.")

        # Populate Super Admin User
        admin_user = User.query.filter_by(username=admin_username).first()
        if not admin_user:
            admin_user = User(
                username=admin_username,
                email=admin_email,
                role='super_admin',
                company_id=None  # Super admin is not tied to a specific company initially
            )
            admin_user.set_password(admin_password)  # Hashes the password
            db.session.add(admin_user)
            print(f"  Added super_admin user: {admin_user.username}")
        else:
            print(f"  User {admin_username} already exists.")

        try:
            db.session.commit()
            print("Data committed successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing data: {e}")

if __name__ == '__main__':
    populate_data()
    print("Initial data population script finished.")
