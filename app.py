import os
import io
import zipfile
import base64
from flask import Flask, render_template, request, send_file, flash, redirect, url_for

# Import background operations (model loads internally ONE TIME)
from modules.background_ops import (
    remove_background,
    replace_background_color,
    replace_background_image,
    blur_background
)

app = Flask(__name__)
app.secret_key = "super_secret_key"

UPLOAD_DIR = "static/uploads"
OUTPUT_DIR = "static/outputs"
BATCH_DIR = "static/batch_outputs"
SAMPLES_DIR = "static/samples"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BATCH_DIR, exist_ok=True)


# Utility: Load image → base64 for templates
def file_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ----------------------------------------
# INDEX PAGE
# ----------------------------------------
@app.route("/")
def index():
    return render_template("index.html", title="AIvision Extract")


# ----------------------------------------
# BACKGROUND REMOVAL
# ----------------------------------------
@app.route("/background-removal", methods=["GET", "POST"])
def background_removal():
    if request.method == "POST":

        if "image" not in request.files:
            flash("Please upload an image.", "error")
            return redirect(request.url)

        file = request.files["image"]
        if file.filename == "":
            flash("No file selected.", "error")
            return redirect(request.url)

        input_path = os.path.join(UPLOAD_DIR, file.filename)
        file.save(input_path)

        # Process image
        output_bytes = remove_background(input_path)

        output_path = os.path.join(OUTPUT_DIR, "removed.png")
        with open(output_path, "wb") as f:
            f.write(output_bytes)

        return render_template(
            "background_removal.html",
            input_b64=file_to_base64(input_path),
            output_b64=file_to_base64(output_path),
            title="Background Removal"
        )

    return render_template("background_removal.html")


# ----------------------------------------
# BACKGROUND REPLACE
# ----------------------------------------
@app.route("/background-replace", methods=["GET", "POST"])
def background_replace():

    mode = "color"
    selected_color = "#ffffff"

    if request.method == "POST":

        if "image" not in request.files:
            flash("Upload a main image.", "error")
            return redirect(request.url)

        main_file = request.files["image"]
        main_path = os.path.join(UPLOAD_DIR, main_file.filename)
        main_file.save(main_path)

        mode = request.form.get("mode")

        # COLOR REPLACE
        if mode == "color":
            selected_color = request.form.get("color", "#ffffff")

            output_path = os.path.join(OUTPUT_DIR, "replaced.png")
            replace_background_color(main_path, selected_color, save_to=output_path)

            return render_template(
                "background_replace.html",
                input_b64=file_to_base64(main_path),
                output_b64=file_to_base64(output_path),
                mode="color",
                selected_color=selected_color,
            )

        # IMAGE REPLACE
        if mode == "image":

            if "bg_image" not in request.files:
                flash("Upload background image.", "error")
                return redirect(request.url)

            bg_file = request.files["bg_image"]
            bg_path = os.path.join(UPLOAD_DIR, bg_file.filename)
            bg_file.save(bg_path)

            output_path = os.path.join(OUTPUT_DIR, "replaced.png")

            replace_background_image(main_path, bg_path, save_to=output_path)

            return render_template(
                "background_replace.html",
                input_b64=file_to_base64(main_path),
                output_b64=file_to_base64(output_path),
                mode="image"
            )

    return render_template("background_replace.html", mode="color", selected_color="#ffffff")


# ----------------------------------------
# BLUR BACKGROUND
# ----------------------------------------
@app.route("/blur", methods=["GET", "POST"])
def blur_background_page():

    if request.method == "POST":

        if "image" not in request.files:
            flash("Upload an image.", "error")
            return redirect(request.url)

        file = request.files["image"]
        img_path = os.path.join(UPLOAD_DIR, file.filename)
        file.save(img_path)

        blur_value = int(request.form.get("blur", 25))

        output_path = os.path.join(OUTPUT_DIR, "blurred.png")
        blur_background(img_path, blur_value, save_to=output_path)

        return render_template(
            "blur_background.html",
            input_b64=file_to_base64(img_path),
            output_b64=file_to_base64(output_path),
            blur_value=blur_value
        )

    return render_template("blur_background.html")


# ----------------------------------------
# BATCH PROCESSING
# ----------------------------------------
@app.route("/batch-processing", methods=["GET", "POST"])
def batch_processing():

    if request.method == "POST":
        files = request.files.getlist("images")

        # Clean previous outputs
        for f in os.listdir(BATCH_DIR):
            os.remove(os.path.join(BATCH_DIR, f))

        outputs = []

        for f in files:
            save_path = os.path.join(BATCH_DIR, f.filename)
            f.save(save_path)

            out_path = os.path.join(BATCH_DIR, "out_" + f.filename)
            remove_background(save_path, save_to=out_path)

            outputs.append({
                "name": f.filename,
                "b64": file_to_base64(out_path)
            })

        return render_template("batch_processing.html", outputs=outputs)

    return render_template("batch_processing.html")


# ----------------------------------------
# DOWNLOAD ZIP FOR BATCH
# ----------------------------------------
@app.route("/download-zip")
def download_zip():
    zip_path = os.path.join(OUTPUT_DIR, "batch_outputs.zip")

    with zipfile.ZipFile(zip_path, "w") as z:
        for fn in os.listdir(BATCH_DIR):
            z.write(os.path.join(BATCH_DIR, fn), fn)

    return send_file(zip_path, as_attachment=True)


# ----------------------------------------
# SAMPLE GALLERY
# ----------------------------------------
@app.route("/gallery")
def sample_gallery():
    files = os.listdir(SAMPLES_DIR)
    return render_template("sample_gallery.html", files=files)


# ----------------------------------------
# ABOUT PAGE
# ----------------------------------------
@app.route("/about")
def about():
    return render_template("about.html")


# ----------------------------------------
# ENTRY POINT (Render uses Gunicorn so this rarely runs)
# ----------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
