import os
import io
import zipfile
import base64

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    flash,
    redirect,
    url_for,
)

from PIL import Image

from modules.background_ops import (
    remove_background,
    replace_background_color,
    replace_background_image,
    blur_background,
    uniform_resize,
)

app = Flask(__name__)
app.secret_key = "super_secret_key"

# -------------------------------------------------
# STATIC PATHS (ensure folders exist)
# -------------------------------------------------
STATIC_DIR = os.path.join(app.root_path, "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
OUTPUT_DIR = os.path.join(STATIC_DIR, "outputs")
BATCH_DIR = os.path.join(STATIC_DIR, "batch_outputs")
SAMPLES_DIR = os.path.join(STATIC_DIR, "samples")

for d in [UPLOAD_DIR, OUTPUT_DIR, BATCH_DIR]:
    os.makedirs(d, exist_ok=True)


# -------------------------------------------------
# HELPER: file → base64
# -------------------------------------------------
def file_to_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def bytes_to_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


# -------------------------------------------------
# INDEX
# -------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", title="AIvision Extract")


# -------------------------------------------------
# BACKGROUND REMOVAL
# -------------------------------------------------
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

        # Save uploaded image
        input_path = os.path.join(UPLOAD_DIR, file.filename)
        file.save(input_path)

        # Run removal (background_ops handles model internally)
        try:
            output_bytes = remove_background(input_path)
        except Exception as e:
            print("Error in remove_background:", e)
            flash("Failed to process the image. Please try another image.", "error")
            return redirect(request.url)

        # Convert to base64 for inline preview
        input_b64 = file_to_b64(input_path)
        output_b64 = bytes_to_b64(output_bytes)

        return render_template(
            "background_removal.html",
            title="Background Removal · AIvision Extract",
            input_b64=input_b64,
            output_b64=output_b64,
        )

    # GET
    return render_template(
        "background_removal.html",
        title="Background Removal · AIvision Extract",
    )


# -------------------------------------------------
# BACKGROUND REPLACEMENT (COLOR / IMAGE)
# -------------------------------------------------
@app.route("/background-replace", methods=["GET", "POST"])
def background_replace():
    # Default UI state
    mode = "color"
    selected_color = "#00ffff"

    if request.method == "POST":
        mode = request.form.get("mode", "color")

        # Main image
        file = request.files.get("image")
        if file is None or file.filename == "":
            flash("Please upload a main image.", "error")
            return redirect(request.url)

        main_path = os.path.join(UPLOAD_DIR, file.filename)
        file.save(main_path)

        input_b64 = file_to_b64(main_path)

        # COLOR MODE
        if mode == "color":
            selected_color = request.form.get("color", "#00ffff")
            try:
                output_bytes = replace_background_color(main_path, selected_color)
            except Exception as e:
                print("Error in replace_background_color:", e)
                flash("Failed to apply color background.", "error")
                return redirect(request.url)

            output_b64 = bytes_to_b64(output_bytes)

            return render_template(
                "background_replace.html",
                title="Background Replace · AIvision Extract",
                mode="color",
                selected_color=selected_color,
                input_b64=input_b64,
                output_b64=output_b64,
            )

        # IMAGE MODE
        if mode == "image":
            bg_file = request.files.get("bg_image")
            if bg_file is None or bg_file.filename == "":
                flash("Please upload a background image.", "error")
                return redirect(request.url)

            bg_path = os.path.join(UPLOAD_DIR, bg_file.filename)
            bg_file.save(bg_path)

            try:
                output_bytes = replace_background_image(main_path, bg_path)
            except Exception as e:
                print("Error in replace_background_image:", e)
                flash("Failed to apply image background.", "error")
                return redirect(request.url)

            output_b64 = bytes_to_b64(output_bytes)

            return render_template(
                "background_replace.html",
                title="Background Replace · AIvision Extract",
                mode="image",
                selected_color=selected_color,
                input_b64=input_b64,
                output_b64=output_b64,
            )

        # Fallback
        flash("Invalid mode selected.", "error")
        return redirect(request.url)

    # GET
    return render_template(
        "background_replace.html",
        title="Background Replace · AIvision Extract",
        mode=mode,
        selected_color=selected_color,
    )


# -------------------------------------------------
# BLUR BACKGROUND
# -------------------------------------------------
@app.route("/blur", methods=["GET", "POST"])
def blur_background_page():
    blur_value = 25

    if request.method == "POST":
        if "image" not in request.files:
            flash("Upload an image.", "error")
            return redirect(request.url)

        file = request.files["image"]
        if file.filename == "":
            flash("No file selected.", "error")
            return redirect(request.url)

        img_path = os.path.join(UPLOAD_DIR, file.filename)
        file.save(img_path)

        try:
            blur_value = int(request.form.get("blur", 25))
        except ValueError:
            blur_value = 25

        try:
            output_bytes = blur_background(img_path, blur_px=blur_value)
        except Exception as e:
            print("Error in blur_background:", e)
            flash("Failed to blur background.", "error")
            return redirect(request.url)

        input_b64 = file_to_b64(img_path)
        output_b64 = bytes_to_b64(output_bytes)

        return render_template(
            "blur_background.html",
            title="Blur Background · AIvision Extract",
            blur_value=blur_value,
            input_b64=input_b64,
            output_b64=output_b64,
        )

    # GET
    return render_template(
        "blur_background.html",
        title="Blur Background · AIvision Extract",
        blur_value=blur_value,
    )


# -------------------------------------------------
# BATCH PROCESSING
# -------------------------------------------------
@app.route("/batch-processing", methods=["GET", "POST"])
def batch_processing():
    outputs = []

    if request.method == "POST":
        files = request.files.getlist("images")
        if not files or len(files) == 0:
            flash("Please upload one or more images.", "error")
            return redirect(request.url)

        for f in files:
            if f.filename == "":
                continue

            # Save original
            save_path = os.path.join(BATCH_DIR, f.filename)
            f.save(save_path)

            # Remove background → PNG bytes
            try:
                out_bytes = remove_background(save_path)
            except Exception as e:
                print("Error in batch remove_background:", e)
                continue

            # Save processed file for ZIP download
            out_filename = f"out_{f.filename}"
            out_path = os.path.join(BATCH_DIR, out_filename)
            with open(out_path, "wb") as out_f:
                out_f.write(out_bytes)

            # Uniform thumbnail for UI grid
            pil_out = Image.open(io.BytesIO(out_bytes)).convert("RGB")
            thumb = uniform_resize(pil_out, size=450)

            buf = io.BytesIO()
            thumb.save(buf, format="PNG")
            thumb_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            outputs.append({"filename": out_filename, "b64": thumb_b64})

        if not outputs:
            flash("Failed to process images. Please try different images.", "error")
        else:
            flash("Batch processing completed!", "success")

    return render_template(
        "batch_processing.html",
        title="Batch Processing · AIvision Extract",
        outputs=outputs,
    )


# -------------------------------------------------
# DOWNLOAD BATCH ZIP
# -------------------------------------------------
@app.route("/download-zip")
def download_zip():
    if not os.path.exists(BATCH_DIR):
        flash("No batch outputs found.", "error")
        return redirect(url_for("batch_processing"))

    files = [
        f for f in os.listdir(BATCH_DIR)
        if os.path.isfile(os.path.join(BATCH_DIR, f))
    ]

    if not files:
        flash("No batch outputs found.", "error")
        return redirect(url_for("batch_processing"))

    # Create in-memory ZIP
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files:
            path = os.path.join(BATCH_DIR, fname)
            zf.write(path, arcname=fname)
    mem_zip.seek(0)

    return send_file(
        mem_zip,
        mimetype="application/zip",
        as_attachment=True,
        download_name="batch_outputs.zip",
    )


# -------------------------------------------------
# SAMPLE GALLERY
# -------------------------------------------------
@app.route("/gallery")
def sample_gallery():
    files = []
    if os.path.exists(SAMPLES_DIR):
        for f in os.listdir(SAMPLES_DIR):
            path = os.path.join(SAMPLES_DIR, f)
            if os.path.isfile(path):
                files.append(f)

    files.sort()
    return render_template(
        "sample_gallery.html",
        title="Sample Gallery · AIvision Extract",
        files=files,
    )


# -------------------------------------------------
# ABOUT
# -------------------------------------------------
@app.route("/about")
def about():
    return render_template("about.html", title="About · AIvision Extract")


# -------------------------------------------------
# LOCAL ENTRY (for testing) – Render uses Gunicorn
# -------------------------------------------------
if __name__ == "__main__":
    # For local debug only; in Render, Dockerfile uses Gunicorn
    app.run(host="0.0.0.0", port=10000, debug=False)
