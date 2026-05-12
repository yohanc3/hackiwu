from flask import Flask, render_template, request, flash, redirect, url_for
from supabase import create_client, Client 
import config

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

supabase: Client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_KEY
)

@app.route("/")
def index():
    return render_template("landing_page.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form_data = {}
    if request.method == "POST":
        try:
            # Process form data
            for key in request.form.keys():
                if key == "dietary":
                    form_data[key] = request.form.getlist(key)
                else:
                    form_data[key] = request.form.get(key)

            # Map form data to database schema
            application = {
                "first_name": form_data.get("first_name"),
                "last_name": form_data.get("last_name"),
                "email": form_data.get("email"),
                "phone": form_data.get("phone"),
                "age_confirm": form_data.get("age_confirm") == "on",
                "accuracy_confirm": form_data.get("accuracy_confirm") == "on",
                "media_release": form_data.get("media_release") == "on",
                "school": form_data.get("school"),
                "school_other": form_data.get("school_other"),
                "year": form_data.get("year"),
                "major": form_data.get("major"),
                "grad_year": form_data.get("grad_year"),
                "experience": form_data.get("experience"),
                "team_status": form_data.get("team_status"),
                "track_preference": form_data.get("track_preference"),
                "dietary": form_data.get("dietary", []),
                "dietary_other": form_data.get("dietary_other"),
                "linkedin": form_data.get("linkedin"),
                "referral": form_data.get("referral"),
            }

            # Insert into Supabase
            supabase.table("applications").insert(application).execute()
            
            flash("Application submitted successfully! We'll be in touch.", "success")
            return redirect(url_for("index"))

        except Exception as e:
            print(f"Error submitting application: {e}")
            
            # Check for unique constraint violation (email already exists)
            if hasattr(e, 'code') and e.code == '23505':
                flash("That email has already been used for an application.", "error")
            else:
                flash("Something went wrong. Please try again later.", "error")
            
            # Return to register page with existing form data
            return render_template("register.html", form_data=form_data)
        
    return render_template("register.html", form_data=form_data)

@app.route("/applications")
def view_applications():
    try:
        response = supabase.table("applications").select("*").order("submitted_at", desc=True).execute()
        applications = response.data
        return render_template("applications.html", applications=applications)
    except Exception as e:
        print(f"Error fetching applications: {e}")
        flash("Could not load applications.", "error")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
