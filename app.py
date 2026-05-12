from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    session,
)
from supabase import create_client, Client
from werkzeug.security import check_password_hash, generate_password_hash

import config

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

supabase: Client = create_client(
    config.SUPABASE_URL,
    config.SUPABASE_KEY,
)


@app.context_processor
def inject_staff_session():
    return {
        "staff_logged_in": bool(session.get("staff_id")),
        "staff_email": session.get("staff_email"),
    }


def staff_required(view_function):
    @wraps(view_function)
    def wrapped(*args, **kwargs):
        if not session.get("staff_id"):
            flash("Please sign in as staff to view applications.", "error")
            return redirect(url_for("staff_login", next=request.path))
        return view_function(*args, **kwargs)

    return wrapped


def _safe_redirect_path(next_path):
    if not next_path or not isinstance(next_path, str):
        return url_for("view_applications")
    if next_path.startswith("/") and not next_path.startswith("//"):
        return next_path
    return url_for("view_applications")


@app.route("/")
def index():
    return render_template("landing_page.html")


@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    if session.get("staff_id"):
        return redirect(_safe_redirect_path(request.args.get("next")))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        staff_code = (request.form.get("staff_code") or "").strip()

        if staff_code != config.STAFF_CODE:
            flash("Staff code does not match.", "error")
            return render_template("staff_login.html", email_prefill=email)
        if not email or not password:
            flash("Enter your email and password.", "error")
            return render_template("staff_login.html", email_prefill=email)

        try:
            response = (
                supabase.table("staff_users")
                .select("id, email, password_hash")
                .eq("email", email)
                .limit(1)
                .execute()
            )
            rows = response.data or []
            if not rows:
                flash("Invalid credentials.", "error")
                return render_template("staff_login.html", email_prefill=email)

            row = rows[0]
            if not check_password_hash(row["password_hash"], password):
                flash("Invalid credentials.", "error")
                return render_template("staff_login.html", email_prefill=email)

            session["staff_id"] = row["id"]
            session["staff_email"] = row["email"]
            flash("Signed in. Welcome back.", "success")
            next_path = request.form.get("next") or request.args.get("next")
            return redirect(_safe_redirect_path(next_path))

        except Exception as exc:
            print(f"Staff login error: {exc}")
            flash("Something went wrong. Please try again later.", "error")
            return render_template("staff_login.html", email_prefill=email)

    return render_template("staff_login.html", email_prefill="")


@app.route("/staff/signup", methods=["GET", "POST"])
def staff_signup():
    if session.get("staff_id"):
        return redirect(url_for("view_applications"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        password_confirm = request.form.get("password_confirm") or ""
        staff_code = (request.form.get("staff_code") or "").strip()
        email_input = request.form.get("email") or ""

        if staff_code != config.STAFF_CODE:
            flash("Staff code does not match.", "error")
            return render_template("staff_signup.html", email_prefill=email_input)

        if not email or not password:
            flash("Enter your email and a password.", "error")
            return render_template("staff_signup.html", email_prefill=email_input)

        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template("staff_signup.html", email_prefill=email_input)

        if len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
            return render_template("staff_signup.html", email_prefill=email_input)

        password_hash = generate_password_hash(password)

        try:
            result = (
                supabase.table("staff_users")
                .insert({"email": email, "password_hash": password_hash})
                .execute()
            )
            rows = result.data or []
            if not rows:
                lookup = (
                    supabase.table("staff_users")
                    .select("id, email")
                    .eq("email", email)
                    .limit(1)
                    .execute()
                )
                rows = lookup.data or []
            if not rows:
                flash("Could not create account. Try again.", "error")
                return render_template("staff_signup.html", email_prefill=email_input)

            row = rows[0]
            session["staff_id"] = row["id"]
            session["staff_email"] = row["email"]
            flash("Account created. You're signed in.", "success")
            return redirect(url_for("view_applications"))

        except Exception as exc:
            print(f"Staff signup error: {exc}")
            code = getattr(exc, "code", None)
            err_text = str(exc)
            duplicate = (
                code in ("23505", 23505)
                or "23505" in err_text
                or "duplicate key" in err_text.lower()
                or "unique constraint" in err_text.lower()
            )
            if duplicate:
                flash("That email is already registered. Sign in instead.", "error")
            else:
                flash("Something went wrong. Please try again later.", "error")
            return render_template("staff_signup.html", email_prefill=email_input)

    return render_template("staff_signup.html", email_prefill="")


@app.route("/staff/logout", methods=["POST"])
def staff_logout():
    session.pop("staff_id", None)
    session.pop("staff_email", None)
    flash("You have signed out.", "success")
    return redirect(url_for("index"))


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
@staff_required
def view_applications():
    try:
        response = (
            supabase.table("applications")
            .select("*")
            .order("submitted_at", desc=True)
            .execute()
        )
        applications = response.data
        return render_template("applications.html", applications=applications)
    except Exception as e:
        print(f"Error fetching applications: {e}")
        flash("Could not load applications.", "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
